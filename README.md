# UDP网络直播聊天室项目教程

## 项目概述

作者：南

这个项目是一个基于UDP协议的局域网内网络直播聊天室系统，支持视频直播、屏幕共享和实时聊天功能。由于时间限制，未能完成整个项目，项目仅用于tcp课程设计。

本人小白一个，欢迎各位大佬指正，谢谢。

### 系统架构

系统分为两个主要部分：

1. **管理员后台**：用于视频直播和系统管理
2. **客户端界面**：用于观看直播和参与聊天

### 技术栈
- 后端语言 ：Python
- Web框架 ：Flask
- 实时通信 ：Flask-SocketIO
- 网络通信 ：原生Socket（UDP协议）
- 音视频处理 ：OpenCV、Pillow（PIL）、Numpy
- 音频处理 ：PyAudio（如需扩展音频）
- 前端 ：HTML、CSS、JavaScript
- 辅助工具 ：FFmpeg（用于音视频格式转换、采集等，主要在部署和扩展时用到）

### 功能特点

- 基于UDP的音视频流传输
- 本地视频文件播放
- 屏幕实时共享
- 实时聊天功能
- 在线用户统计
- 自动区分管理员和普通用户界面

### 功能概述
* **视频直播**
   - 支持本地视频文件播放和屏幕实时共享。
   - 视频数据通过UDP高效推送到所有客户端。
* **实时聊天**
   - 所有用户可通过WebSocket实时交流。
   - 支持在线人数统计。
* **客户端自动注册与管理**
   - 客户端启动后自动向服务器注册，服务器维护活跃客户端列表。
* **数据可靠性机制**
  - 实现了分片、序列号、ACK确认、缓存清理等机制，提升UDP传输的可靠性。
* **界面自适应**
   - 管理员和普通用户界面自动区分，操作简单。
* **易于部署和扩展**
   - 依赖清晰，支持局域网环境下快速部署。
### 主要依赖库及解释
* **Flask**
	
	- 作用 ：轻量级Web框架，用于搭建Web服务器，处理HTTP请求，渲染页面。
	- 用途 ：提供管理员后台和客户端界面，处理文件上传、API请求等。
* **Flask-SocketIO**

  - 作用 ：为Flask提供WebSocket支持，实现实时双向通信。
  - 用途 ：实现聊天室功能、在线人数统计、消息推送等。
* **socket（Python标准库）**

  - 作用 ：实现底层网络通信。
  - 用途 ：通过UDP协议进行音视频数据的高效传输。
* **threading（Python标准库）**

  - 作用 ：多线程支持。
  - 用途 ：实现数据接收、广播、客户端管理等并发任务。
* **OpenCV（opencv-python）**

  - 作用 ：强大的计算机视觉库。
  - 用途 ：读取、处理、编码视频帧，支持视频文件和摄像头。
* **Pillow（PIL）**

  - 作用 ：图像处理库。
  - 用途 ：屏幕捕获（ImageGrab）、图像格式转换等。
* **Numpy**

  - 作用 ：数值计算库。
  - 用途 ：高效处理图像数据（如屏幕捕获转数组）。
* **PyAudio**

  - 作用 ：音频流处理库。
  - 用途 ：如需扩展音频采集和播放。
* **其他**

  - Werkzeug、Jinja2、MarkupSafe、itsdangerous、click ：Flask及其生态依赖。

  - gevent、gevent-websocket ：为SocketIO提供异步支持。

  - python-socketio、python-engineio ：SocketIO协议实现。

### 实现原理
* **UDP音视频传输**
  - 采用UDP协议进行视频数据传输，因UDP延迟低、效率高，适合实时场景。
  - 视频帧通过OpenCV读取并编码为JPEG格式，必要时分片发送。
  - 客户端接收分片后重组，保证视频帧完整性。
  - 通过序列号、ACK机制提升UDP可靠性。
* **屏幕共享**
  - 使用Pillow的ImageGrab捕获屏幕，OpenCV处理和编码，UDP发送。
* **实时聊天**
  - 通过Flask-SocketIO实现WebSocket通信，支持消息实时推送和在线人数统计。
* **管理员与客户端区分**
  - 通过IP判断访问者身份，自动切换后台和前台界面。
* **文件上传与管理**
  - 支持管理员上传本地视频文件，服务器保存并可用于直播。


