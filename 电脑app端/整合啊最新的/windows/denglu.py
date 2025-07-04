from PyQt6 import QtWidgets, QtCore
from database import DatabaseManager
from network import WebSocketClient


class LoginDialog(QtWidgets.QDialog):
    login_success = QtCore.pyqtSignal(dict)  # 登录成功信号
    register_success = QtCore.pyqtSignal(dict)  # 注册成功信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("登录/注册")
        self.setFixedSize(450, 450)

        # 初始化UI
        self.setup_ui()

        # 初始化数据库和网络
        self.db_manager = DatabaseManager()
        self.websocket_client = None

    def setup_ui(self):

        # 创建标题标签（水平居中）
        self.title_label = QtWidgets.QLabel(self)
        self.title_label.setGeometry(QtCore.QRect(124, 30, 201, 41))  # (450-201)/2=124.5→124
        self.title_label.setStyleSheet("""
            QLabel {
                font-family: "微软雅黑";
                font-weight: bold;
                font-size: 18px;
                color: #333333;
                background-color: transparent;
                qproperty-alignment: AlignCenter;
                padding: 0px;
                border: none;
            }
        """)
        self.title_label.setText("登录/注册")  # 设置标签文本




        # -------------------- 用户名输入框控件 --------------------
        self.username_input = QtWidgets.QLineEdit(self)
        self.username_input.setPlaceholderText("用户名")
        self.username_input.setGeometry(115, 110, 221, 41)  # 调整位置和大小
        self.username_input.setStyleSheet(" background-color: rgb(255, 255, 255);  \n"
                                    "QLineEdit, QTextEdit {\n"
                                    "    border: 1px solid #cccccc;  /* 边框颜色 */\n"
                                    "    border-radius: 5px;         /* 圆角半径（可调整） */\n"
                                    "    padding: 5px;               /* 内边距 */\n"
                                    "    color: #666666;             /* 灰色字体 */\n"
                                    "    font-size: 14px;            /* 字体大小（可选） */\n"
                                    "}")

        # -------------------- 密码输入框控件 --------------------
        self.password_input = QtWidgets.QLineEdit(self)
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.password_input.setGeometry(115, 160, 220, 41)  # 调整位置和大小

        # -------------------- 教师验证码输入框控件 --------------------
        self.teacher_code_input = QtWidgets.QLineEdit(self)
        self.teacher_code_input.setPlaceholderText("教师验证码（可选，填了即注册教师）")
        self.teacher_code_input.setGeometry(115, 210, 221, 41)  # 调整位置和大小
        self.teacher_code_input.setStyleSheet(" background-color: rgb(255, 255, 255);  \n"
                                      "QLineEdit, QTextEdit {\n"
                                      "    border: 1px solid #cccccc;  /* 边框颜色 */\n"
                                      "    border-radius: 5px;         /* 圆角半径（可调整） */\n"
                                      "    padding: 5px;               /* 内边距 */\n"
                                      "    color: #666666;             /* 灰色字体 */\n"
                                      "    font-size: 14px;            /* 字体大小（可选） */\n"
                                      "}")
        # -------------------- 登录按钮控件 --------------------
        login_btn = QtWidgets.QPushButton("登录", self)
        login_btn.setGeometry(115, 260, 221, 40)  # x=115保持与其他控件对齐，宽度221与输入框一致
        login_btn.setStyleSheet("""
            /* 蓝色按钮样式 */
            QPushButton {
                background-color: rgb(74, 126, 246);
                border-radius: 2.5px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
            }
            /* 按下时的深蓝色效果 */
            QPushButton:pressed {
                background-color: rgb(50, 88, 173);
                border: 2px solid #004a87;
            }
        """)
        login_btn.clicked.connect(self.handle_login)

        # -------------------- 注册按钮控件 --------------------
        register_btn = QtWidgets.QPushButton("注册", self)
        register_btn.setGeometry(115, 310, 221, 40)  # x相同，y=260+40+10=310（10px间距）
        register_btn.setStyleSheet(login_btn.styleSheet())  # 复用相同的样式表
        register_btn.clicked.connect(self.handle_register)


    def handle_login(self):
        """处理登录请求"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QtWidgets.QMessageBox.warning(self, "错误", "用户名和密码不能为空")
            return

        message = {
            "action": "login",
            "username": username,
            "password": password,
        }

        # 初始化 websocket_client
        self.websocket_client = WebSocketClient(username, password, "login")
        self.websocket_client.message_received.connect(self.handle_websocket_message)
        self.websocket_client.start()
        self.websocket_client.send_message_sync(message)

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

        if action == "login_response":
            if message.get("success"):
                # 登录成功，发射信号
                self.login_success.emit(message)
                self.accept()
            else:
                error_msg = message.get("message", "登录失败")
                QtWidgets.QMessageBox.warning(self, "登录失败", error_msg)

        elif action == "register_response":
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