import cv2
import numpy as np
import time
import threading
import socket
import json
import logging
import os
import base64
from PIL import ImageGrab

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, udp_port=12345, client_port=12346, quality="medium"):
        self.udp_port = udp_port
        self.client_port = client_port
        self.quality = quality
        self.socket = None
        self.clients = {}
        self.running = False
        self.broadcast_thread = None
        self.capture = None
        self.seq_num = 0
        self.max_seq_num = 2**32 - 1
        self.max_packet_size = 65000  # UDP最大包大小减去头部
        
        # 视频质量设置
        self.quality_settings = {
            "high": {"width": 1280, "height": 720, "fps": 30, "jpeg_quality": 80},
            "medium": {"width": 854, "height": 480, "fps": 25, "jpeg_quality": 70},
            "low": {"width": 640, "height": 360, "fps": 20, "jpeg_quality": 60}
        }
    
    def init_socket(self):
        """初始化UDP套接字"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('0.0.0.0', self.udp_port))
            logger.info(f"UDP服务器已启动，监听端口: {self.udp_port}")
            return True
        except Exception as e:
            logger.error(f"初始化UDP套接字失败: {e}")
            return False
    
    def start_broadcast_video(self, video_path):
        """开始广播本地视频"""
        if self.running:
            logger.warning("已经在广播中")
            return False
        
        if not os.path.exists(video_path):
            logger.error(f"视频文件不存在: {video_path}")
            return False
        
        if not self.init_socket():
            return False
        
        self.running = True
        self.broadcast_thread = threading.Thread(target=self._broadcast_video_thread, args=(video_path,))
        self.broadcast_thread.daemon = True
        self.broadcast_thread.start()
        
        logger.info(f"开始广播视频: {video_path}")
        return True
    
    def start_broadcast_screen(self):
        """开始广播屏幕"""
        if self.running:
            logger.warning("已经在广播中")
            return False
        
        if not self.init_socket():
            return False
        
        self.running = True
        self.broadcast_thread = threading.Thread(target=self._broadcast_screen_thread)
        self.broadcast_thread.daemon = True
        self.broadcast_thread.start()
        
        logger.info("开始广播屏幕")
        return True
    
    def stop_broadcast(self):
        """停止广播"""
        self.running = False
        
        if self.capture and isinstance(self.capture, cv2.VideoCapture):
            self.capture.release()
            self.capture = None
        
        if self.socket:
            self.socket.close()
            self.socket = None
        
        if self.broadcast_thread and self.broadcast_thread.is_alive():
            self.broadcast_thread.join(timeout=2)
        
        logger.info("广播已停止")
        return True
    
    def _broadcast_video_thread(self, video_path):
        """广播视频线程"""
        try:
            self.capture = cv2.VideoCapture(video_path)
            if not self.capture.isOpened():
                logger.error(f"无法打开视频文件: {video_path}")
                self.running = False
                return
            
            settings = self.quality_settings[self.quality]
            fps = settings["fps"]
            frame_time = 1.0 / fps
            
            while self.running:
                start_time = time.time()
                
                ret, frame = self.capture.read()
                if not ret:
                    # 视频结束，循环播放
                    self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                
                # 调整帧大小
                frame = cv2.resize(frame, (settings["width"], settings["height"]))
                
                # 编码帧
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, settings["jpeg_quality"]])
                frame_data = buffer.tobytes()
                
                # 发送帧数据
                self._send_frame(frame_data)
                
                # 控制帧率
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_time - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except Exception as e:
            logger.error(f"广播视频时发生错误: {e}")
        finally:
            if self.capture and isinstance(self.capture, cv2.VideoCapture):
                self.capture.release()
                self.capture = None
            self.running = False
    
    def _broadcast_screen_thread(self):
        """广播屏幕线程"""
        try:
            settings = self.quality_settings[self.quality]
            fps = settings["fps"]
            frame_time = 1.0 / fps
            
            while self.running:
                start_time = time.time()
                
                # 捕获屏幕
                screen = np.array(ImageGrab.grab())
                frame = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
                
                # 调整帧大小
                frame = cv2.resize(frame, (settings["width"], settings["height"]))
                
                # 编码帧
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, settings["jpeg_quality"]])
                frame_data = buffer.tobytes()
                
                # 发送帧数据
                self._send_frame(frame_data)
                
                # 控制帧率
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_time - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except Exception as e:
            logger.error(f"广播屏幕时发生错误: {e}")
        finally:
            self.running = False
    
    def _send_frame(self, frame_data):
        """发送帧数据到所有客户端"""
        if not self.clients:
            return
        
        # 检查是否需要分片
        if len(frame_data) <= self.max_packet_size:
            # 单包发送
            packet = json.dumps({
                "seq_num": self.seq_num,
                "total_packets": 1,
                "packet_index": 0,
                "data": base64.b64encode(frame_data).decode('ascii')
            }).encode()
            
            for client_ip in self.clients:
                try:
                    self.socket.sendto(packet, (client_ip, self.client_port))
                except Exception as e:
                    logger.error(f"向客户端 {client_ip} 发送数据失败: {e}")
        else:
            # 分片发送
            chunks = [frame_data[i:i+self.max_packet_size] for i in range(0, len(frame_data), self.max_packet_size)]
            total_packets = len(chunks)
            
            for i, chunk in enumerate(chunks):
                packet = json.dumps({
                    "seq_num": self.seq_num,
                    "total_packets": total_packets,
                    "packet_index": i,
                    "data": base64.b64encode(chunk).decode('ascii')
                }).encode()
                
                for client_ip in self.clients:
                    try:
                        self.socket.sendto(packet, (client_ip, self.client_port))
                    except Exception as e:
                        logger.error(f"向客户端 {client_ip} 发送数据失败: {e}")
        
        # 更新序列号
        self.seq_num = (self.seq_num + 1) % self.max_seq_num
    
    def handle_client_messages(self):
        """处理客户端消息的线程"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(1024)
                client_ip = addr[0]
                
                try:
                    message = json.loads(data.decode())
                    message_type = message.get("type")
                    
                    if message_type == "register":
                        # 客户端注册
                        self.clients[client_ip] = {
                            "last_seen": time.time(),
                            "ack_received": {}
                        }
                        logger.info(f"客户端注册: {client_ip}")
                        
                        # 发送确认消息
                        response = json.dumps({"type": "register_ack"}).encode()
                        self.socket.sendto(response, addr)
                    
                    elif message_type == "ack":
                        # 处理确认消息
                        if client_ip in self.clients:
                            seq_num = message.get("seq_num")
                            self.clients[client_ip]["ack_received"][seq_num] = True
                            self.clients[client_ip]["last_seen"] = time.time()
                
                except json.JSONDecodeError:
                    logger.error(f"无法解析来自 {client_ip} 的消息")
            
            except Exception as e:
                if self.running:  # 只在非正常关闭时记录错误
                    logger.error(f"处理客户端消息时发生错误: {e}")
    
    def start_client_handler(self):
        """启动客户端消息处理线程"""
        client_thread = threading.Thread(target=self.handle_client_messages)
        client_thread.daemon = True
        client_thread.start()
        return client_thread

# 使用示例
def main():
    processor = VideoProcessor()
    
    print("1. 广播本地视频")
    print("2. 广播屏幕")
    choice = input("请选择广播类型: ")
    
    if choice == "1":
        video_path = input("请输入视频文件路径: ")
        processor.start_broadcast_video(video_path)
    elif choice == "2":
        processor.start_broadcast_screen()
    else:
        print("无效的选择")
        return
    
    # 启动客户端消息处理线程
    client_thread = processor.start_client_handler()
    
    try:
        print("广播已开始，按Ctrl+C停止...")
        while processor.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("正在停止广播...")
    finally:
        processor.stop_broadcast()

if __name__ == "__main__":
    main()