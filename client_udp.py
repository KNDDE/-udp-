import socket
import json
import threading
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UdpClient:
    def __init__(self, server_ip, server_port=12345, client_port=12346):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_port = client_port
        self.socket = None
        self.running = False
        self.receive_thread = None
        self.frame_callback = None
        self.buffer = {}
        self.last_seq_num = -1
        self.max_buffer_size = 100
        
    def start(self):
        """启动UDP客户端"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('0.0.0.0', self.client_port))
            self.running = True
            
            # 向服务器注册
            self.register()
            
            # 启动接收线程
            self.receive_thread = threading.Thread(target=self.receive_data)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            logger.info(f"UDP客户端已启动，监听端口: {self.client_port}")
            return True
        except Exception as e:
            logger.error(f"启动UDP客户端失败: {e}")
            return False
    
    def stop(self):
        """停止UDP客户端"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1)
        logger.info("UDP客户端已停止")
    
    def register(self):
        """向服务器注册客户端"""
        try:
            register_msg = json.dumps({"type": "register"}).encode()
            self.socket.sendto(register_msg, (self.server_ip, self.server_port))
            logger.info(f"已向服务器 {self.server_ip}:{self.server_port} 发送注册请求")
        except Exception as e:
            logger.error(f"注册客户端失败: {e}")
    
    def send_ack(self, seq_num):
        """发送确认消息"""
        try:
            ack_msg = json.dumps({"type": "ack", "seq_num": seq_num}).encode()
            self.socket.sendto(ack_msg, (self.server_ip, self.server_port))
        except Exception as e:
            logger.error(f"发送确认消息失败: {e}")
    
    def set_frame_callback(self, callback):
        """设置帧数据回调函数"""
        self.frame_callback = callback
    
    def receive_data(self):
        """接收数据线程"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(65507)  # UDP最大包大小
                
                try:
                    # 解析数据包
                    packet = json.loads(data.decode())
                    
                    # 处理注册确认
                    if packet.get("type") == "register_ack":
                        logger.info("服务器已确认注册")
                        continue
                    
                    # 处理视频数据包
                    seq_num = packet.get("seq_num")
                    total_packets = packet.get("total_packets")
                    packet_index = packet.get("packet_index")
                    data_hex = packet.get("data")
                    
                    if seq_num is not None and data_hex:
                        # 发送确认消息
                        self.send_ack(seq_num)
                        
                        # 处理数据
                        data_bytes = bytes.fromhex(data_hex)
                        
                        # 如果是单包数据
                        if total_packets == 1:
                            if self.frame_callback:
                                self.frame_callback(data_bytes)
                        else:
                            # 多包数据需要缓存并重组
                            if seq_num not in self.buffer:
                                self.buffer[seq_num] = {}
                            
                            self.buffer[seq_num][packet_index] = data_bytes
                            
                            # 检查是否收到了所有分片
                            if len(self.buffer[seq_num]) == total_packets:
                                # 重组数据
                                full_data = b''
                                for i in range(total_packets):
                                    if i in self.buffer[seq_num]:
                                        full_data += self.buffer[seq_num][i]
                                
                                # 调用回调函数
                                if self.frame_callback:
                                    self.frame_callback(full_data)
                                
                                # 清理缓存
                                del self.buffer[seq_num]
                        
                        # 清理过期的缓存
                        self.clean_buffer()
                
                except json.JSONDecodeError:
                    logger.error("无法解析收到的数据包")
                except Exception as e:
                    logger.error(f"处理数据包时发生错误: {e}")
            
            except Exception as e:
                if self.running:  # 只在非正常关闭时记录错误
                    logger.error(f"接收数据时发生错误: {e}")
    
    def clean_buffer(self):
        """清理过期的缓存"""
        if len(self.buffer) > self.max_buffer_size:
            # 按序列号排序
            seq_nums = sorted(self.buffer.keys())
            # 删除最旧的一半缓存
            for seq_num in seq_nums[:len(seq_nums)//2]:
                del self.buffer[seq_num]

# 使用示例
def handle_frame(frame_data):
    # 这里处理接收到的帧数据
    # 在实际应用中，可能需要解码视频帧并显示
    print(f"收到帧数据: {len(frame_data)} 字节")

def main():
    # 获取服务器IP
    server_ip = input("请输入服务器IP地址: ")
    
    # 创建UDP客户端
    client = UdpClient(server_ip)
    
    # 设置帧数据回调
    client.set_frame_callback(handle_frame)
    
    # 启动客户端
    if client.start():
        try:
            print("UDP客户端已启动，按Ctrl+C停止...")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("正在停止客户端...")
        finally:
            client.stop()

if __name__ == "__main__":
    main()