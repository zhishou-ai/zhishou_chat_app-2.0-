import os
import asyncio
import json
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QMessageBox
import shutil
import os
from PyQt6.QtGui import QDesktopServices

from .ui_main_window import Ui_zhi_liao
from database import DatabaseManager
from network import WebSocketClient
from .qunfa_window import QunfaWindow
from .nicheng_window import ChangeNicknameWindow
from .jianqun_window import CreateGroupWindow
from .denglu import LoginDialog  # 导入程序1的登录对话框

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_zhi_liao()
        self.ui.setupUi(self)
        self.db_manager = DatabaseManager()
        self.username = ""
        self.user_id = None
        self.all_users = []
        self.chat_history = {}
        self.current_chat = None
        self.current_chat_id = None
        self.current_chat_type = None
        self.permission = "student"  # 用户权限属性
        self._pending_downloads = {}
        ##以下的两个新状态，录音可能会用到？##
        # 添加语音按钮状态变量
        self.is_recording = False
        # 连接语音按钮信号
        self.ui.yuyin.clicked.connect(self.toggle_recording)


        # 连接信号和槽
        self.ui.privateChatBtn.clicked.connect(self.show_private_list)
        self.ui.groupChatBtn.clicked.connect(self.show_group_list)
        self.ui.listWidget.itemClicked.connect(self.select_chat_target)
        self.ui.pushButton.clicked.connect(self.open_file_dialog)
        self.ui.pushButton_2.clicked.connect(self.send_chat_message)
        self.ui.textEdit.installEventFilter(self)
        self.ui.pushButton_5.clicked.connect(self.open_qunfa_window)
        self.ui.pushButton_3.clicked.connect(self.open_jianqun_window)
        # 连接文件链接点击信号
        self.ui.shu_chu.setOpenLinks(False)
        self.ui.shu_chu.anchorClicked.connect(self.handle_file_link_clicked)

        self.hide()  # 初始时隐藏主窗口
        self.logged_in = False  # 添加登录状态标记
        self.show_login_dialog()  # 显示登录对话框

    def toggle_recording(self):
        """切换录音状态"""
        self.is_recording = not self.is_recording

        # 根据状态改变按钮颜色
        if self.is_recording:
            # 开始录音状态 - 红色
            self.ui.yuyin.setStyleSheet("""
                QPushButton {
                    background-color: #FF0000;
                    border: none;
                    color: white;
                    padding: 1px;
                    text-align: center;
                    border-radius: 4px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #CC0000;
                    margin: 3px;
                    padding: 0px;
                }
                QPushButton:pressed {
                    background-color: #990000;
                    margin: 6px;
                    padding: 0px;
                }
            """)##这个是为了给开始和停止录音设置不一样的样式表，这个别改！#
            # 这里添加开始录音的逻辑，
        else:
            # 停止录音状态 - 绿色
            self.ui.yuyin.setStyleSheet("""
                QPushButton {
                    background-color: #07C160;
                    border: none;
                    color: white;
                    padding: 1px;
                    text-align: center;
                    border-radius: 4px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #06AD56;
                    margin: 3px;
                    padding: 0px;
                }
                QPushButton:pressed {
                    background-color: #05984D;
                    margin: 6px;
                    padding: 0px;
                }
            """)##这个是为了给开始和停止录音设置不一样的样式表，这个别改！#
            # 这里添加停止录音的逻辑，跟上面的self对齐应该就行


    def handle_register_success(self, message):
        """处理注册成功"""
        self.user_id = message.get("user_id")
        self.username = message.get("username")

        # 保存用户信息到本地数据库
        self.db_manager.save_user(self.user_id, self.username, "")

        # 更新UI显示
        self.ui.userNameLabel.setText(f"当前用户: {self.username}")
        self.display_message("系统", "注册成功！")

        # 设置WebSocket客户端
        self.websocket_client = self.login_dialog.websocket_client
        self.websocket_client.message_received.connect(self.handle_websocket_message)

        # 初始化用户列表
        self.init_user_list()

        # 主动请求在线用户列表
        if self.websocket_client.is_connected():
            self.websocket_client.send_message_sync({
                "action": "get_online_users"
            })





    def handle_login_success(self, message):
        """处理登录成功"""##为了拆分登录界面新建的##
        self.user_id = message.get("user_id")
        self.username = message.get("username")
        self.user_identity = message.get("permission", "")

        # 保存用户信息到本地数据库
        self.db_manager.save_user(self.user_id, self.username, "")

        # 更新UI显示
        self.ui.userNameLabel.setText(f"当前用户: {self.username}")
        self.display_message("系统", "登录成功！")

        # 初始化用户列表
        self.init_user_list()

        # 设置WebSocket客户端
        self.websocket_client = self.login_dialog.websocket_client
        self.websocket_client.message_received.connect(self.handle_websocket_message)

        # 主动请求在线用户列表
        if self.websocket_client.is_connected():
            self.websocket_client.send_message_sync({
                "action": "get_online_users"
            })





    def show_private_list(self):
        """只显示好友列表"""
        self.ui.listWidget.clear()
        contacts = self.db_manager.get_contacts(self.user_id) if self.user_id else []
        seen = set()
        for contact_id, contact_name in contacts:
            if contact_id in seen:
                continue
            user_item = QtWidgets.QListWidgetItem(contact_name)
            user_item.setData(QtCore.Qt.ItemDataRole.UserRole, {
                "username": contact_name,
                "user_id": contact_id
            })
            seen.add(contact_id)
            self.ui.listWidget.addItem(user_item)

    def show_group_list(self):
        """只显示群组列表"""
        self.ui.listWidget.clear()
        groups = self.db_manager.get_groups(self.user_id) if self.user_id else []
        seen = set()
        for group_id, group_name in groups:
            if group_id in seen:
                continue
            group_item = QtWidgets.QListWidgetItem(f"群:{group_name}")
            group_item.setData(QtCore.Qt.ItemDataRole.UserRole, f"群:{group_id}")
            seen.add(group_id)
            self.ui.listWidget.addItem(group_item)

    def open_qunfa_window(self):
        """打开群发窗口"""
        # 如果离线，使用本地联系人
        if not self.websocket_client.is_connected():
            contacts = self.db_manager.get_contacts(self.user_id) if self.user_id else []
            usernames = [contact[1] for contact in contacts]
        else:
            # 用所有用户列表
            usernames = [user["username"] for user in self.all_users if "username" in user]

        # 创建群发窗口
        self.qunfa_window = QunfaWindow(usernames)
        # 显示窗口
        self.qunfa_window.show()

        # 连接群发信号
        if hasattr(self.qunfa_window, 'message_to_send'):
            self.qunfa_window.message_to_send.connect(self.send_bulk_message)

    def send_bulk_message(self, message_content, recipients):
        """发送群发消息"""
        if self.user_id is None:
            self.display_message("系统", "请先登录成功后再发送消息")
            return

        # 获取接收者数据
        for username in recipients:
            # 查找用户ID
            user_id = None
            for user in self.all_users:
                if user["username"] == username:
                    user_id = user["user_id"]
                    break

            if user_id:
                # 保存到本地数据库（标记为已发送）
                timestamp = QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.DateFormat.ISODate)
                self.db_manager.save_message(
                    self.user_id,
                    self.user_id,
                    self.username,
                    user_id,
                    "private",
                    message_content,
                    timestamp,
                    is_sent=1
                )

                # 添加到聊天历史
                receiver = str(user_id)
                if receiver not in self.chat_history:
                    self.chat_history[receiver] = []

                self.chat_history[receiver].append({
                    "sender": "我",
                    "content": message_content,
                    "timestamp": timestamp,
                    "is_group": False
                })

                # 如果在线，通过网络发送
                if self.websocket_client.is_connected():
                    # 构造消息
                    message = {
                        "action": "send_qunfamessage",
                        "sender_id": self.user_id,
                        "receivers_id": [user_id],
                        "content": message_content
                    }
                    try:
                        # 发送消息
                        self.websocket_client.send_message_sync(message)
                    except Exception as e:
                        # 发送失败处理
                        self.display_message("系统", f"发送给 {username} 的消息失败: {str(e)}")

        # 更新显示
        if self.current_chat:
            self.update_chat_display()

        # 显示发送完成提示
        self.display_message("系统", f"群发消息已发送给 {len(recipients)} 个联系人")

    def show_login_dialog(self):
        """显示登录对话框（使用程序1的denglu.py）"""
        self.login_dialog = LoginDialog(self)  # 使用导入的登录对话框

        # 连接信号
        self.login_dialog.login_success.connect(self.handle_login_success)
        self.login_dialog.register_success.connect(self.handle_register_success)

        # 显示对话框
        self.login_dialog.exec()

    def handle_register(self, username, password, teacher_code, dialog):
        """处理注册请求"""
        # 判断是否输入了教师验证码
        is_teacher = bool(teacher_code.strip())
        yanzheng = teacher_code.strip() if is_teacher else None

        # 通过 websocket 发送注册请求
        message = {
            "action": "register",
            "username": username,
            "password": password,
            "is_teacher": is_teacher,
            "yanzheng": yanzheng
        }
        print(message)

        # 初始化 websocket_client 并发送注册消息
        self.websocket_client = WebSocketClient(username, password, "register")
        # 设置教师相关属性
        self.websocket_client.is_teacher = is_teacher
        self.websocket_client.yanzheng = yanzheng

        self.websocket_client.message_received.connect(self.handle_websocket_message)
        self.websocket_client.connection_changed.connect(self.handle_connection_change)
        self.websocket_client.start()
        self.websocket_client.send_message_sync(message)

    def handle_file_link_clicked(self, url):
        """处理文件链接点击事件"""
        # 获取链接中的文件路径
        file_path = url.toString()

        # 如果是本地文件
        if file_path.startswith("file://"):
            file_path = file_path[7:]  # 移除"file://"前缀

            # 检查文件是否存在
            if os.path.exists(file_path):
                # 使用系统默认应用打开文件
                QDesktopServices.openUrl(url)
            else:
                QMessageBox.warning(self, "文件不存在", f"文件 {file_path} 不存在或已被移动。")
        else:
            # 处理其他类型的链接（如HTTP链接）
            QDesktopServices.openUrl(url)



    def handle_auth(self, action_type, username, password, dialog):
        """处理登录请求"""
        username = username.strip()
        password = password.strip()
        message = {
            "action": "login",
            "username": username,
            "password": password,
        }

        if not username or not password:
            QtWidgets.QMessageBox.warning(dialog, "错误", "用户名和密码不能为空")
            return

        # 初始化 websocket_client
        self.websocket_client = WebSocketClient(username, password, action_type)
        self.websocket_client.message_received.connect(self.handle_websocket_message)
        self.websocket_client.connection_changed.connect(self.handle_connection_change)
        self.websocket_client.start()
        self.websocket_client.send_message_sync(message)

    def load_local_contacts(self):
        """加载本地联系人"""
        if self.user_id is not None:
            # 加载联系人
            contacts = self.db_manager.get_contacts(self.user_id)
            for contact_id, contact_name in contacts:
                # 创建联系人列表项
                user_item = QtWidgets.QListWidgetItem(contact_name)
                # 设置项数据
                user_item.setData(QtCore.Qt.ItemDataRole.UserRole, {
                    "username": contact_name,
                    "user_id": contact_id
                })
                # 添加到列表控件
                self.ui.listWidget.addItem(user_item)

            # 加载群组
            groups = self.db_manager.get_groups(self.user_id)
            for group_id, group_name in groups:
                # 创建群组列表项
                group_item = QtWidgets.QListWidgetItem(f"群:{group_name}")
                # 设置项数据
                group_item.setData(QtCore.Qt.ItemDataRole.UserRole, f"群:{group_id}")
                # 添加到列表控件
                self.ui.listWidget.addItem(group_item)

    def init_user_list(self):
        """初始化用户列表控件"""
        # 清除现有项
        self.ui.listWidget.clear()

        # 如果已登录，从数据库加载联系人和群组
        if self.user_id is not None:
            self.load_local_contacts()

    def update_user_list(self, users):
        """更新所有用户列表"""
        self.all_users = users  # <--- 加上这一行，确保all_users有数据
        # 保存当前选中的项
        current_item = self.ui.listWidget.currentItem()
        current_receiver = current_item.data(QtCore.Qt.ItemDataRole.UserRole) if current_item else None

        # 清除现有项
        self.ui.listWidget.clear()

        # 添加在线用户
        for user in users:
            if user.get("username") != self.username:  # 不显示自己
                # 保存到数据库
                self.db_manager.save_contact(self.user_id, user.get("user_id"), user.get("username"))

                # 创建用户列表项
                user_item = QtWidgets.QListWidgetItem(user.get("username"))
                user_item.setData(QtCore.Qt.ItemDataRole.UserRole, {
                    "username": user.get("username"),
                    "user_id": user.get("user_id")
                })
                self.ui.listWidget.addItem(user_item)

    def update_group_list(self, groups):
        """更新群组列表"""
        # 保存服务器推送的群组
        self.groups = groups if isinstance(groups, list) else []
        # 保存到本地数据库
        if self.user_id:
            for group in self.groups:
                self.db_manager.save_group(self.user_id, group.get("group_id"), group.get("group_name"))
        # 更新列表显示
        self.show_group_list()

    def select_chat_target(self, item):
        """选择聊天对象"""
        if self.user_id is None:
            self.display_message("系统", "请先登录成功后再选择聊天对象")
            return

        # 获取接收者数据
        receiver_data = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not receiver_data:
            return

        # 解析接收者数据
        if isinstance(receiver_data, dict):
            # 私聊
            self.current_chat = str(receiver_data["user_id"])
            self.current_chat_id = receiver_data["user_id"]
            self.current_chat_type = "private"
            self.ui.label.setText(f"私聊: {receiver_data['username']}")

            # 请求消息历史
            if self.websocket_client.is_connected():
                self.request_private_history(receiver_data["user_id"])
            else:
                self.load_local_messages(receiver_data["user_id"], "private")
        elif isinstance(receiver_data, str) and receiver_data.startswith("群:"):
            # 群聊
            group_id = receiver_data[2:]
            self.current_chat = f"群:{group_id}"
            self.current_chat_id = group_id
            self.current_chat_type = "group"

            # 获取群组名称
            group_name = "未知群组"
            for group in getattr(self, "groups", []):
                if str(group.get("group_id")) == group_id:
                    group_name = group.get("group_name", "未知群组")
                    break

            self.ui.label.setText(f"群聊: {group_name}")

            # 请求消息历史
            if self.websocket_client.is_connected():
                self.request_group_history(group_id)
            else:
                self.load_local_messages(group_id, "group")
        else:
            return

        # 更新聊天显示
        self.update_chat_display()

    def load_local_messages(self, receiver_id, receiver_type):
        """从本地数据库加载消息"""
        if self.user_id is None:
            return

        # 从数据库获取消息
        messages = self.db_manager.get_messages(self.user_id, receiver_id, receiver_type)

        # 确定接收者标识
        if receiver_type == "group":
            receiver = f"群:{receiver_id}"
        else:
            receiver = str(receiver_id)

        # 存储消息
        if receiver not in self.chat_history:
            self.chat_history[receiver] = []

        # 清空现有消息
        self.chat_history[receiver].clear()

        # 转换消息格式
        for msg in reversed(messages):
            sender_id, sender_name, content, timestamp, is_sent = msg
            converted_msg = {
                "sender": "我" if is_sent else sender_name,
                "content": content,
                "timestamp": timestamp,
                "is_group": receiver_type == "group"
            }
            self.chat_history[receiver].append(converted_msg)

    def request_group_history(self, group_id):
        """请求群组消息历史"""
        if self.user_id is None:
            self.display_message("系统", "请先登录成功后再获取历史消息")
            return

        if not self.websocket_client.is_connected():
            self.display_message("系统", "离线状态下无法获取最新历史消息")
            return

        # 构造获取消息请求
        message = {
            "action": "get_messages",
            "user_id": self.user_id,
            "receiver_type": "group",
            "receiver_id": group_id,
            "page": 1,
            "page_size": 50
        }
        # 发送请求
        self.websocket_client.send_message_sync(message)

    def request_private_history(self, user_id):
        """请求私聊消息历史"""
        if self.user_id is None:
            self.display_message("系统", "请先登录成功后再获取历史消息")
            return

        if not self.websocket_client.is_connected():
            self.display_message("系统", "离线状态下无法获取最新历史消息")
            return

        # 构造获取消息请求
        message = {
            "action": "get_messages",
            "user_id": self.user_id,
            "receiver_type": "private",
            "receiver_id": user_id,
            "page": 1,
            "page_size": 50
        }
        # 发送请求
        self.websocket_client.send_message_sync(message)

    def update_chat_display(self):
        """更新聊天显示区域"""
        if not self.current_chat or self.current_chat not in self.chat_history:
            return

        # 构建HTML格式的聊天内容
        chat_content = ""
        for msg in self.chat_history[self.current_chat][::-1]:
            sender = msg.get("sender", "未知")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")

            try:
                # 格式化时间
                time_str = QtCore.QDateTime.fromString(timestamp[:19], QtCore.Qt.DateFormat.ISODate).toString("yyyy-MM-dd hh:mm:ss")
            except:
                time_str = timestamp[:19] if timestamp else ""

            if sender == "我":
                # 自己发送的消息右对齐
                chat_content += f'<div style="text-align: right; margin: 5px;">'
                chat_content += f'<span style="color: #888; font-size: small;">{time_str}</span><br>'
                chat_content += f'<span style="background-color: #e3f2fd; padding: 5px 10px; border-radius: 10px; display: inline-block;">{content}</span>'
                chat_content += '</div>'
            else:
                # 他人发送的消息左对齐
                chat_content += f'<div style="text-align: left; margin: 5px;">'
                chat_content += f'<span style="font-weight: bold; color: #333;">{sender}</span> '
                chat_content += f'<span style="color: #888; font-size: small;">{time_str}</span><br>'
                chat_content += f'<span style="background-color: #f1f1f1; padding: 5px 10px; border-radius: 10px; display: inline-block;">{content}</span>'
                chat_content += '</div>'

        # 设置HTML内容
        self.ui.shu_chu.setHtml(chat_content)
        # 滚动到底部
        self.ui.shu_chu.verticalScrollBar().setValue(self.ui.shu_chu.verticalScrollBar().maximum())

    def handle_websocket_message(self, message):
        """处理从WebSocket接收到的消息"""
        action = message.get("action")

        if action == "message_history":
            # 处理消息历史
            receiver_type = message.get("receiver_type")
            receiver_id = message.get("receiver_id")
            messages = message.get("messages", [])

            # 确定接收者标识
            receiver = f"群:{receiver_id}" if receiver_type == "group" else str(receiver_id)

            # 初始化消息列表
            if receiver not in self.chat_history:
                self.chat_history[receiver] = []
            else:
                self.chat_history[receiver].clear()

            # 处理每条消息
            for msg in messages:
                sender_id = msg.get("sender_id")
                content = msg.get("content")
                timestamp = msg.get("created_at", "")
                sender_name = msg.get("sender_name", f"用户{sender_id}")

                # 转换消息格式
                converted_msg = {
                    "sender": "我" if sender_id == self.user_id else sender_name,
                    "content": content,
                    "timestamp": timestamp,
                    "is_group": receiver_type == "group"
                }

                # 保存到本地数据库
                self.db_manager.save_message(
                    self.user_id,
                    sender_id,
                    sender_name,
                    receiver_id,
                    receiver_type,
                    content,
                    timestamp,
                    is_sent=(sender_id == self.user_id)
                )

                # 添加到聊天历史
                self.chat_history[receiver].append(converted_msg)

            # 更新显示
            if self.current_chat == receiver:
                self.update_chat_display()

        elif action in ["new_private_message", "new_group_message"]:
            # 统一处理新消息
            is_group = action == "new_group_message"
            msg = message.get("message", {})
            sender_id = msg.get("sender_id")
            content = msg.get("content")
            timestamp = msg.get("timestamp", "")
            sender_name = msg.get("sender_name", f"用户{sender_id}")

            if is_group:
                group_id = message.get("group_id")
                receiver = f"群:{group_id}"
                receiver_id = group_id
            else:
                receiver_id = msg.get("receiver_id") if sender_id == self.user_id else sender_id
                receiver = str(receiver_id)

            # 初始化消息列表
            if receiver not in self.chat_history:
                self.chat_history[receiver] = []

            # 转换消息格式
            converted_msg = {
                "sender": "我" if sender_id == self.user_id else sender_name,
                "content": content,
                "timestamp": timestamp,
                "is_group": is_group
            }

            # 保存到本地数据库
            self.db_manager.save_message(
                self.user_id,
                sender_id,
                sender_name,
                receiver_id,
                "group" if is_group else "private",
                content,
                timestamp,
                is_sent=(sender_id == self.user_id))

            # 添加到聊天历史
            self.chat_history[receiver].append(converted_msg)

            # 更新显示
            if self.current_chat == receiver:
                self.update_chat_display()

        elif action == "group_list":
            # 更新群组列表
            groups = message.get("groups", [])
            self.update_group_list(groups)

        elif action == "login_response":
            # 登录响应处理
            if message.get("success"):
                self.user_id = message.get("user_id")
                self.username = message.get("username")
                self.user_identity = message.get("permission", "")
                self.db_manager.save_user(self.user_id, self.username, "")

                # 更新UI显示
                self.ui.userNameLabel.setText(f"当前用户: {self.username}")
                self.display_message("系统", "登录成功！")
                self.init_user_list()

                # 关闭登录对话框
                if hasattr(self, 'login_dialog'):
                    self.login_dialog.accept()

        elif action == "error":
            # 错误处理
            error_msg = message.get("message", "未知错误")
            self.display_message("系统", f"错误: {error_msg}")

            # 如果是登录/注册错误，保持对话框打开
            if action in ["login_response", "register_response"] and not message.get("success"):
                QtWidgets.QMessageBox.warning(self.login_dialog, "错误", error_msg)

        elif action == "online_users":
            # 服务器推送的在线用户列表
            users = message.get("users", [])
            self.update_user_list(users)

        elif action == "group_created":
            # 群组创建成功
            group_name = message.get("group_name")
            group_id = message.get("group_id")
            self.display_message("系统", f"群组 '{group_name}' 创建成功！")

        elif action == "added_to_group":
            # 被添加到群组
            group_name = message.get("group_name")
            group_id = message.get("group_id")
            self.display_message("系统", f"已被添加到群组 '{group_name}'！")

        elif action == "register_response":
            # 注册响应
            if message.get("success"):
                # 注册成功处理
                self.user_id = message.get("user_id")
                self.username = message.get("username")

                # 保存用户信息到本地数据库
                self.db_manager.save_user(self.user_id, self.username, "")

                # 启用控件
                self.ui.listWidget.setEnabled(True)
                self.ui.pushButton_2.setEnabled(True)
                self.display_message("系统", "注册成功！")

                # 更新UI显示
                self.ui.userNameLabel.setText(f"当前用户: {self.username}")

                # 关闭登录对话框
                if hasattr(self, 'login_dialog'):
                    self.login_dialog.accept()

                # 初始化用户列表
                self.init_user_list()

                # 主动请求在线用户列表
                if self.websocket_client.is_connected():
                    self.websocket_client.send_message_sync({
                        "action": "get_online_users"
                    })
            else:
                # 注册失败处理
                error_msg = message.get("message", "未知错误")
                self.display_message("系统", f"注册失败：{error_msg}")
                QtWidgets.QMessageBox.warning(self.login_dialog, "注册失败", error_msg)

        elif action == "all_users":
            # 所有用户列表
            users = message.get("users", [])
            self.update_user_list(users)

    def handle_connection_change(self, connected):
        """处理连接状态变化"""
        if connected:
            # 连接成功
            self.display_message("系统", "已连接到聊天服务器")
        else:
            # 连接断开
            self.display_message("系统", "与聊天服务器的连接已断开")

    def display_message(self, sender, content):
        """在聊天区域显示消息"""
        # 获取当前文本
        current_text = self.ui.shu_chu.toHtml()
        new_text = f"{current_text}<br>{sender}: {content}"
        # 设置HTML内容
        self.ui.shu_chu.setHtml(new_text)
        # 滚动到底部
        self.ui.shu_chu.verticalScrollBar().setValue(self.ui.shu_chu.verticalScrollBar().maximum())

    def send_chat_message(self):
        """发送聊天消息"""
        if self.user_id is None:
            self.display_message("系统", "请先登录成功后再发送消息")
            return

        # 获取输入文本
        text = self.ui.textEdit.toPlainText().strip()
        if not text:
            return

        if not self.current_chat:
            self.display_message("系统", "请选择聊天对象")
            return

        # 判断是否是群聊
        is_group = self.current_chat.startswith("群:")
        receiver_id = self.current_chat_id
        receiver_type = "group" if is_group else "private"

        # 保存到本地数据库（标记为已发送）
        timestamp = QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.DateFormat.ISODate)
        self.db_manager.save_message(
            self.user_id,
            self.user_id,
            self.username,
            receiver_id,
            receiver_type,
            text,
            timestamp,
            is_sent=1
        )

        # 添加到聊天历史
        if self.current_chat not in self.chat_history:
            self.chat_history[self.current_chat] = []

        self.chat_history[self.current_chat].append({
            "sender": "我",
            "content": text,
            "timestamp": timestamp,
            "is_group": is_group
        })

        # 更新显示
        self.update_chat_display()

        # 如果在线，通过网络发送
        if self.websocket_client.is_connected():
            # 构造消息
            message = {
                "action": "send_message",
                "sender_id": self.user_id,
                "receiver_type": receiver_type,
                "receiver_id": receiver_id,
                "content": text
            }
            try:
                # 发送消息
                self.websocket_client.send_message_sync(message)
                # 清空输入框
                self.ui.textEdit.clear()
            except Exception as e:
                # 发送失败处理
                self.display_message("系统", f"发送消息失败: {str(e)}")
        else:
            # 离线状态处理
            self.display_message("系统", "离线状态下消息已保存到本地")
            # 清空输入框
            self.ui.textEdit.clear()

    def open_nicheng_window(self):
        """打开昵称设置窗口"""
        # 创建昵称设置窗口
        self.nicheng_window = ChangeNicknameWindow()
        # 显示窗口
        self.nicheng_window.show()

        # 连接昵称更改信号
        if hasattr(self.nicheng_window, 'nickname_changed'):
            self.nicheng_window.nickname_changed.connect(self.update_nickname)

    def update_nickname(self, new_nickname):
        """更新昵称"""
        # 构造更新昵称消息
        message = {
            "action": "update_nickname",
            "username": self.username,
            "nickname": new_nickname
        }
        # 通过WebSocket发送（使用同步方法）
        self.websocket_client.send_message_sync(message)

        # 更新本地显示
        self.username = new_nickname
        self.ui.userNameLabel.setText(f"当前用户: {new_nickname}")

    def open_jianqun_window(self):
        """打开建群窗口"""
        # 如果离线，使用本地联系人
        if not self.websocket_client.is_connected():
            contacts = self.db_manager.get_contacts(self.user_id) if self.user_id else []
            usernames = [contact[1] for contact in contacts]
        else:
            # 用所有用户列表
            usernames = [user["username"] for user in self.all_users if "username" in user]

        # 创建建群窗口
        self.jianqun_window = CreateGroupWindow(usernames)
        # 显示窗口
        self.jianqun_window.show()

        # 连接建群信号
        if hasattr(self.jianqun_window, 'group_created'):
            self.jianqun_window.group_created.connect(self.create_group)

    def create_group(self, group_name, members):
        """创建新群组"""
        # members 是用户名列表，需要转成 user_id 列表
        user_ids = []

        # 如果在线，使用服务器用户列表
        if self.websocket_client.is_connected():
            for username in members:
                for user in self.all_users:
                    if user["username"] == username:
                        user_ids.append(user["user_id"])
                        break
        else:
            # 如果离线，使用本地数据库
            if self.user_id:
                contacts = self.db_manager.get_contacts(self.user_id)
                username_to_id = {name: id for id, name in contacts}
                for username in members:
                    if username in username_to_id:
                        user_ids.append(username_to_id[username])

        # 把自己也加进去（如果没选自己）
        if self.user_id not in user_ids:
            user_ids.append(self.user_id)

        # 如果在线，发送建群请求
        if self.websocket_client.is_connected():
            # 构造建群消息
            message = {
                "action": "create_group",
                "group_name": group_name,
                "creator_id": self.user_id,
                "initial_members": user_ids
            }
            # 发送消息
            self.websocket_client.send_message_sync(message)
        else:
            # 离线状态处理
            self.display_message("系统", "离线状态下无法创建新群组")

    def open_file_dialog(self):
        """选择文件并发送给当前聊天对象"""
        if not hasattr(self, "current_chat_id") or not self.current_chat_id:
            self.display_message("系统", "请先选择聊天对象")
            return
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("选择文件")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                asyncio.run(self.send_file_to_user(file_path, self.current_chat_id))

    async def send_file_to_user(self, file_path, receiver_id):
        """异步发送文件给指定用户"""
        if not self.websocket_client.is_connected():
            self.display_message("系统", "未连接服务器，无法发送文件")
            return
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
            filename = os.path.basename(file_path)
            filesize = len(file_data)
            # 先发文件信息
            file_info = {
                "type": "file_info",
                "filename": filename,
                "filesize": filesize,
                "receiver_id": receiver_id
            }
            await self.websocket_client.websocket.send(json.dumps(file_info))
            # 再发二进制内容
            await self.websocket_client.websocket.send(file_data)
            self.display_message("系统", f"文件 {filename} 已发送")
        except Exception as e:
            self.display_message("系统", f"发送文件失败: {e}")

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 断开WebSocket连接
        if hasattr(self, 'websocket_client') and self.websocket_client.isRunning():
            # 停止线程
            self.websocket_client.running = False
            # 退出线程
            self.websocket_client.quit()
            # 等待线程结束
            self.websocket_client.wait()
        # 接受关闭事件
        event.accept()

    def eventFilter(self, obj, event):
        # 回车发送消息
        if obj == self.ui.textEdit and event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                if not (event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier):
                    # 发送消息
                    self.send_chat_message()
                    return True  # 阻止回车换行
        return super().eventFilter(obj, event)

    def get_username_by_id(self, user_id):
        # 先从在线用户中查找
        for user in getattr(self, "all_users", []):
            if user.get("user_id") == user_id:
                return user.get("username")

        # 如果是离线模式或未找到，从本地数据库查找
        if self.user_id is not None:
            contacts = self.db_manager.get_contacts(self.user_id)
            for contact_id, contact_name in contacts:
                if contact_id == user_id:
                    return contact_name

        # 默认返回用户ID
        return f"用户{user_id}"