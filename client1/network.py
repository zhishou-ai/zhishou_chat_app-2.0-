import asyncio
import json
import websockets
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import QFileDialog

class WebSocketClient(QThread, QObject):
    message_received = pyqtSignal(dict)
    connection_changed = pyqtSignal(bool)

    def __init__(self, username, password, action_type):
        QThread.__init__(self)
        QObject.__init__(self)
        self.username = username
        self.password = password
        self.action_type = action_type
        self.websocket = None
        self.running = False
        self.server_url = "ws://192.168.3.250:8765"
        self.loop = None
        self.user_id = None
        self._connected = False
        self._pending_file_info = None

    def is_connected(self):
        return self._connected

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

            login_msg = {
                "action": self.action_type,
                "username": self.username,
                "password": self.password,
                "isteacher": getattr(self, "is_teacher", False),
                "yanzheng": getattr(self, "yanzheng", None)
            }
            await self.websocket.send(json.dumps(login_msg))

            self._pending_file_info = None
            while self.running:
                try:
                    message = await self.websocket.recv()
                    if isinstance(message, bytes):
                        if self._pending_file_info:
                            filename = self._pending_file_info.get("filename", "received_file")
                            save_path, _ = QFileDialog.getSaveFileName(
                                None, "保存文件", filename, "所有文件 (*)"
                            )
                            if save_path:
                                with open(save_path, "wb") as f:
                                    f.write(message)
                            self._pending_file_info = None
                    else:
                        data = json.loads(message)
                        # 如果是登录响应且失败，断开连接
                        if data.get('action') == 'login_response' and not data.get('success'):
                            print(f"登录失败: {data.get('error', '未知错误')}")
                            self._connected = False
                            self.connection_changed.emit(False)
                            self.message_received.emit(data)
                            # 断开连接
                            await self.disconnect()
                            break
                        elif data.get('action') == 'error':
                            print(f"服务器错误: {data.get('message', '未知错误')}")
                            self.message_received.emit(data)
                        elif data.get("type") == "file_info":
                            self._pending_file_info = data
                        else:
                            self.message_received.emit(data)
                except websockets.exceptions.ConnectionClosed:
                    self._connected = False
                    self.connection_changed.emit(False)
                    break
        except Exception as e:
            print(f"连接错误: {e}")
            self._connected = False
            self.connection_changed.emit(False)
            # 发送登录失败的响应
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