###  新手友好型解释
这个程序是一个基于UDP协议的网络直播聊天室系统，让我用简单的话来解释它的工作原理和流程。
想象一下，这个系统就像一个小型的直播平台，有一个主播（管理员）和多个观众（客户端）。主播可以播放视频或者分享自己的屏幕，观众们可以观看直播内容并在聊天室里交流。
首先，当你启动server.py时，它会在你的电脑上创建一个服务器，并自动获取你电脑在局域网中的IP地址。
服务器会自动获取本机在局域网中的IP地址，并创建一个UDP套接字监听12345端口，等待客户端连接。
这个服务器有两个主要功能：一个是提供网页界面（通过Flask实现），另一个是处理视频数据传输（通过UDP协议实现）。服务器会自动判断访问者是谁 - 如果是从本机访问，就显示管理员界面；如果是从其他设备访问，就显示普通用户界面。
管理员界面上，你可以上传视频文件或选择分享屏幕。当你点击"开始直播"按钮时，服务器会启动一个新线程来处理视频数据。如果是播放视频，它会读取视频文件；如果是分享屏幕，它会捕获你的屏幕内容
然后，服务器会将视频数据分成小包，通过UDP协议发送给所有连接的客户端。
与此同时，client_udp.py是客户端程序，负责接收服务器发送的视频数据。当你启动客户端时，它会先问你服务器的IP地址，然后创建一个UDP连接并向服务器注册自己。客户端会启动一个专门的线程不断监听服务器发来的数据包。当收到数据包后，客户端会发送确认消息给服务器，然后处理这些数据。如果视频帧太大被分成了多个包，客户端会先把这些包存在缓冲区里，等全部收到后再拼起来显示完整的画面。
video_processor.py是视频处理模块，负责视频的采集、编码和发送。它可以读取本地视频文件或捕获屏幕内容，然后将视频帧调整大小、压缩质量，最后分片发送给客户端。这个模块支持不同的视频质量设置（高、中、低），可以根据网络状况调整。
整个系统还支持实时聊天功能。当用户在聊天框中输入消息并发送时，消息会通过WebSocket发送到服务器，然后服务器会将这条消息广播给所有在线用户，这样大家就能看到彼此的聊天内容了。系统还会显示当前在线人数，当有新用户加入或离开时，这个数字会自动更新。
总的来说，这个程序创建了一个小型的局域网直播系统，让你可以在局域网内与他人分享视频内容并实时交流，就像一个简化版的直播平台。整个过程中，服务器负责管理连接和分发内容，客户端负责接收和显示内容，而视频处理模块则负责处理视频数据，三者协同工作，形成了一个完整的直播聊天系统。

## 01环境准备

### 1.1所需软件

1. Python 3.8+
2. FFmpeg (用于视频处理)
3. 必要的Python库

### 1.2安装步骤

