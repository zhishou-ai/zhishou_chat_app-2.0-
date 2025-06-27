from PyQt6 import QtWidgets, QtCore

class CreateGroupWindow(QtWidgets.QDialog):
    group_created = QtCore.pyqtSignal(str, list)  # 信号：群名和成员列表
    
    def __init__(self, usernames, parent=None):
        super().__init__(parent)
        self.setWindowTitle("创建群组")
        self.setFixedSize(400, 500)
        
        layout = QtWidgets.QVBoxLayout()
        
        # 群名输入框
        self.group_name_edit = QtWidgets.QLineEdit()
        self.group_name_edit.setPlaceholderText("输入群组名称...")
        layout.addWidget(self.group_name_edit)
        
        # 联系人列表
        self.members_list = QtWidgets.QListWidget()
        self.members_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        for username in usernames:
            item = QtWidgets.QListWidgetItem(username)
            self.members_list.addItem(item)
        layout.addWidget(self.members_list)
        
        # 按钮区域
        button_layout = QtWidgets.QHBoxLayout()
        create_button = QtWidgets.QPushButton("创建")
        create_button.clicked.connect(self.create_group)
        button_layout.addWidget(create_button)
        
        cancel_button = QtWidgets.QPushButton("取消")
        cancel_button.clicked.connect(self.close)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_group(self):
        group_name = self.group_name_edit.text().strip()
        if not group_name:
            QtWidgets.QMessageBox.warning(self, "警告", "群组名称不能为空")
            return
            
        if len(group_name) < 3 or len(group_name) > 20:
            QtWidgets.QMessageBox.warning(self, "警告", "群组名称长度应在3-20个字符之间")
            return
            
        # 获取选中的成员
        selected_items = self.members_list.selectedItems()
        members = [item.text() for item in selected_items]
        
        if not members:
            QtWidgets.QMessageBox.warning(self, "警告", "请选择至少一个群成员")
            return
            
        # 发射信号
        self.group_created.emit(group_name, members)
        self.close()