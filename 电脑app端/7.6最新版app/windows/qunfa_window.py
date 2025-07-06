from PyQt6 import QtCore, QtGui, QtWidgets


class QunfaWindow(QtWidgets.QDialog):
    message_to_send = QtCore.pyqtSignal(str, list)  # 信号：消息内容和接收者列表

    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("群发消息")
        self.setFixedSize(400, 500)
        # 设置窗口背景色
        self.setStyleSheet("background-color: white;")

        # 联系人TreeView - 绝对定位
        self.contacts_tree = QtWidgets.QTreeView(self)
        self.contacts_tree.setGeometry(10, 10, 380, 300)  # x, y, width, height
        self.contacts_tree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)

        # 隐藏TreeView的索引列（解决数字"1"显示问题）
        self.contacts_tree.setHeaderHidden(True)  # 隐藏表头
        self.contacts_tree.setRootIsDecorated(False)  # 隐藏根节点装饰

        # 重要：设置样式时添加索引列隐藏规则
        self.contacts_tree.setStyleSheet("""
            QTreeView {
                background-color: transparent;
                border: 1px solid #eee;
                font-size: 14px;
                show-decoration-selected: 0;
                border-radius: 4px;
            }
            QTreeView::item {
                height: 30px;
                padding: 5px;
                color: black;
                background-color: transparent;
            }
            QTreeView::item:hover {
                background-color: rgba(0,0,0,0.1);
            }
            QTreeView::item:selected {
                background-color: #07C160;
                color: white;
            }
            /* 隐藏索引列（解决数字"1"显示问题）*/
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                border-image: none;
                image: none;
            }
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                border-image: none;
                image: none;
            }
        """)

        # 创建标准项模型
        self.tree_model = QtGui.QStandardItemModel()
        self.contacts_tree.setModel(self.tree_model)

        # 添加分组
        self.teachers_item = QtGui.QStandardItem("老师 (0)")
        self.students_item = QtGui.QStandardItem("学生 (0)")
        self.tree_model.appendRow(self.teachers_item)
        self.tree_model.appendRow(self.students_item)

        # 添加用户到对应分组
        teacher_count = 0
        student_count = 0

        for user in user_data:
            username = user.get("username", "")
            permission = user.get("permission", "student")

            if not username:
                continue

            item = QtGui.QStandardItem(username)

            # 根据权限添加到不同分组
            if permission == "teacher":
                self.teachers_item.appendRow(item)
                teacher_count += 1
            else:
                self.students_item.appendRow(item)
                student_count += 1

        # 更新分组标题计数
        self.teachers_item.setText(f"老师 ({teacher_count})")
        self.students_item.setText(f"学生 ({student_count})")

        # 展开所有分组
        self.contacts_tree.expandAll()

        # 消息输入框 - 绝对定位
        self.message_edit = QtWidgets.QTextEdit(self)
        self.message_edit.setGeometry(10, 320, 380, 100)  # x, y, width, height
        self.message_edit.setPlaceholderText("输入群发消息内容...")
        self.message_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #eee;
                border-radius: 4px;
                padding: 5px;
                font-size: 14px;
            }
        """)

        # 发送按钮 - 绝对定位
        self.send_button = QtWidgets.QPushButton("发送", self)
        self.send_button.setGeometry(220, 430, 120, 45)  # x, y, width, height
        self.send_button.clicked.connect(self.send_message)

        # 取消按钮 - 绝对定位
        self.cancel_button = QtWidgets.QPushButton("取消", self)
        self.cancel_button.setGeometry(60, 430, 120, 45)  # x, y, width, height
        self.cancel_button.clicked.connect(self.close)

        # 设置按钮样式
        button_style = """
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
        """
        self.send_button.setStyleSheet(button_style)
        self.cancel_button.setStyleSheet(button_style)

    def send_message(self):
        # 获取选中的联系人
        selected_indexes = self.contacts_tree.selectedIndexes()
        recipients = []

        for index in selected_indexes:
            item = self.tree_model.itemFromIndex(index)
            # 只添加用户项，跳过分组项
            if item not in (self.teachers_item, self.students_item):
                recipients.append(item.text())

        # 获取消息内容
        message_content = self.message_edit.toPlainText().strip()

        if not recipients:
            QtWidgets.QMessageBox.warning(self, "警告", "请选择至少一个接收者")
            return

        if not message_content:
            QtWidgets.QMessageBox.warning(self, "警告", "消息内容不能为空")
            return

        # 发射信号
        self.message_to_send.emit(message_content, recipients)
        self.close()