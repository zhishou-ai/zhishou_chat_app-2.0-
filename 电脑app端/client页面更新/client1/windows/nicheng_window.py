from PyQt6 import QtWidgets, QtCore

class ChangeNicknameWindow(QtWidgets.QDialog):
    nickname_changed = QtCore.pyqtSignal(str)  # 信号：新昵称
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("修改昵称")
        self.setFixedSize(300, 150)
        
        layout = QtWidgets.QVBoxLayout()
        
        # 昵称输入框
        self.nickname_edit = QtWidgets.QLineEdit()
        self.nickname_edit.setPlaceholderText("输入新昵称...")
        layout.addWidget(self.nickname_edit)
        
        # 按钮区域
        button_layout = QtWidgets.QHBoxLayout()
        save_button = QtWidgets.QPushButton("保存")
        save_button.clicked.connect(self.save_nickname)
        button_layout.addWidget(save_button)
        
        cancel_button = QtWidgets.QPushButton("取消")
        cancel_button.clicked.connect(self.close)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def save_nickname(self):
        new_nickname = self.nickname_edit.text().strip()
        if not new_nickname:
            QtWidgets.QMessageBox.warning(self, "警告", "昵称不能为空")
            return
            
        if len(new_nickname) < 3 or len(new_nickname) > 20:
            QtWidgets.QMessageBox.warning(self, "警告", "昵称长度应在3-20个字符之间")
            return
            
        # 发射信号
        self.nickname_changed.emit(new_nickname)
        self.close()