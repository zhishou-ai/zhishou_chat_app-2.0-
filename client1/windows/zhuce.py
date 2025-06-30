from PyQt6 import QtWidgets, QtCore
from database import DatabaseManager
from network import WebSocketClient


class RegisterDialog(QtWidgets.QDialog):
    register_success = QtCore.pyqtSignal(dict)  # 注册成功信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("注册")
        self.setFixedSize(300, 220)

        # 初始化UI
        self.setup_ui()

        # 初始化数据库和网络
        self.db_manager = DatabaseManager()
        self.websocket_client = None

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()

        # 用户名输入框
        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("用户名")
        layout.addWidget(self.username_input)

        # 密码输入框
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        # 教师验证码输入框（可选）
        self.teacher_code_input = QtWidgets.QLineEdit()
        self.teacher_code_input.setPlaceholderText("教师验证码（可选，填了即注册教师）")
        layout.addWidget(self.teacher_code_input)

        # 注册按钮
        register_btn = QtWidgets.QPushButton("注册")
        register_btn.clicked.connect(self.handle_register)
        layout.addWidget(register_btn)

        self.setLayout(layout)

    def handle_register(self):
        """处理注册请求"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        teacher_code = self.teacher_code_input.text().strip()

        # 判断是否输入了教师验证码
        is_teacher = bool(teacher_code)
        yanzheng = teacher_code if is_teacher else None

        if not username or not password:
            QtWidgets.QMessageBox.warning(self, "错误", "用户名和密码不能为空")
            return

        message = {
            "action": "register",
            "username": username,
            "password": password,
            "is_teacher": is_teacher,
            "yanzheng": yanzheng
        }

        # 初始化 websocket_client
        self.websocket_client = WebSocketClient(username, password, "register")
        self.websocket_client.is_teacher = is_teacher
        self.websocket_client.yanzheng = yanzheng
        self.websocket_client.message_received.connect(self.handle_websocket_message)
        self.websocket_client.start()
        self.websocket_client.send_message_sync(message)

    def handle_websocket_message(self, message):
        """处理WebSocket消息"""
        action = message.get("action")

        if action == "register_response":
            if message.get("success"):
                # 注册成功，发射信号
                self.register_success.emit(message)
                self.accept()
            else:
                error_msg = message.get("message", "注册失败")
                QtWidgets.QMessageBox.warning(self, "注册失败", error_msg)

    def closeEvent(self, event):
        """关闭事件处理"""
        if self.websocket_client and self.websocket_client.isRunning():
            self.websocket_client.running = False
            self.websocket_client.quit()
            self.websocket_client.wait()
        super().closeEvent(event)