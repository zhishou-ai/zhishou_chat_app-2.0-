import asyncio
import json
import websockets
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import QFileDialog
import os

class WebSocketClient(QThread, QObject):
    message_received = pyqtSignal(dict)
    connection_changed = pyqtSignal(bool)

    def __init__(self, username, password, action_type, yanzheng=None, is_teacher=False):
        QThread.__init__(self)
        QObject.__init__(self)
        self.username = username
        self.password = password
        self.action_type = action_type
        self.websocket = None
        self.running = False
        self.server_url = "ws://192.168.3.170:8765"
        self.loop = None
        self.user_id = None
        self._connected = False
        self._pending_file_info = None
        self.is_teacher = is_teacher  # 添加教师标志
        self.yanzheng = yanzheng    # 添加验证码属性

    def is_connected(self):
        return self._connected
    
    def handle_file_download(self, filename, file_data):
        """处理文件下载 - 保存到客户端本地"""
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 创建客户端本地的临时目录
        temp_dir = os.path.join(current_dir, "temp_files")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 保存文件到客户端本地
        temp_path = os.path.join(temp_dir, filename)
        try:
            with open(temp_path, "wb") as f:
                f.write(file_data)
            return temp_path
        except Exception as e:
            print(f"保存文件失败: {e}")
            self.message_received.emit({
                "action": "file_error",
                "filename": filename,
                "error": str(e)
            })
            return None

    async def connect(self):
        print(f"尝试连接到 WebSocket 服务器: {self.server_url}")
        try:
            self.websocket = await asyncio.wait_for(
                websockets.connect(
                    self.server_url,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=1
                ),
                timeout=5.0
            )
            self._connected = True
            self.connection_changed.emit(True)

            # 根据操作类型构建不同的认证消息
            if self.action_type == "register":
                login_msg = {
                    "action": self.action_type,
                    "username": self.username,
                    "password": self.password,
                    "yanzheng": self.yanzheng,
                    "is_teacher": self.is_teacher
                }
            else:
                login_msg = {
                    "action": self.action_type,
                    "username": self.username,
                    "password": self.password
                }
            
            print(f"发送认证消息: {login_msg}")
            await self.websocket.send(json.dumps(login_msg))

            self._pending_file_info = None
            while self.running:
                try:
                    message = await self.websocket.recv()
                    if isinstance(message, bytes):
                        # 处理二进制文件数据
                        if self._pending_file_info:
                            filename = self._pending_file_info.get("filename", "received_file")
                            # 保存到客户端本地的临时目录
                            save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "temp_files"))
                            os.makedirs(save_dir, exist_ok=True)
                            save_path = os.path.join(save_dir, filename)
                            
                            try:
                                with open(save_path, "wb") as f:
                                    f.write(message)
                                # 发送文件接收成功信号
                                self.message_received.emit({
                                    "action": "file_downloaded",
                                    "filename": filename,
                                    "temp_path": save_path,
                                    "sender_id": self._pending_file_info.get("sender_id")
                                })
                            except Exception as e:
                                self.message_received.emit({
                                    "action": "file_error",
                                    "filename": filename,
                                    "error": str(e)
                                })
                            finally:
                                self._pending_file_info = None
                        else:
                            print("收到二进制数据但没有 file_info")
                    else:
                        data = json.loads(message)
                        # 处理文件信息通知
                        if data.get("action") == "file_received":
                            # 仅传递文件名，不传递完整路径
                            self.message_received.emit({
                                "action": "file_received",
                                "filename": data["filename"],
                                "sender_id": data["sender_id"]
                            })
                        elif data.get("action") == "login_response" and data.get("success"):
                            self.user_id = data["user_id"]
                            self.permission = data.get("permission", "student")
                        # 处理文件下载开始通知
                        elif data.get("action") == "file_download_start":
                            self._pending_file_info = {
                                "filename": data["filename"]
                            }
                        self.message_received.emit(data)

                except websockets.exceptions.ConnectionClosed:
                    self._connected = False
                    self.connection_changed.emit(False)
                    break
        except Exception as e:
            print(f"连接错误: {e}")
            self._connected = False
            self.connection_changed.emit(False)
            self.message_received.emit({
                "action": f"{self.action_type}_response",
                "success": False,
                "error": str(e),
                "user_id": -1,
                "username": self.username
            })

    def send_message_sync(self, message: dict):
        if self.loop and self.running and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._send_message_async(message), self.loop)

    async def _send_message_async(self, message: dict):
        try:
            if self.websocket is None or self.websocket.closed:
                print("WebSocket 未连接，尝试重新连接...")
                await self.connect()

            if self.websocket and not self.websocket.closed:
                print(f"发送消息: {message}")
                await self.websocket.send(json.dumps(message))
            else:
                print("无法发送消息：WebSocket 连接不可用")
        except Exception as e:
            print(f"发送消息失败: {e}")
            self._connected = False
            self.connection_changed.emit(False)

    async def disconnect(self):
        self.running = False
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        self._connected = False
        self.connection_changed.emit(False)

    def stop(self):
        self.running = False
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self.disconnect(), self.loop)

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.running = True
        self.loop.run_until_complete(self.connect())
        self.loop.close()