1. **安装Python**
   - 访问 [Python官网](https://www.python.org/downloads/) 下载并安装Python 3.8或更高版本
   - 安装时勾选"Add Python to PATH"选项

2. **安装FFmpeg**
   - Windows用户：
     - 下载FFmpeg: https://ffmpeg.org/download.html
     - 解压到一个目录，如 `C:\ffmpeg`
     - 将 `C:\ffmpeg\bin` 添加到系统环境变量PATH中
   - 验证安装：打开命令提示符，输入 `ffmpeg -version`

3. **安装Python依赖**
   - 在项目目录中打开命令提示符
   - 运行以下命令安装所需依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 02项目结构

```
-udp--master/
│
├── server.py           # 服务器主程序
├── client_udp.py       # UDP客户端
├── video_processor.py  # 视频处理模块
├── requirements.txt    # 项目依赖
├── README.md           # 项目说明
│
├── static/             # 静态资源目录
│   ├── css/            # CSS样式文件
│   ├── js/             # JavaScript文件
│   └── img/            # 图片资源
│
├── templates/          # HTML模板目录
│   ├── admin.html      # 管理员界面
│   └── client.html     # 客户端界面
│
└── uploads/            # 上传的视频文件存储目录
```

## 03核心组件解析

### 3.1UDP通信原理

UDP (用户数据报协议) 是一种无连接的传输层协议，具有以下特点：

1. **无连接**：发送数据前不需要建立连接
2. **不可靠传输**：不保证数据包的到达顺序，也不保证数据包是否到达
3. **低延迟**：相比TCP，UDP具有更低的延迟，更适合实时应用如视频直播
4. **无拥塞控制**：UDP不会因为网络拥塞而降低发送速率

在本项目中，我们通过以下机制增强UDP的可靠性：

1. **序列号机制**：为每个数据包分配唯一序列号，确保接收端能够按顺序重组数据
2. **数据分片与重组**：将大型视频帧分割成小数据包，在接收端重组
3. **确认机制**：接收端发送ACK消息确认成功接收的数据包

这个基于UDP协议的网络直播聊天室系统运作流程非常清晰，下面我将结合代码详细讲解整个系统是如何一步一步运作的。

### 3.2服务器端启动流程

当运行server.py时，系统首先进行初始化：

1. **服务器初始化**：服务器创建一个UDP套接字，并绑定到指定端口（默认12345）上。
```python
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind(('0.0.0.0', UDP_SERVER_PORT))
```

2. **获取本机IP**：服务器通过创建一个临时连接来获取本机在局域网中的IP地址，这个IP地址将用于区分管理员和普通用户。
```python
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"获取本地IP失败: {e}")
        return "127.0.0.1"
```

3. **启动Web服务**：服务器启动Flask应用，提供Web界面，这样用户可以通过浏览器访问系统。

4. **启动客户端处理线程**：服务器启动一个专门的线程来处理UDP客户端的连接和消息。

### 3.3客户端启动流程

当我们运行client_udp.py时，客户端进行如下操作：

1. **获取服务器IP**：首先询问用户输入服务器的IP地址。
```python
server_ip = input("请输入服务器IP地址: ")
```

2. **创建UDP客户端**：创建一个UdpClient对象，并设置好服务器IP和端口。
```python
client = UdpClient(server_ip)
```

3. **设置回调函数**：设置一个回调函数，用于处理接收到的视频帧数据。
```python
client.set_frame_callback(handle_frame)
```

4. **启动客户端**：客户端创建UDP套接字，绑定到本地端口（默认12346），并向服务器发送注册请求。
```python
def start(self):
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
```

5. **启动接收线程**：客户端启动一个专门的线程来不断接收服务器发来的数据。

### 3.3用户界面区分

当用户通过浏览器访问服务器时，系统会根据访问者的IP地址来区分是管理员还是普通用户：

```python
@app.route('/')
def index():
    client_ip = request.remote_addr
    
    # 如果是本机IP或127.0.0.1，显示管理员界面
    if client_ip == LOCAL_IP or client_ip == '127.0.0.1':
        return render_template('admin.html')
    else:
        return render_template('client.html')
```

如果是从服务器本机访问（IP是本机IP或127.0.0.1），就显示管理员界面；如果是从其他设备访问，就显示普通用户界面。

### 3.4管理员直播

1. **选择直播类型**：管理员可以选择上传视频文件或分享屏幕。

2. **开始直播**：当管理员点击"开始直播"按钮时，服务器会启动一个新线程来处理视频数据。
```python
# 定义一个路由，当客户端向 /api/start_broadcast 发送 POST 请求时，会调用下面的函数
@app.route('/api/start_broadcast', methods=['POST'])
def start_broadcast():
    global broadcasting, broadcast_thread, broadcast_type, video_path
    
    if broadcasting:  #检查
        return jsonify({"status": "error", "message": "已经在直播中"})
    
    data = request.json
    # 从获取的数据中提取直播类型
    broadcast_type = data.get('type')
    
     # 如果直播类型是视频直播
    if broadcast_type == 'video':
        video_filename = data.get('video_path')
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
        if not os.path.exists(video_path):
            return jsonify({"status": "error", "message": "视频文件不存在"})
    
    broadcasting = True
    # 创建一个新的线程，线程的目标函数是 broadcast_video
    broadcast_thread = threading.Thread(target=broadcast_video)
    # 将线程设置为守护线程，主线程退出时，守护线程也会随之退出
    broadcast_thread.daemon = True
    broadcast_thread.start()
    
    return jsonify({"status": "success", "message": "直播已开始"})
```

### 3.5视频处理和发送

视频处理模块（video_processor.py）负责处理视频数据：

1. **读取视频或捕获屏幕**：根据直播类型，系统会读取视频文件或捕获屏幕内容。
```python
def _broadcast_video_thread(self, video_path):
    try:
        self.capture = cv2.VideoCapture(video_path)
        if not self.capture.isOpened():
            logger.error(f"无法打开视频文件: {video_path}")
            self.running = False
            return
        # 根据当前选择的视频质量从 quality_settings 字典中获取对应的设置
        settings = self.quality_settings[self.quality]
        # 从设置中提取帧率（Frames Per Second）
        fps = settings["fps"]
        # 计算每一帧的时间间隔（秒）
        frame_time = 1.0 / fps
        
        # 只要 running 标志为 True，就持续循环播放视频
        while self.running:
            start_time = time.time()
            
              # 从视频文件中读取一帧图像，ret 表示是否成功读取到帧，frame 是读取到的帧图像
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
            
            # 调用 _send_frame 方法，将编码后的帧数据发送出去
            self._send_frame(frame_data)
            
            # 控制帧率
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_time - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
```

2. **数据分片和发送**：如果视频帧太大，系统会将其分成多个小包发送。
```python
def _send_frame(self, frame_data):
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
        
        # 遍历所有客户端 IP 地址
        for client_ip in self.clients:
            try:
                # 使用 UDP 套接字将数据包发送到客户端的指定端口
                self.socket.sendto(packet, (client_ip, self.client_port))
            except Exception as e:
                logger.error(f"向客户端 {client_ip} 发送数据失败: {e}")
    else:
        # 分片发送
        # 帧数据长度超过最大数据包大小，需要进行分片发送
        # 将帧数据按最大数据包大小进行切片，得到多个数据块
        chunks = [frame_data[i:i+self.max_packet_size] for i in range(0, len(frame_data), self.max_packet_size)]
        total_packets = len(chunks)
        
        # 遍历每个数据块
        for i, chunk in enumerate(chunks):
            packet = json.dumps({
                # 数据包的序列号，所有分片数据包序列号相同
                "seq_num": self.seq_num,
                # 总的数据包数量
                "total_packets": total_packets,
                # 当前数据包的索引，从 0 开始
                "packet_index": i,
                # 对当前数据块进行 Base64 编码并转换为 ASCII 字符串
                "data": base64.b64encode(chunk).decode('ascii')
            }).encode()
            
            for client_ip in self.clients:
                try:
                    self.socket.sendto(packet, (client_ip, self.client_port))
                except Exception as e:
                    logger.error(f"向客户端 {client_ip} 发送数据失败: {e}")
```

### 3.6客户端接收和处理视频数据

1. **接收数据**：客户端的接收线程不断监听服务器发来的数据包。
```python
def receive_data(self):
    while self.running:
        try:
            data, addr = self.socket.recvfrom(65507)  # UDP最大包大小
            
            try:
                # 解析数据包
                packet = json.loads(data.decode())
```

2. **发送确认**：当收到数据包后，客户端会发送确认消息给服务器。
```python
# 发送确认消息
self.send_ack(seq_num)
```

3. **数据重组**：如果是多包数据，客户端会将这些包存在缓冲区中，等收到所有分片后再重组。
```python
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
```

4. **清理缓存**：客户端会定期清理过期的缓存，防止内存占用过多。
```python
def clean_buffer(self):
    if len(self.buffer) > self.max_buffer_size:
        # 按序列号排序
        seq_nums = sorted(self.buffer.keys())
        # 删除最旧的一半缓存
        for seq_num in seq_nums[:len(seq_nums)//2]:
            del self.buffer[seq_num]
```

### 3.7聊天功能流程

1. **用户连接**：当用户通过浏览器连接到服务器时，会建立WebSocket连接，并被添加到活跃用户集合中。
```python
@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    client_ip = request.remote_addr
    
    # 将客户端添加到活跃用户集合
    active_users.add(client_id)
    
    # 广播更新的用户数量
    emit('user_count', {'count': len(active_users)}, broadcast=True)
```

2. **发送消息**：用户在聊天框中输入消息并发送，消息通过WebSocket发送到服务器。

3. **广播消息**：服务器接收到消息后，会将其广播给所有在线用户。
```python
@socketio.on('chat_message')
def handle_chat_message(data):
    username = data.get('username', '匿名用户')
    message = data.get('message', '')
    
    # 广播消息给所有客户端
    emit('chat_message', {
        'username': username,
        'message': message,
        'timestamp': time.strftime('%H:%M:%S')
    }, broadcast=True)
```

4. **用户断开连接**：当用户关闭浏览器或断开连接时，会从活跃用户集合中移除，并更新在线人数。
```python
@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    
    # 从活跃用户集合中移除客户端
    if client_id in active_users:
        active_users.remove(client_id)
    
    # 广播更新的用户数量
    emit('user_count', {'count': len(active_users)}, broadcast=True)
```

### 3.8客户端注册和管理

1. **客户端注册**：客户端启动后，会向服务器发送注册请求。
```python
def register(self):
    try:
        register_msg = json.dumps({"type": "register"}).encode()
        self.socket.sendto(register_msg, (self.server_ip, self.server_port))
        logger.info(f"已向服务器 {self.server_ip}:{self.server_port} 发送注册请求")
    except Exception as e:
        logger.error(f"注册客户端失败: {e}")
```

2. **服务器处理注册**：服务器接收到注册请求后，会将客户端添加到客户端列表中，并发送确认消息。
```python
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
```

3. **清理不活跃客户端**：服务器会定期检查客户端的活跃状态，移除长时间没有响应的客户端。
```python
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
```

## 04部署步骤

### 4.1 准备环境

1. 确保已安装Python 3.8+和FFmpeg
2. 创建项目目录并下载项目文件

### 4.2 安装依赖

在项目目录中打开命令提示符，运行：

```bash
pip install -r requirements.txt
```

### 4.3 创建必要的目录

确保以下目录存在：
- `static/` - 存放静态资源
- `templates/` - 存放HTML模板
- `uploads/` - 存放上传的视频文件

### 4.4 创建HTML模板

在`templates`目录中创建以下文件：

**admin.html** - 管理员界面，包含视频上传、直播控制和聊天功能
**client.html** - 客户端界面，包含视频播放和聊天功能

### 4.5 启动服务器

在项目目录中运行：

```bash
python server.py
```

服务器将在本地IP的5000端口启动。

### 4.6 访问系统

- 管理员界面：在本机浏览器中访问 `http://localhost:5000`
- 客户端界面：在其他设备浏览器中访问 `http://<服务器IP>:5000`

## 05功能测试

### 5.1 测试视频直播

1. 在管理员界面上传一个视频文件
2. 选择"本地视频"模式并点击"开始直播"
3. 在客户端界面查看是否能正常播放视频

### 5.2 测试屏幕共享

*此功能存在bug没有改正*

1. 在管理员界面选择"屏幕共享"模式并点击"开始直播"
2. 在客户端界面查看是否能看到管理员的屏幕

### 5.3 测试聊天功能

1. 在客户端界面输入用户名和消息
2. 点击发送按钮
3. 检查消息是否显示在所有客户端和管理员界面上

## 06常见问题解答

### 6.1 视频播放卡顿

**可能原因**：

- 网络带宽不足
- 视频质量设置过高
- 客户端设备性能不足

**解决方案**：
- 降低视频质量设置
- 确保局域网带宽充足
- 减小视频分辨率

### 6.2 客户端无法连接服务器

**可能原因**：
- 防火墙阻止UDP通信
- 服务器IP或端口配置错误
- 网络连接问题

**解决方案**：
- 检查防火墙设置，允许UDP端口12345和12346
- 确认服务器IP地址正确
- 检查网络连接

### 6.3视频无法上传

**可能原因**：
- 视频文件过大
- 上传目录权限问题
- 服务器磁盘空间不足

**解决方案**：
- 检查`MAX_CONTENT_LENGTH`设置
- 确保上传目录有写入权限
- 清理磁盘空间

## 07进阶优化

### 7.1 视频编码优化

可以使用H.264或H.265等高效编码格式替代JPEG，提高视频质量和传输效率：

```python
def encode_frame(frame, quality):
    # 使用H.264编码
    fourcc = cv2.VideoWriter_fourcc(*'H264')
    # 创建内存缓冲区
    buffer = cv2.imencode('.mp4', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buffer
```

### 7.2网络传输优化

实现自适应比特率，根据网络状况动态调整视频质量：

```python
def adaptive_quality(client_stats):
    # 根据客户端的丢包率和延迟调整质量
    if client_stats['packet_loss'] > 0.1:  # 丢包率超过10%
        return "low"
    elif client_stats['packet_loss'] > 0.05:  # 丢包率超过5%
        return "medium"
    else:
        return "high"
```

### 7.3 安全性增强

添加简单的认证机制：

```python
def authenticate_client(client_ip, token):
    # 验证客户端提供的令牌
    if token in valid_tokens:
        return True
    return False
```

### 7.4 多房间支持

扩展系统支持多个直播房间：

```python
# 创建房间字典
rooms = {}

def create_room(room_id, admin_ip):
    rooms[room_id] = {
        'admin': admin_ip,
        'clients': set(),
        'broadcasting': False,
        'video_path': None
    }
    return room_id

def join_room(room_id, client_ip):
    if room_id in rooms:
        rooms[room_id]['clients'].add(client_ip)
        return True
    return False
```

---

## 08 总结

本项目由于时间原因，屏幕共享方面存在bug，可以正常启动功能，但是画面仍然是黑屏，无法观看实时屏幕画面。

通过此次项目，很好增进了我面向ai工程化流程开发能力，使用ai拆解问题，分析问题解决问题的能力，对于调试ai的能力。