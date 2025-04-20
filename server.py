import os
import socket
import threading
import time
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging
import subprocess
import sys
import signal
import platform
from werkzeug.utils import secure_filename

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)  

# 初始化Flask应用
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'nangege-streaming-secret'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 限制上传大小为500MB
socketio = SocketIO(app, cors_allowed_origins="*")

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 全局变量
clients = {}
active_users = set()
broadcasting = False
broadcast_thread = None
broadcast_type = None
video_path = None
frame_buffer = []
max_buffer_size = 100

# UDP服务器配置
UDP_SERVER_PORT = 12345
UDP_CLIENT_PORT = 12346
MAX_PACKET_SIZE = 65507  # UDP最大包大小
SEQ_NUM_BITS = 32
MAX_SEQ_NUM = 2**SEQ_NUM_BITS - 1

# 创建UDP套接字
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind(('0.0.0.0', UDP_SERVER_PORT))

# 获取本机IP地址
def get_local_ip():
    try:
        # 创建一个临时套接字连接到一个公共地址，获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"获取本地IP失败: {e}")
        return "127.0.0.1"

LOCAL_IP = get_local_ip()
logger.info(f"本机IP地址: {LOCAL_IP}")

# 路由设置
@app.route('/')
def index():
    client_ip = request.remote_addr
    logger.info(f"访问IP: {client_ip}")
    
    # 如果是本机IP或127.0.0.1，显示管理员界面
    if client_ip == LOCAL_IP or client_ip == '127.0.0.1':
        return render_template('admin.html')
    else:
        return render_template('client.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/uploads/<path:path>')
def serve_uploads(path):
    return send_from_directory(app.config['UPLOAD_FOLDER'], path)

