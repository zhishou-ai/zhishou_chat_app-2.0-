from PyQt6 import QtCore, QtGui, QtWidgets


class MessageBubble(QtWidgets.QWidget):
    """自定义聊天气泡控件"""

    def __init__(self, sender, content, timestamp, is_me, parent=None):
        super().__init__(parent)
        self.is_me = is_me
        self.setup_ui(sender, content, timestamp)

    def setup_ui(self, sender, content, timestamp):
        # 主布局
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)

        # 水平布局
        h_layout = QtWidgets.QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)

        # 气泡
        bubble = QtWidgets.QFrame()
        bubble.setStyleSheet(f"""
            QFrame {{
                background-color: {'#95EC69' if self.is_me else 'white'};
                border-radius: 8px;
                padding: 8px 12px;
                {'margin-right: 15px;' if self.is_me else 'margin-left: 15px;'}
                max-width: 300px;
            }}
        """)

        # 气泡内容
        bubble_layout = QtWidgets.QVBoxLayout(bubble)
        if not self.is_me:
            lbl_sender = QtWidgets.QLabel(sender)
            lbl_sender.setStyleSheet("color: #576B95; font-weight: 500; font-size: 13px;")
            bubble_layout.addWidget(lbl_sender)

        lbl_content = QtWidgets.QLabel(content)
        lbl_content.setWordWrap(True)
        bubble_layout.addWidget(lbl_content)

        lbl_time = QtWidgets.QLabel(timestamp[-8:-3])  # 显示HH:MM
        lbl_time.setStyleSheet("color: #999999; font-size: 11px;")
        bubble_layout.addWidget(lbl_time, alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        # 添加到布局
        if self.is_me:
            h_layout.addStretch()
            h_layout.addWidget(bubble)
        else:
            h_layout.addWidget(bubble)
            h_layout.addStretch()

        layout.addLayout(h_layout)
        self.setLayout(layout)


class Ui_zhi_liao(object):
    def setupUi(self, zhi_liao):
        zhi_liao.setObjectName("zhi_liao")
        zhi_liao.resize(1100, 710)

        # 背景
        zhi_liao.setStyleSheet("background-color: #F5F5F5;")

        # 聊天输出区域
        self.shu_chu = QtWidgets.QTextBrowser(parent=zhi_liao)
        self.shu_chu.setGeometry(QtCore.QRect(330, 50, 700, 471))
        self.shu_chu.setStyleSheet("QTextBrowser {\n"
                                   "    background-color: rgba(0, 0, 0, 0);\n"
                                   "    color: black;\n"
                                   "    border-radius: 10px;\n"
                                   "    padding: 20px;\n"
                                   "    border: none;\n"
                                   "}\n")
        self.shu_chu.setObjectName("shu_chu")

        # 群发按钮
        self.pushButton_5 = QtWidgets.QPushButton(parent=zhi_liao)
        self.pushButton_5.setGeometry(QtCore.QRect(360, 545, 35, 35))
        self.pushButton_5.setStyleSheet("""
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
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            QPushButton:pressed {
                background-color: #05984D;
                margin: 6px;
                padding: 0px;
                font-size: 13.5px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                transform: translateY(1px);
            }
        """)
        self.pushButton_5.setObjectName("pushButton_5")

        # 语音按钮
        self.yuyin = QtWidgets.QPushButton(parent=zhi_liao)
        self.yuyin.setGeometry(QtCore.QRect(400, 545, 35, 35))
        self.yuyin.setStyleSheet("""
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
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            QPushButton:pressed {
                background-color: #05984D;
                margin: 6px;
                padding: 0px;
                font-size: 13.5px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                transform: translateY(1px);
            }
        """)
        self.yuyin.setObjectName("yuyin")

        # 文件按钮
        self.pushButton = QtWidgets.QPushButton(parent=zhi_liao)
        self.pushButton.setGeometry(QtCore.QRect(320, 545, 35, 35))
        self.pushButton.setStyleSheet("""
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
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            QPushButton:pressed {
                background-color: #05984D;
                margin: 6px;
                padding: 0px;
                font-size: 13.5px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                transform: translateY(1px);
            }
        """)
        self.pushButton.setObjectName("pushButton")

        # 水平装饰性边框 (顶部)
        self.decorative_border = QtWidgets.QFrame(parent=zhi_liao)
        self.decorative_border.setGeometry(QtCore.QRect(300, 60, 800, 1))
        self.decorative_border.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.15);
                min-height: 0.5px;
                max-height: 0.5px;
                border: none;
                margin: 0;
                padding: 0;
            }
        """)

        # 水平装饰性边框 (输入框上方)
        self.textEdit_border = QtWidgets.QFrame(parent=zhi_liao)
        self.textEdit_border.setGeometry(QtCore.QRect(300, 550, 800, 1))
        self.textEdit_border.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.15);
                min-height: 0.5px;
                max-height: 0.5px;
                border: none;
                margin: 0;
                padding: 0;
            }
        """)

        # 垂直装饰性边框
        self.vertical_border = QtWidgets.QFrame(parent=zhi_liao)
        self.vertical_border.setGeometry(QtCore.QRect(300, 50, 1, 620))
        self.vertical_border.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.1);
                min-width: 0.5px;
                max-width: 0.5px;
                border: none;
                margin: 0;
                padding: 0;
            }
        """)

        # 文本输入框
        self.textEdit = QtWidgets.QTextEdit(parent=zhi_liao)
        self.textEdit.setGeometry(QtCore.QRect(300, 580, 800, 140))
        self.textEdit.setStyleSheet("""
            QTextEdit {
                background-color: white;
                color: black;
                border-left: none;
                border-right: none;
                border-bottom: none;
                border-radius: 0;
                padding: 20px;
      
                font-size: 15px;
                
            }
        """)
        self.textEdit.setObjectName("textEdit")

        # 发送按钮
        self.pushButton_2 = QtWidgets.QPushButton(parent=zhi_liao)
        self.pushButton_2.setGeometry(QtCore.QRect(990, 645, 100, 55))
        self.pushButton_2.setStyleSheet("""
            QPushButton {
                background-color: #07C160;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                border-radius: 6px;
                margin: 5px;
                font-size: 14px;
                font-family: "Microsoft YaHei";
                min-width: 60px;
                min-height: 30px;
                transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            }
            QPushButton:hover {
                background-color: #06AD56;
                margin: 3px;
                padding: 10px 18px;
                font-size: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            QPushButton:pressed {
                background-color: #05984D;
                margin: 6px;
                padding: 7px 15px;
                font-size: 13.5px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                transform: translateY(1px);
            }
        """)
        self.pushButton_2.setObjectName("pushButton_2")

        # 当前用户名称标签
        self.userNameLabel = QtWidgets.QLabel(parent=zhi_liao)
        self.userNameLabel.setGeometry(QtCore.QRect(0, 0, 300, 60))
        self.userNameLabel.setStyleSheet("""
            QLabel {
                font-family: "黑体";
                font-size: 16px;
                font-weight: 300;
                color: white;
                padding-left: 50px;
                padding-top: 0px;
                padding-bottom: 0px;
                background-color: #07C160;
                border: none;
                margin: 0px;
                qproperty-alignment: 'AlignVCenter | AlignLeft';
            }
        """)
        self.userNameLabel.setObjectName("userNameLabel")

        # 头像
        self.avatarLabel = QtWidgets.QLabel(parent=zhi_liao)
        self.avatarLabel.setGeometry(QtCore.QRect(5, 10, 40, 40))
        self.avatarLabel.setStyleSheet("""
            QLabel {
                background-color: white;
                border-radius: 20px;
                min-width: 40px;
                max-width: 40px;
                min-height: 40px;
                max-height: 40px;
            }
        """)
        self.avatarLabel.setObjectName("avatarLabel")

        # 私聊按钮
        self.privateChatBtn = QtWidgets.QRadioButton(parent=zhi_liao)
        self.privateChatBtn.setGeometry(QtCore.QRect(0, 60, 150, 60))
        self.privateChatBtn.setStyleSheet("""
            QRadioButton {
                background-color: #F5F5F5;
                border: none;
                color: black;
                font-size: 14px;
                border-radius: 0;
                padding-left: 20px;
            }
            QRadioButton::indicator {
                width: 0px;
                height: 0px;
            }
            QRadioButton:checked {
                color: #07C160;
                border-bottom: 3px solid #07C160;
            }
        """)
        self.privateChatBtn.setObjectName("privateChatBtn")
        self.privateChatBtn.setChecked(True)

        # 群聊按钮
        self.groupChatBtn = QtWidgets.QRadioButton(parent=zhi_liao)
        self.groupChatBtn.setGeometry(QtCore.QRect(150, 60, 150, 60))
        self.groupChatBtn.setStyleSheet("""
            QRadioButton {
                background-color: #F5F5F5;
                border: none;
                color: black;
                font-size: 14px;
                border-radius: 0;
                padding-left: 20px;
            }
            QRadioButton::indicator {
                width: 0px;
                height: 0px;
            }
            QRadioButton:checked {
                color: #07C160;
                border-bottom: 3px solid #07C160;
            }
        """)
        self.groupChatBtn.setObjectName("groupChatBtn")

        # 用户列表控件 (改为TreeView)
        self.treeView = QtWidgets.QTreeView(parent=zhi_liao)
        self.treeView.setGeometry(QtCore.QRect(0, 120, 300, 591))
        self.treeView.setStyleSheet("""
            QTreeView {
                background-color: transparent;
                border: none;
                font-size: 14px;
                show-decoration-selected: 0; /* 隐藏选中装饰 */
            }
            QTreeView::item {
                height: 40px;
                padding: 5px;
                color: black; /* 默认文字颜色 */
                background-color: transparent; /* 默认背景透明 */
            }
            QTreeView::item:hover {
                background-color: rgba(0,0,0,0.1); /* 悬停效果 */
            }
            QTreeView::item:pressed {
                background-color: #07C160; /* 点击效果 */
                color: white; /* 点击时文字颜色 */
            }
            /* 移除选中状态的虚线框 */
            QTreeView::item:focus {
                outline: none;
            }
        """)
        self.treeView.setHeaderHidden(True)
        self.treeView.setObjectName("treeView")

        # 创建标准项模型
        self.treeModel = QtGui.QStandardItemModel()
        self.treeView.setModel(self.treeModel)

        # 添加老师和学生分组
        self.teachersItem = QtGui.QStandardItem("老师 (0)")
        self.studentsItem = QtGui.QStandardItem("学生 (0)")
        self.treeModel.appendRow(self.teachersItem)
        self.treeModel.appendRow(self.studentsItem)

        # 展开分组
        self.treeView.expandAll()

        # 建群按钮
        self.pushButton_3 = QtWidgets.QPushButton(parent=zhi_liao)
        self.pushButton_3.setGeometry(QtCore.QRect(1010, 10, 50, 45))
        self.pushButton_3.setStyleSheet("""
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
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            QPushButton:pressed {
                background-color: #05984D;
                margin: 6px;
                padding: 0px;
                font-size: 13.5px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                transform: translateY(1px);
            }
        """)
        self.pushButton_3.setObjectName("pushButton_3")

        # 标签
        self.label = QtWidgets.QLabel(parent=zhi_liao)
        self.label.setGeometry(QtCore.QRect(350, 10, 131, 41))
        self.label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                padding: 3px 20px 3px 20px;
                color: black;
            }
        """)
        self.label.setObjectName("label")

        self.retranslateUi(zhi_liao)
        QtCore.QMetaObject.connectSlotsByName(zhi_liao)

    def retranslateUi(self, zhi_liao):
        _translate = QtCore.QCoreApplication.translate
        zhi_liao.setWindowTitle(_translate("zhi_liao", "知了聊天"))
        self.pushButton.setText(_translate("zhi_liao", "文件"))
        self.pushButton_2.setText(_translate("zhi_liao", "发送"))
        self.userNameLabel.setText(_translate("zhi_liao", "未登录"))
        self.privateChatBtn.setText(_translate("zhi_liao", "私聊"))
        self.groupChatBtn.setText(_translate("zhi_liao", "群聊"))
        self.pushButton_3.setText(_translate("zhi_liao", "建群"))
        self.pushButton_5.setText(_translate("zhi_liao", "群发"))
        self.yuyin.setText(_translate("zhi_liao", "语音"))
        self.label.setText(_translate("zhi_liao", "群聊、好友名"))

        # 创建按钮组
        self.chatModeGroup = QtWidgets.QButtonGroup(zhi_liao)
        self.chatModeGroup.addButton(self.privateChatBtn)
        self.chatModeGroup.addButton(self.groupChatBtn)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, username="未登录", role="student"):
        super().__init__()
        self.ui = Ui_zhi_liao()
        self.ui.setupUi(self)

        # 修改：将QTextBrowser改为QListWidget
        self.ui.shu_chu = QtWidgets.QListWidget(self)
        self.ui.shu_chu.setGeometry(QtCore.QRect(330, 50, 700, 471))
        self.ui.shu_chu.setStyleSheet("""
            QListWidget {
                background-color: #F0F0F0;
                border: none;
                padding: 0;
            }
            QListWidget::item {
                border: none;
                padding: 0;
                margin: 0;
            }
        """)

        # 模拟聊天数据
        self.chat_history = [
            {"sender": "张三", "content": "你好，在吗？", "timestamp": "2023-01-01 10:00:00", "is_me": False},
            {"sender": "我", "content": "在的，有什么事吗？", "timestamp": "2023-01-01 10:01:00", "is_me": True},
        ]
        self.update_chat_display()

        # 更新用户标签显示
        role_text = "老师" if role == "teacher" else "学生"
        self.ui.userNameLabel.setText(f"{username}（{role_text}）")

    def update_chat_display(self):
        """使用QListWidget显示带气泡的消息"""
        self.ui.shu_chu.clear()

        # 按时间正序显示
        for msg in sorted(self.chat_history, key=lambda x: x["timestamp"]):
            item = QtWidgets.QListWidgetItem()
            self.ui.shu_chu.addItem(item)

            # 创建气泡控件
            bubble = MessageBubble(
                sender=msg["sender"],
                content=msg["content"],
                timestamp=msg["timestamp"],
                is_me=msg["is_me"]
            )

            # 设置item大小和控件
            item.setSizeHint(bubble.sizeHint())
            self.ui.shu_chu.setItemWidget(item, bubble)

        # 滚动到底部
        self.ui.shu_chu.scrollToBottom()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow("测试用户", "teacher")
    window.show()
    sys.exit(app.exec())