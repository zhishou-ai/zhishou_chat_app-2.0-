import os
import asyncio
import json
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QMessageBox
import shutil
from PyQt6.QtGui import QDesktopServices

from .ui_main_window import Ui_zhi_liao
from database import DatabaseManager
from network import WebSocketClient
from .qunfa_window import QunfaWindow
from .nicheng_window import ChangeNicknameWindow
from .jianqun_window import CreateGroupWindow
from .denglu import LoginDialog

import threading
import tempfile
import numpy as np
import sounddevice as sd    ###
import soundfile as sf


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_zhi_liao()
        self.ui.setupUi(self)
        self.db_manager = DatabaseManager()  # 数据库管理实例
        self.username = ""  # 当前用户名
        self.user_id = None  # 当前用户ID
        self.all_users = []  # 所有用户列表
        self.chat_history = {}  # 聊天历史记录
        self.current_chat = None  # 当前聊天对象标识
        self.current_chat_id = None  # 当前聊天对象ID
        self.current_chat_type = None  # 当前聊天类型（私聊/群聊）
        self.permission = "student"  # 用户权限
        self._pending_downloads = {}  # 待下载文件队列
        self.is_recording = False  # 录音状态标识
        self.audio_recording_thread = None  # 录音线程
        self.audio_data = None  # 录音数据
        self.audio_sample_rate = 16000  # 采样率，适合语音
        self.audio_channels = 1  # 单声道
        self.audio_tempfile = None  # 临时音频文件路径

        # 连接界面元素信号与槽函数
        self.ui.privateChatBtn.clicked.connect(self.show_private_list)  # 显示私聊列表
        self.ui.groupChatBtn.clicked.connect(self.show_group_list)  # 显示群聊列表
        self.ui.treeView.clicked.connect(self.select_chat_target)  # 选择聊天对象
        self.ui.pushButton.clicked.connect(self.open_file_dialog)  # 打开文件选择对话框
        self.ui.pushButton_2.clicked.connect(self.send_chat_message)  # 发送聊天消息
        self.ui.textEdit.installEventFilter(self)  # 安装事件过滤器
        self.ui.pushButton_5.clicked.connect(self.open_qunfa_window)  # 打开群发窗口
        self.ui.pushButton_3.clicked.connect(self.open_jianqun_window)  # 打开建群窗口
        self.ui.yuyin.clicked.connect(self.toggle_recording)  # 切换录音状态
        self.ui.shu_chu.setOpenLinks(False)  # 禁止自动打开链接
        self.ui.shu_chu.anchorClicked.connect(self.handle_file_link_clicked)  # 处理文件链接点击

        self.hide()  # 初始隐藏主窗口
        self.logged_in = False  # 登录状态标识
        self.show_login_dialog()  # 显示登录对话框

    def toggle_recording(self):
        """切换录音状态并更新按钮样式，集成录音与自动发送"""
        self.is_recording = not self.is_recording

        if self.is_recording:
            # 录音中按钮样式（红色）
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
            """)
            # 开始录音（新线程，防止阻塞UI）
            self.audio_data = []
            self.audio_recording_thread = threading.Thread(target=self._record_audio_thread, daemon=True)
            self.audio_recording_thread.start()
        else:
            # 未录音按钮样式（绿色）
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
            """)
            # 停止录音并自动发送
            sd.stop()
            if self.audio_recording_thread and self.audio_recording_thread.is_alive():
                self.audio_recording_thread.join(timeout=2)
            if self.audio_data:
                audio_np = np.concatenate(self.audio_data, axis=0)
                # 保存到临时文件
                temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
                os.close(temp_fd)
                sf.write(temp_path, audio_np, self.audio_sample_rate, format='WAV', subtype='PCM_16')
                self.audio_tempfile = temp_path
                # 自动发送语音
                self.send_voice_message(temp_path)
                # 清理
                self.audio_data = None
                self.audio_tempfile = None

    def _record_audio_thread(self):
        """录音线程，采集音频数据"""
        def callback(indata, frames, time, status):
            if status:
                print(f"录音状态: {status}")
            self.audio_data.append(indata.copy())
        try:
            with sd.InputStream(samplerate=self.audio_sample_rate, channels=self.audio_channels, dtype='float32', callback=callback):
                while self.is_recording:
                    sd.sleep(100)
        except Exception as e:
            print(f"录音错误: {e}")
            self.is_recording = False

    def send_voice_message(self, file_path):
        """发送语音文件到服务端（假设走文件发送通道）"""
        if not self.current_chat_id or not self.current_chat_type:
            self.display_message("系统", "请先选择聊天对象后再发送语音")
            return
        # 这里假设有文件发送接口，走和图片/文件一样的逻辑
        try:
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            filename = os.path.basename(file_path)
            # 构造消息，假设websocket_client有send_file方法
            if hasattr(self, 'websocket_client') and self.websocket_client.is_connected():
                self.websocket_client.send_file(
                    file_bytes=file_bytes,
                    filename=filename,
                    receiver_id=self.current_chat_id,
                    receiver_type=self.current_chat_type
                )
                self.display_message("系统", f"语音消息已发送: {filename}")
            else:
                self.display_message("系统", "离线状态下无法发送语音")
        except Exception as e:
            self.display_message("系统", f"语音发送失败: {e}")

    def update_user_list(self, users):
        """更新用户列表到TreeView控件"""
        # 清空现有项但保留分组
        self.ui.teachersItem.removeRows(0, self.ui.teachersItem.rowCount())
        self.ui.studentsItem.removeRows(0, self.ui.studentsItem.rowCount())

        self.all_users = users

        for user in users:
            if not user.get("username") or not user.get("user_id"):
                continue
            if user.get("username") == self.username:
                continue

            user_item = QtGui.QStandardItem(user["username"])
            user_item.setData({
                "username": user["username"],
                "user_id": user["user_id"],
                "permission": user.get("permission", "student")
            }, QtCore.Qt.ItemDataRole.UserRole)

            # 根据用户权限添加到不同分组
            if user.get("permission") == "teacher":
                self.ui.teachersItem.appendRow(user_item)
            else:
                self.ui.studentsItem.appendRow(user_item)

        # 更新分组标题显示数量
        self.ui.teachersItem.setText(f"老师 ({self.ui.teachersItem.rowCount()})")
        self.ui.studentsItem.setText(f"学生 ({self.ui.studentsItem.rowCount()})")

    def select_chat_target(self, index):
        """选择聊天对象（TreeView版本）"""
        if self.user_id is None:
            self.display_message("系统", "请先登录成功后再选择聊天对象")
            return

        item = self.ui.treeModel.itemFromIndex(index)
        # 检查是否选中的是分组项而非用户/群组项
        if not item or item is self.ui.teachersItem or item is self.ui.studentsItem:
            return

        user_data = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not user_data:
            return

        # 处理私聊或群聊选择
        if isinstance(user_data, dict):
            # 私聊情况
            self.current_chat = str(user_data["user_id"])
            self.current_chat_id = user_data["user_id"]
            self.current_chat_type = "private"
            self.ui.label.setText(f"私聊: {user_data['username']}")

            # 根据网络连接状态获取聊天历史
            if self.websocket_client.is_connected():
                self.request_private_history(user_data["user_id"])
            else:
                self.load_local_messages(user_data["user_id"], "private")
        elif isinstance(user_data, str) and user_data.startswith("群:"):
            # 群聊情况
            group_id = user_data[2:]
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

            # 根据网络连接状态获取聊天历史
            if self.websocket_client.is_connected():
                self.request_group_history(group_id)
            else:
                self.load_local_messages(group_id, "group")

        self.update_chat_display()  # 更新聊天显示

    def show_private_list(self):
        """显示好友列表（TreeView版本）"""
        # 清空现有项但保留分组结构
        self.ui.teachersItem.removeRows(0, self.ui.teachersItem.rowCount())
        self.ui.studentsItem.removeRows(0, self.ui.studentsItem.rowCount())

        # 根据网络连接状态获取联系人
        if self.websocket_client.is_connected():
            self.websocket_client.send_message_sync({
                "action": "get_online_users"
            })
        else:
            contacts = self.db_manager.get_contacts(self.user_id) if self.user_id else []
            for contact_id, contact_name in contacts:
                user_item = QtGui.QStandardItem(contact_name)
                user_item.setData({
                    "username": contact_name,
                    "user_id": contact_id,
                    "permission": "unknown"
                }, QtCore.Qt.ItemDataRole.UserRole)
                self.ui.studentsItem.appendRow(user_item)

        # 更新分组标题显示数量
        self.ui.teachersItem.setText(f"老师 ({self.ui.teachersItem.rowCount()})")
        self.ui.studentsItem.setText(f"学生 ({self.ui.studentsItem.rowCount()})")

    def show_group_list(self):
        """显示群组列表（TreeView版本）"""
        # 清空现有项但保留分组结构
        self.ui.teachersItem.removeRows(0, self.ui.teachersItem.rowCount())
        self.ui.studentsItem.removeRows(0, self.ui.studentsItem.rowCount())

        # 从数据库获取群组信息
        groups = self.db_manager.get_groups(self.user_id) if self.user_id else []
        seen = set()
        for group_id, group_name in groups:
            if group_id in seen:
                continue
            # 创建群组项并添加到学生分组
            group_item = QtGui.QStandardItem(f"群: {group_name}")
            group_item.setData(f"群:{group_id}", QtCore.Qt.ItemDataRole.UserRole)
            seen.add(group_id)
            self.ui.studentsItem.appendRow(group_item)

        # 更新分组标题显示数量
        self.ui.teachersItem.setText(f"老师 (0)")
        self.ui.studentsItem.setText(f"学生和群组 ({self.ui.studentsItem.rowCount()})")

    # 保留其余原有方法不变 ...

    def show_group_list(self):
        """显示群组列表（TreeView版本）"""
        # 清空现有项但保留分组结构
        self.ui.teachersItem.removeRows(0, self.ui.teachersItem.rowCount())
        self.ui.studentsItem.removeRows(0, self.ui.studentsItem.rowCount())

        # 从数据库获取群组信息
        groups = self.db_manager.get_groups(self.user_id) if self.user_id else []
        seen = set()
        for group_id, group_name in groups:
            if group_id in seen:
                continue
            # 创建群组项并设置数据
            group_item = QtGui.QStandardItem(f"群: {group_name}")
            group_item.setData(f"群:{group_id}", QtCore.Qt.ItemDataRole.UserRole)
            seen.add(group_id)
            # 添加到学生分组
            self.ui.studentsItem.appendRow(group_item)

        # 更新分组标题显示数量
        self.ui.teachersItem.setText(f"老师 (0)")
        self.ui.studentsItem.setText(f"学生和群组 ({self.ui.studentsItem.rowCount()})")

    def open_qunfa_window(self):
        """打开群发窗口"""
        # 准备用户数据，包含用户名和权限
        user_data = []
        if not self.websocket_client.is_connected():
            # 离线模式从数据库获取
            contacts = self.db_manager.get_contacts(self.user_id) if self.user_id else []
            for contact_id, contact_name in contacts:
                # 这里假设无法获取离线用户的权限，可以默认为学生
                user_data.append({"username": contact_name, "permission": "student"})
        else:
            # 在线模式使用所有用户列表
            for user in self.all_users:
                if "username" in user and user["username"] != self.username:
                    user_data.append({
                        "username": user["username"],
                        "permission": user.get("permission", "student")
                    })

        # 创建并显示群发窗口，传入完整的用户数据而不仅仅是用户名列表
        self.qunfa_window = QunfaWindow(user_data)
        self.qunfa_window.show()

        # 连接群发信号
        if hasattr(self.qunfa_window, 'message_to_send'):
            self.qunfa_window.message_to_send.connect(self.send_bulk_message)

    def send_bulk_message(self, message_content, recipients):
        """发送群发消息"""
        if self.user_id is None:
            self.display_message("系统", "请先登录成功后再发送消息")
            return

        # 遍历接收者并发送消息
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
                    "is_group": False,
                    "is_file": False,
                    "file_url": ""
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
        """显示登录对话框（使用分离的denglu.py）"""
        self.login_dialog = LoginDialog(self)  # 使用导入的登录对话框

        # 连接登录成功和注册成功信号
        self.login_dialog.login_success.connect(self.handle_login_success)
        self.login_dialog.register_success.connect(self.handle_register_success)

        # 显示对话框
        self.login_dialog.exec()

    def handle_login_success(self, message):
        """处理登录成功逻辑"""
        self.user_id = message.get("user_id")
        self.username = message.get("username")
        self.permission = message.get("permission", "student")  # 获取用户权限

        # 保存用户信息到本地数据库
        self.db_manager.save_user(
            self.user_id,
            self.username,
            "",  # 不保存密码
            self.permission  # 保存权限
        )

        # 更新UI显示
        self.ui.userNameLabel.setText(f"当前用户: {self.username} ({self.permission})")
        self.display_message("系统", "登录成功！")

        # 设置WebSocket客户端
        self.websocket_client = self.login_dialog.websocket_client
        self.websocket_client.message_received.connect(self.handle_websocket_message)
        self.websocket_client.connection_changed.connect(self.handle_connection_change)

        # 初始化用户列表
        self.init_user_list()

        # 主动请求在线用户列表
        if self.websocket_client.is_connected():
            self.websocket_client.send_message_sync({
                "action": "get_online_users"
            })

    def handle_register_success(self, message):
        """处理注册成功逻辑"""
        self.user_id = message.get("user_id")
        self.username = message.get("username")
        self.permission = message.get("permission", "student")  # 获取用户权限

        # 保存用户信息到本地数据库
        self.db_manager.save_user(
            self.user_id,
            self.username,
            "",  # 不保存密码
            self.permission  # 保存权限
        )

        # 更新UI显示
        self.ui.userNameLabel.setText(f"当前用户: {self.username} ({self.permission})")
        self.display_message("系统", "注册成功！")

        # 设置WebSocket客户端
        self.websocket_client = self.login_dialog.websocket_client
        self.websocket_client.message_received.connect(self.handle_websocket_message)
        self.websocket_client.connection_changed.connect(self.handle_connection_change)

        # 初始化用户列表
        self.init_user_list()

        # 主动请求在线用户列表
        if self.websocket_client.is_connected():
            self.websocket_client.send_message_sync({
                "action": "get_online_users"
            })

    def load_local_contacts(self):
        """从本地数据库加载联系人"""
        if self.user_id is not None:
            # 加载联系人
            contacts = self.db_manager.get_contacts(self.user_id)
            for contact_id, contact_name in contacts:
                # 创建联系人项
                user_item = QtGui.QStandardItem(contact_name)
                # 设置项数据
                user_item.setData({
                    "username": contact_name,
                    "user_id": contact_id,
                    "permission": "unknown"
                }, QtCore.Qt.ItemDataRole.UserRole)
                # 添加到学生分组
                self.ui.studentsItem.appendRow(user_item)

            # 加载群组
            groups = self.db_manager.get_groups(self.user_id)
            seen = set()
            for group_id, group_name in groups:
                if group_id in seen:
                    continue
                # 创建群组项
                group_item = QtGui.QStandardItem(f"群: {group_name}")
                # 设置项数据
                group_item.setData(f"群:{group_id}", QtCore.Qt.ItemDataRole.UserRole)
                seen.add(group_id)
                # 添加到学生分组
                self.ui.studentsItem.appendRow(group_item)

            # 更新分组标题
            self.ui.teachersItem.setText(f"老师 ({self.ui.teachersItem.rowCount()})")
            self.ui.studentsItem.setText(f"学生和群组 ({self.ui.studentsItem.rowCount()})")
    def init_user_list(self):
        """初始化用户列表控件"""
        # 清除现有项但保留分组结构
        self.ui.teachersItem.removeRows(0, self.ui.teachersItem.rowCount())
        self.ui.studentsItem.removeRows(0, self.ui.studentsItem.rowCount())

        # 如果已登录，从数据库加载联系人和群组
        if self.user_id is not None:
            self.load_local_contacts()

    def update_user_list(self, users):
        """更新所有用户列表"""
        self.all_users = users

        # 清空现有项但保留分组
        self.ui.teachersItem.removeRows(0, self.ui.teachersItem.rowCount())
        self.ui.studentsItem.removeRows(0, self.ui.studentsItem.rowCount())

        # 添加在线用户
        for user in users:
            # 跳过无效用户和自己
            if not user.get("username") or not user.get("user_id"):
                continue
            if user.get("username") == self.username:
                continue

            # 创建用户项
            user_item = QtGui.QStandardItem(user["username"])
            user_item.setData({
                "username": user["username"],
                "user_id": user["user_id"],
                "permission": user.get("permission", "student")
            }, QtCore.Qt.ItemDataRole.UserRole)

            # 根据权限添加到不同分组
            if user.get("permission") == "teacher":
                self.ui.teachersItem.appendRow(user_item)
            else:
                self.ui.studentsItem.appendRow(user_item)

            # 保存到数据库
            self.db_manager.save_contact(self.user_id, user["user_id"], user["username"])

        # 更新分组标题
        self.ui.teachersItem.setText(f"老师 ({self.ui.teachersItem.rowCount()})")
        self.ui.studentsItem.setText(f"学生 ({self.ui.studentsItem.rowCount()})")

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

    def select_chat_target(self, index):
        """选择聊天对象（TreeView版本）"""
        if self.user_id is None:
            self.display_message("系统", "请先登录成功后再选择聊天对象")
            return

        item = self.ui.treeModel.itemFromIndex(index)
        # 检查是否选中的是分组项而非用户/群组项
        if not item or item is self.ui.teachersItem or item is self.ui.studentsItem:
            return

        user_data = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not user_data:
            return

        # 处理私聊或群聊选择
        if isinstance(user_data, dict):
            # 私聊情况
            self.current_chat = str(user_data["user_id"])
            self.current_chat_id = user_data["user_id"]
            self.current_chat_type = "private"
            self.ui.label.setText(f"私聊: {user_data['username']}")

            # 根据网络连接状态获取聊天历史
            if self.websocket_client.is_connected():
                self.request_private_history(user_data["user_id"])
            else:
                self.load_local_messages(user_data["user_id"], "private")
        elif isinstance(user_data, str) and user_data.startswith("群:"):
            # 群聊情况
            group_id = user_data[2:]
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

            # 根据网络连接状态获取聊天历史
            if self.websocket_client.is_connected():
                self.request_group_history(group_id)
            else:
                self.load_local_messages(group_id, "group")

        self.update_chat_display()  # 更新聊天显示

    def handle_file_received(self, filename, file_path, sender_id):
        """处理接收到的文件消息"""
        if self.current_chat_id and self.current_chat_type:
            timestamp = QtCore.QDateTime.currentDateTime().toString(QtCore.Qt.DateFormat.ISODate)

            # 获取发送者用户名
            sender_name = self.get_username_by_id(sender_id)

            file_msg = {
                "action": "file_received",
                "sender": sender_name,
                "content": filename,
                "timestamp": timestamp,
                "is_file": True,
                "file_path": file_path,
                "file_url": file_path,
                "sender_id": sender_id
            }

            # 添加到聊天历史
            if self.current_chat not in self.chat_history:
                self.chat_history[self.current_chat] = []
            self.chat_history[self.current_chat].append(file_msg)

            # 更新显示
            self.update_chat_display()

            # 保存到本地数据库
            self.db_manager.save_message(
                self.user_id,
                sender_id,
                sender_name,
                self.current_chat_id,
                self.current_chat_type,
                filename,
                timestamp,
                is_sent=0,
                is_file=True
            )

    def load_local_messages(self, receiver_id, receiver_type):
        """从本地数据库加载消息历史"""
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

    def handle_file_link_clicked(self, link):
        """处理文件链接点击事件，触发文件下载"""
        # 调用新的处理方法
        return self.handle_file_link_clicked(link.url())

        # 发送下载请求（旧逻辑，实际不会执行）
        message = {"action": "download_file", "filename": filename}
        self.websocket_client.send_message_sync(message)

        # 保存目标路径并显示下载状态
        self._pending_downloads[filename] = save_path
        self.update_chat_display(f"正在下载文件: {filename}", "system")

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

    def close_login_dialog(self):
        """安全关闭登录对话框"""
        if hasattr(self, 'login_dialog') and self.login_dialog:
            self.login_dialog.accept()
            # 标记已登录并显示主窗口
            self.logged_in = True
            self.show()

    def update_chat_display(self):
        """更新聊天显示区域，支持语音消息播放按钮"""
        if not self.current_chat or self.current_chat not in self.chat_history:
            return
        chat_content = ""
        for msg in self.chat_history[self.current_chat][::-1]:
            sender = msg.get("sender", "未知")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            is_file = msg.get("is_file", False)
            file_url = msg.get("file_url", "") or msg.get("file_path", "") if is_file else ""
            try:
                time_str = QtCore.QDateTime.fromString(timestamp[:19], QtCore.Qt.DateFormat.ISODate).toString("yyyy-MM-dd hh:mm:ss")
            except:
                time_str = timestamp[:19] if timestamp else ""
            if is_file:
                filename = os.path.basename(content)
                is_voice = filename.lower().endswith('.wav')
                if is_voice:
                    # 语音消息，生成播放链接
                    chat_content += f'<div style="text-align: left; margin: 5px;">'
                    chat_content += f'<span style="font-weight: bold; color: #333;">{sender}</span> '
                    chat_content += f'<span style="color: #888; font-size: small;">{time_str}</span><br>'
                    chat_content += f'<a href="voice://{file_url}" style="color: #007bff; text-decoration: underline;">▶️ 播放语音</a>'
                    chat_content += f' <span style="color:#888;font-size:small">({filename})</span>'
                    chat_content += '</div>'
                else:
                    # 其他文件
                    chat_content += f'<div style="text-align: left; margin: 5px;">'
                    chat_content += f'<span style="font-weight: bold; color: #333;">{sender}</span> '
                    chat_content += f'<span style="color: #888; font-size: small;">{time_str}</span><br>'
                    chat_content += f'<a href="file://{file_url}" style="color: #007bff; text-decoration: underline;">📎 {filename}</a>'
                    chat_content += '</div>'
            else:
                # 普通文本
                chat_content += f'<div style="text-align: left; margin: 5px;">'
                chat_content += f'<span style="font-weight: bold; color: #333;">{sender}</span> '
                chat_content += f'<span style="color: #888; font-size: small;">{time_str}</span><br>'
                chat_content += f'<span style="background-color: #f1f1f1; padding: 5px 10px; border-radius: 10px; display: inline-block;">{content}</span>'
                chat_content += '</div>'
        self.ui.shu_chu.setHtml(chat_content)
        self.ui.shu_chu.update()
        self.ui.shu_chu.repaint()
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 100)
        self.ui.shu_chu.verticalScrollBar().setValue(self.ui.shu_chu.verticalScrollBar().maximum())

    def handle_file_link_clicked(self, url):
        """处理文件/语音链接点击事件，支持语音自动下载并播放"""
        file_url = url.toString()
        if file_url.startswith("voice://"):
            # 语音消息
            local_path = file_url.replace("voice://", "")
            if os.path.exists(local_path):
                self.play_audio_file(local_path)
            else:
                # 本地无文件，自动下载
                filename = os.path.basename(local_path)
                save_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "temp_files", filename)
                self._pending_downloads[filename] = save_path
                if self.websocket_client.is_connected():
                    self.websocket_client.send_message_sync({"action": "download_file", "filename": filename})
                    self.display_message("系统", f"正在下载语音: {filename}")
                else:
                    self.display_message("系统", "离线无法下载语音")
        elif file_url.startswith("file://"):
            # 其他文件
            filename = os.path.basename(file_url)
            save_path, _ = QFileDialog.getSaveFileName(self, "保存文件", os.path.join(os.path.expanduser("~"), "Downloads", filename))
            if not save_path:
                return
            self._pending_downloads[filename] = save_path
            if self.websocket_client.is_connected():
                self.websocket_client.send_message_sync({"action": "download_file", "filename": filename})
                self.display_message("系统", f"正在下载文件: {filename}")
            else:
                self.display_message("系统", "离线无法下载文件")
        else:
            # 其他链接
            QDesktopServices.openUrl(url)

    def handle_websocket_message(self, message):
        """处理从WebSocket接收到的消息，支持语音下载完成后自动播放"""
        action = message.get("action")
        if action == "file_downloaded":
            filename = message.get("filename")
            temp_path = message.get("temp_path")
            if filename and temp_path and filename.lower().endswith('.wav'):
                self.display_message("系统", f"语音已下载: {filename}，正在播放...")
                self.play_audio_file(temp_path)
            else:
                self.display_message("系统", f"文件已下载: {filename}")
        elif action == "message_history":
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
                is_file = msg.get("content_type") == "file"
                file_url = msg.get("file_url", "") if is_file else ""

                # 转换消息格式
                converted_msg = {
                    "sender": "我" if sender_id == self.user_id else sender_name,
                    "content": content,
                    "timestamp": timestamp,
                    "is_group": receiver_type == "group",
                    "is_file": is_file,
                    "file_url": file_url
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

            # 检查是否是文件消息
            is_file = msg.get("content_type") == "file"
            file_url = msg.get("file_url", "") if is_file else ""

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
                "is_group": is_group,
                "is_file": is_file,  # 添加文件标志
                "file_url": file_url  # 添加文件路径
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
                is_sent=(sender_id == self.user_id),
                is_file=is_file  # 添加文件标记
            )

            # 添加到聊天历史
            self.chat_history[receiver].insert(0,converted_msg)

            # 更新显示
            if self.current_chat == receiver:
                self.update_chat_display()

        elif action == "group_list":
            # 更新群组列表
            groups = message.get("groups", [])
            self.update_group_list(groups)

        elif action == "login_response":
            if message.get("success"):
                self.user_id = message.get("user_id")
                self.username = message.get("username")
                permission = message.get("permission", "student")  # 获取权限
                self.permission = permission  # 保存权限到实例变量

                # 保存用户信息（包含权限）
                self.db_manager.save_user(
                    self.user_id,
                    self.username,
                    "",  # 不保存密码
                    permission  # 传递权限
                )

                # 更新UI显示
                self.ui.userNameLabel.setText(f"当前用户: {self.username} ({self.permission})")
                self.close_login_dialog()
                self.logged_in = True
            else:
                error_msg = message.get("message", "登录失败，请检查用户名和密码")
                QtWidgets.QMessageBox.warning(self.login_dialog, "登录错误", error_msg)

        elif action == "register_response":
            if message.get("success"):
                self.user_id = message.get("user_id")
                self.username = message.get("username")
                permission = message.get("permission", "student")  # 获取权限
                self.permission = permission  # 保存权限到实例变量

                # 保存用户信息（包含权限）
                self.db_manager.save_user(
                    self.user_id,
                    self.username,
                    "",  # 不保存密码
                    permission  # 传递权限
                )

                # 更新UI显示
                self.ui.userNameLabel.setText(f"当前用户: {self.username} ({permission})")
                self.close_login_dialog()
            else:
                error_msg = message.get("message", "注册失败，请稍后重试")
                QtWidgets.QMessageBox.warning(self.login_dialog, "注册错误", error_msg)
        elif action == "error":
            # 错误处理
            error_msg = message.get("message", "未知错误")

            # 如果用户尚未登录，显示弹窗
            if not self.logged_in and hasattr(self, 'login_dialog') and self.login_dialog.isVisible():
                QtWidgets.QMessageBox.warning(self.login_dialog, "错误", error_msg)
            else:
                self.display_message("系统", f"错误: {error_msg}")

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



        elif action == "all_users":
            # 所有用户列表
            users = message.get("users", [])
            self.update_user_list(users)


        elif action == "file_received":
            filename = message.get("filename")
            file_path = message.get("file_path")
            sender_id = message.get("sender_id")
            self.handle_file_received(filename, file_path, sender_id)
        elif action == "file_download_completed":
            # 处理文件下载完成逻辑
            filename = message.get("filename")
            file_data = message.get("file_data")

            # 如果文件记录不存在或没有文件数据，直接返回
            if filename not in self._pending_downloads or not file_data:
                return

            # 获取用户指定的保存路径
            save_path = self._pending_downloads.pop(filename)

            try:
                # 解码base64文件数据并保存
                import base64
                try:
                    file_data_bytes = base64.b64decode(file_data)
                    with open(save_path, "wb") as f:
                        f.write(file_data_bytes)
                except base64.binascii.Error:
                    self.display_message("系统", "文件数据解码失败: 无效的Base64格式")
                    return
                except Exception as e:
                    self.display_message("系统", f"文件保存失败: {str(e)}")
                    return

                self.display_message("系统", f"文件下载完成: {save_path}")
                # 打开文件所在目录
                QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(os.path.dirname(save_path)))
            except Exception as e:
                self.display_message("系统", f"文件保存失败: {str(e)}")

        elif action == "file_error":
            filename = message.get("filename")
            error = message.get("error")
            self.display_message("系统", f"文件 {filename} 保存失败: {error}")
            # 确保从_pending_downloads中移除失败的下载记录
            if filename in self._pending_downloads:
                self._pending_downloads.pop(filename)

    def handle_file_link_clicked(self, url):
        """处理文件链接点击事件，触发文件下载"""
        file_url = url.toString()
        filename = os.path.basename(file_url)

        # 检查是否已在下载中
        if filename in self._pending_downloads:
            self.display_message("系统", f"文件 {filename} 正在下载中，请不要重复点击")
            return

        # 询问用户保存路径
        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件",
            os.path.join(os.path.expanduser("~"), "Downloads", filename)
        )

        if not save_path:
            # 用户取消了保存对话框
            return

        # 记录待下载文件信息
        self._pending_downloads[filename] = save_path

        # 发送文件下载请求
        if self.websocket_client.is_connected():
            message = {
                "action": "download_file",
                "filename": filename,
                "sender_id": self.user_id,
                "receiver_id": self.current_chat_id,
                "receiver_type": self.current_chat_type
            }
            self.websocket_client.send_message_sync(message)
            self.display_message("系统", f"开始下载文件: {filename}")
        else:
            self.display_message("系统", "离线状态无法下载文件")

    def handle_connection_change(self, connected):
        """处理WebSocket连接状态变化"""
        if connected:
            # 连接成功提示
            self.display_message("系统", "已连接到聊天服务器")
        else:
            # 连接断开提示
            self.display_message("系统", "与聊天服务器的连接已断开")

    def display_message(self, sender, content):
        """在聊天区域显示系统消息"""
        # 获取当前文本并添加新消息
        current_text = self.ui.shu_chu.toHtml()
        new_text = f"{current_text}<br>{sender}: {content}"
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
        # 创建并显示昵称设置窗口
        self.nicheng_window = ChangeNicknameWindow()
        self.nicheng_window.show()

        # 连接昵称更改信号
        if hasattr(self.nicheng_window, 'nickname_changed'):
            self.nicheng_window.nickname_changed.connect(self.update_nickname)

    def update_nickname(self, new_nickname):
        """更新用户昵称"""
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
        self.ui.userNameLabel.setText(f"当前用户: {new_nickname} ({self.permission})")

    def open_jianqun_window(self):
        """打开建群窗口"""
        user_data = []
        if not self.websocket_client.is_connected():
            # 离线模式从数据库获取
            contacts = self.db_manager.get_contacts(self.user_id) if self.user_id else []
            for contact_id, contact_name in contacts:
                # 尝试从本地获取用户权限
                permission = self.db_manager.get_user_permission(contact_id) or "student"
                user_data.append({
                    "username": contact_name,
                    "permission": permission
                })
        else:
            # 在线模式使用所有用户列表
            for user in self.all_users:
                if "username" in user and user["username"] != self.username:
                    user_data.append({
                        "username": user["username"],
                        "permission": user.get("permission", "student").lower()  # 确保小写
                    })

        # 创建并显示建群窗口
        self.jianqun_window = CreateGroupWindow(user_data)
        self.jianqun_window.show()

        # 连接建群信号
        self.jianqun_window.group_created.connect(self.create_group)

    def create_group(self, group_name, members):
        """创建新群组"""
        # 将用户名列表转换为用户ID列表
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
                "receiver_id": receiver_id,
                "receiver_type": self.current_chat_type
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

    def play_audio_file(self, file_path):
        """播放本地wav语音文件"""
        try:
            data, samplerate = sf.read(file_path, dtype='float32')
            sd.play(data, samplerate)
            sd.wait()
            self.display_message("系统", f"语音播放完成: {os.path.basename(file_path)}")
        except Exception as e:
            self.display_message("系统", f"语音播放失败: {e}")