# 视频相关API
@app.route('/api/upload_video', methods=['POST'])
def upload_video():
    if 'video_file' not in request.files:
        return jsonify({"status": "error", "message": "没有上传文件"})
    
    file = request.files['video_file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "未选择文件"})
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        file.save(file_path)
        return jsonify({"status": "success", "message": "文件上传成功", "path": filename})
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        return jsonify({"status": "error", "message": f"文件上传失败: {str(e)}"})

@app.route('/api/start_broadcast', methods=['POST'])
def start_broadcast():
    global broadcasting, broadcast_thread, broadcast_type, video_path
    
    if broadcasting:
        return jsonify({"status": "error", "message": "已经在直播中"})
    
    data = request.json
    broadcast_type = data.get('type')
    
    if broadcast_type == 'video':
        video_filename = data.get('video_path')
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
        if not os.path.exists(video_path):
            return jsonify({"status": "error", "message": "视频文件不存在"})
    
    broadcasting = True
    broadcast_thread = threading.Thread(target=broadcast_video)
    broadcast_thread.daemon = True
    broadcast_thread.start()
    
    return jsonify({"status": "success", "message": "直播已开始"})

@app.route('/api/stop_broadcast', methods=['POST'])
def stop_broadcast():
    global broadcasting
    
    if not broadcasting:
        return jsonify({"status": "error", "message": "当前没有直播"})
    
    broadcasting = False
    # 等待广播线程结束
    if broadcast_thread and broadcast_thread.is_alive():
        broadcast_thread.join(timeout=2)
    
    return jsonify({"status": "success", "message": "直播已停止"})

@app.route('/api/broadcast_status')
def get_broadcast_status():
    return jsonify({
        "broadcasting": broadcasting,
        "type": broadcast_type if broadcasting else None,
        "video_path": video_path if broadcast_type == 'video' and broadcasting else None
    })

# WebSocket事件处理
@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    client_ip = request.remote_addr
    logger.info(f"客户端连接: {client_id} ({client_ip})")
    
    # 将客户端添加到活跃用户集合
    active_users.add(client_id)
    
    # 广播更新的用户数量
    emit('user_count', {'count': len(active_users)}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    logger.info(f"客户端断开连接: {client_id}")
    
    # 从活跃用户集合中移除客户端
    if client_id in active_users:
        active_users.remove(client_id)
    
    # 广播更新的用户数量
    emit('user_count', {'count': len(active_users)}, broadcast=True)

@socketio.on('chat_message')
def handle_chat_message(data):
    username = data.get('username', '匿名用户')
    message = data.get('message', '')
    client_id = request.sid
    
    logger.info(f"收到聊天消息: {username}: {message}")
    
    # 广播消息给所有客户端
    emit('chat_message', {
        'username': username,
        'message': message,
        'timestamp': time.strftime('%H:%M:%S')
    }, broadcast=True)

@socketio.on('get_stream_url')
def handle_get_stream_url():
    # 如果正在广播，发送视频URL
    if broadcasting:
        if broadcast_type == 'video' and video_path:
            # 提取文件名
            video_filename = os.path.basename(video_path)
            emit('stream_url', {'url': f'/uploads/{video_filename}'})
        else:
            # 屏幕共享模式，可以发送一个特殊标识
            emit('stream_url', {'url': '/api/stream', 'type': 'screen'})
    else:
        emit('stream_url', {'url': None})

# UDP广播相关函数
def broadcast_video():
    global broadcasting
    
    logger.info(f"开始广播，类型: {broadcast_type}")
    
    try:
        if broadcast_type == 'video':
            broadcast_local_video()
        elif broadcast_type == 'screen':
            broadcast_screen()
    except Exception as e:
        logger.error(f"广播过程中发生错误: {e}")
    finally:
        broadcasting = False
        logger.info("广播已停止")

def broadcast_local_video():
    global broadcasting
    
    # 这里使用FFmpeg处理视频
    # 实际实现中，需要使用subprocess调用FFmpeg，将视频转换为适合UDP传输的格式
    # 然后将视频数据分片，通过UDP发送给所有客户端
    
    logger.info(f"开始播放本地视频: {video_path}")
    
    # 模拟视频广播过程
    seq_num = 0
    while broadcasting:
        # 模拟视频帧数据
        frame_data = f"FRAME_{seq_num}".encode()
        
        # 为每个客户端发送数据
        for client_ip in clients:
            try:
                # 构建包含序列号的数据包
                packet = json.dumps({
                    "seq_num": seq_num,
                    "total_packets": 1,
                    "packet_index": 0,
                    "data": frame_data.hex()
                }).encode()
                
                udp_socket.sendto(packet, (client_ip, UDP_CLIENT_PORT))
            except Exception as e:
                logger.error(f"向客户端 {client_ip} 发送数据失败: {e}")
        
        seq_num = (seq_num + 1) % MAX_SEQ_NUM
        time.sleep(0.033)  # 约30fps

def broadcast_screen():
    global broadcasting
    
    # 这里使用FFmpeg捕获屏幕
    # 实际实现中，需要使用subprocess调用FFmpeg，捕获屏幕并转换为适合UDP传输的格式
    # 然后将视频数据分片，通过UDP发送给所有客户端
    
    logger.info("开始屏幕共享")
    
    # 模拟屏幕共享过程
    seq_num = 0
    while broadcasting:
        # 模拟屏幕帧数据
        frame_data = f"SCREEN_{seq_num}".encode()
        
        # 为每个客户端发送数据
        for client_ip in clients:
            try:
                # 构建包含序列号的数据包
                packet = json.dumps({
                    "seq_num": seq_num,
                    "total_packets": 1,
                    "packet_index": 0,
                    "data": frame_data.hex()
                }).encode()
                
                udp_socket.sendto(packet, (client_ip, UDP_CLIENT_PORT))
            except Exception as e:
                logger.error(f"向客户端 {client_ip} 发送数据失败: {e}")
        
        seq_num = (seq_num + 1) % MAX_SEQ_NUM
        time.sleep(0.033)  # 约30fps

# UDP客户端注册处理
def handle_udp_clients():
    global clients
    
    logger.info("启动UDP客户端处理线程")
    
    while True:
        try:
            data, addr = udp_socket.recvfrom(MAX_PACKET_SIZE)
            client_ip = addr[0]
            
            # 解析收到的数据
            try:
                message = json.loads(data.decode())
                message_type = message.get("type")
                
                if message_type == "register":
                    # 客户端注册
                    clients[client_ip] = {
                        "last_seen": time.time(),
                        "ack_received": {}
                    }
                    logger.info(f"UDP客户端注册: {client_ip}")
                    
                    # 发送确认消息
                    response = json.dumps({"type": "register_ack"}).encode()
                    udp_socket.sendto(response, addr)
                    
                elif message_type == "ack":
                    # 处理确认消息
                    if client_ip in clients:
                        seq_num = message.get("seq_num")
                        clients[client_ip]["ack_received"][seq_num] = True
                        clients[client_ip]["last_seen"] = time.time()
            except json.JSONDecodeError:
                logger.error(f"无法解析来自 {client_ip} 的UDP消息")
                
        except Exception as e:
            logger.error(f"处理UDP客户端时发生错误: {e}")

# 清理不活跃的客户端
def cleanup_inactive_clients():
    global clients
    
    while True:
        try:
            current_time = time.time()
            inactive_clients = []
            
            for client_ip, client_data in clients.items():
                if current_time - client_data["last_seen"] > 30:  # 30秒无响应视为不活跃
                    inactive_clients.append(client_ip)
            
            for client_ip in inactive_clients:
                del clients[client_ip]
                logger.info(f"移除不活跃的UDP客户端: {client_ip}")
            
            time.sleep(10)  # 每10秒检查一次
        except Exception as e:
            logger.error(f"清理不活跃客户端时发生错误: {e}")

# 优雅关闭
def signal_handler(sig, frame):
    logger.info("正在关闭服务器...")
    udp_socket.close()
    sys.exit(0)

# 主函数
def main():
    # 创建必要的目录
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    
    # 启动UDP客户端处理线程
    udp_thread = threading.Thread(target=handle_udp_clients)
    udp_thread.daemon = True
    udp_thread.start()
    
    # 启动清理不活跃客户端的线程
    cleanup_thread = threading.Thread(target=cleanup_inactive_clients)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    
    # 启动Flask应用
    host = '0.0.0.0'  # 监听所有网络接口
    port = 5000
    logger.info(f"启动服务器: http://{LOCAL_IP}:{port}")
    socketio.run(app, host=host, port=port, debug=True, use_reloader=False)

if __name__ == "__main__":
    main()