from PyQt6 import QtCore, QtGui, QtWidgets

class QunfaWindow(QtWidgets.QDialog):
    message_to_send = QtCore.pyqtSignal(str, list)  # 信号：消息内容和接收者列表
    
    def __init__(self, usernames, parent=None):
        super().__init__(parent)
        self.setWindowTitle("群发消息")
        self.setFixedSize(400, 500)
        
        layout = QtWidgets.QVBoxLayout()
        
        # 联系人列表
        self.contacts_list = QtWidgets.QListWidget()
        self.contacts_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        for username in usernames:
            item = QtWidgets.QListWidgetItem(username)
            self.contacts_list.addItem(item)
        layout.addWidget(self.contacts_list)
        
        # 消息输入框
        self.message_edit = QtWidgets.QTextEdit()
        self.message_edit.setPlaceholderText("输入群发消息内容...")
        layout.addWidget(self.message_edit)
        
        # 按钮区域
        button_layout = QtWidgets.QHBoxLayout()
        send_button = QtWidgets.QPushButton("发送")
        send_button.clicked.connect(self.send_message)
        button_layout.addWidget(send_button)
        
        cancel_button = QtWidgets.QPushButton("取消")
        cancel_button.clicked.connect(self.close)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def send_message(self):
        # 获取选中的联系人
        selected_items = self.contacts_list.selectedItems()
        recipients = [item.text() for item in selected_items]
        
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