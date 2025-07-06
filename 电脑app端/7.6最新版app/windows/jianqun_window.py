from PyQt6 import QtWidgets, QtCore, QtGui


class CreateGroupWindow(QtWidgets.QDialog):
    group_created = QtCore.pyqtSignal(str, list)  # 信号：群名和成员列表

    def __init__(self, usernames, parent=None):
        super().__init__(parent)
        self.setWindowTitle("创建群组")
        self.setFixedSize(400, 500)
        # 设置窗口背景色
        self.setStyleSheet("background-color: white;")

        # 群名输入框 - 绝对定位
        self.group_name_edit = QtWidgets.QLineEdit(self)
        self.group_name_edit.setGeometry(10, 10, 380, 30)  # x, y, width, height
        self.group_name_edit.setPlaceholderText("输入群组名称...")
        self.group_name_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #eee;
                border-radius: 4px;
                padding: 5px;
                font-size: 14px;
            }
        """)

        # 使用TreeView展示成员列表 - 绝对定位
        self.members_tree = QtWidgets.QTreeView(self)
        self.members_tree.setGeometry(10, 50, 380, 380)  # x, y, width, height
        self.members_tree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)

        # 关键新增关键修改：隐藏索引列和表头
        self.members_tree.setHeaderHidden(True)  # 隐藏表头
        self.members_tree.setRootIsDecorated(False)  # 隐藏根节点装饰（去掉数字）

        # 创建模型
        self.tree_model = QtGui.QStandardItemModel()
        self.members_tree.setModel(self.tree_model)

        # 添加分组
        self.teachers_item = QtGui.QStandardItem("老师 (0)")
        self.students_item = QtGui.QStandardItem("学生 (0)")
        self.tree_model.appendRow(self.teachers_item)
        self.tree_model.appendRow(self.students_item)

        # 添加用户到分组
        teacher_count = 0
        student_count = 0

        # 在 __init__ 方法中修改用户分组部分
        for user in usernames:
            # 确保 user 是字典类型且包含 permission 字段
            if isinstance(user, dict):
                username = user.get("username", "")
                permission = user.get("permission", "").lower()  # 转换为小写确保匹配
            else:
                # 如果传入的是纯字符串用户名，默认为学生
                username = str(user)
                permission = "student"

            if not username:
                continue

            item = QtGui.QStandardItem(username)

            # 严格根据 permission 值判断
            if permission == "teacher":
                self.teachers_item.appendRow(item)
                teacher_count += 1
            else:
                # 其他所有情况都归为学生
                self.students_item.appendRow(item)
                student_count += 1

        # 更新分组标题计数
        self.teachers_item.setText(f"老师 ({teacher_count})")
        self.students_item.setText(f"学生 ({student_count})")

        # 展开所有分组
        self.members_tree.expandAll()

        # 设置TreeView样式
        self.members_tree.setStyleSheet("""
            QTreeView {
                background-color: transparent;
                border: none;
                font-size: 14px;
                show-decoration-selected: 0;
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
            /* 隐藏分支图标和线条 */
            QTreeView::branch {
                background-color: transparent;
                border-image: none;
            }
        """)

        # 创建按钮 - 绝对定位
        self.create_button = QtWidgets.QPushButton("创建", self)
        self.create_button.setGeometry(220, 430, 120, 45) # x, y, width, height
        self.create_button.clicked.connect(self.create_group)

        # 取消按钮 - 绝对定位
        self.cancel_button = QtWidgets.QPushButton("取消", self)
        self.cancel_button.setGeometry(60, 430, 120, 45) # x, y, width, height
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
        self.create_button.setStyleSheet(button_style)
        self.cancel_button.setStyleSheet(button_style)

    def create_group(self):
        group_name = self.group_name_edit.text().strip()
        if not group_name:
            QtWidgets.QMessageBox.warning(self, "警告", "群组名称不能为空")
            return

        if len(group_name) < 3 or len(group_name) > 20:
            QtWidgets.QMessageBox.warning(self, "警告", "群组名称长度应在3-20个字符之间")
            return

        # 获取选中的成员
        selected_indexes = self.members_tree.selectedIndexes()
        members = []

        for index in selected_indexes:
            item = self.tree_model.itemFromIndex(index)
            # 只添加用户项，跳过分组项
            if item not in (self.teachers_item, self.students_item):
                members.append(item.text())

        if not members:
            QtWidgets.QMessageBox.warning(self, "警告", "请选择至少一个群成员")
            return

        # 发射信号
        self.group_created.emit(group_name, members)
        self.close()
