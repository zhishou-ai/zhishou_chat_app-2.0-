from PyQt6 import QtCore, QtGui, QtWidgets

class QunfaWindow(QtWidgets.QDialog):
    message_to_send = QtCore.pyqtSignal(str, list)  # 信号：消息内容和接收者列表

    def __init__(self, usernames, parent=None):
        super().__init__(parent)
        self.setWindowTitle("创建新群聊")
        self.setFixedSize(400, 500)
        
        # Main color theme (RGB: 7, 193, 96)
        self.main_color = "rgb(7, 193, 96)"
        self.main_color_hover = "rgb(6, 173, 86)"
        
        # Main layout
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header banner
        header = QtWidgets.QLabel("创建新群聊")
        header.setStyleSheet(f"""
            QLabel {{
                background-color: {self.main_color};
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }}
        """)
        header.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Group name section
        group_name_layout = QtWidgets.QVBoxLayout()
        group_name_label = QtWidgets.QLabel("群名称：")
        group_name_label.setStyleSheet("font-weight: bold;")
        group_name_layout.addWidget(group_name_label)
        
        self.group_name_edit = QtWidgets.QLineEdit()
        self.group_name_edit.setPlaceholderText("输入群名称")
        self.group_name_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        group_name_layout.addWidget(self.group_name_edit)
        layout.addLayout(group_name_layout)

        # Members selection section
        members_label = QtWidgets.QLabel("选择成员：")
        members_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(members_label)

        # Scroll area for member list
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QScrollArea > QWidget > QWidget {
                background-color: white;
            }
        """)
        
        # Container for checkboxes
        members_container = QtWidgets.QWidget()
        members_layout = QtWidgets.QVBoxLayout(members_container)
        members_layout.setSpacing(10)
        
        # Create checkboxes for each member
        self.member_checkboxes = []
        for username in usernames:
            checkbox = QtWidgets.QCheckBox(username)
            checkbox.setStyleSheet("""
                QCheckBox {
                    padding: 5px;
                    background-color: white;
                }
            """)
            members_layout.addWidget(checkbox)
            self.member_checkboxes.append(checkbox)
        
        scroll_area.setWidget(members_container)
        layout.addWidget(scroll_area)

        # Buttons at bottom - now with equal size
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        # Set fixed size for both buttons
        button_size = QtCore.QSize(100, 40)  # Width: 100, Height: 40
        
        cancel_button = QtWidgets.QPushButton("取消")
        cancel_button.setFixedSize(button_size)
        cancel_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        cancel_button.clicked.connect(self.close)
        button_layout.addWidget(cancel_button)
        
        create_button = QtWidgets.QPushButton("发送")
        create_button.setFixedSize(button_size)
        create_button.setStyleSheet(f"""
            QPushButton {{
                padding: 8px 16px;
                background-color: {self.main_color};
                color: white;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.main_color_hover};
            }}
        """)
        create_button.clicked.connect(self.create_group)
        button_layout.addWidget(create_button)
        
        layout.addLayout(button_layout)
        
        # Set main window background
        self.setStyleSheet(f"""
            QDialog {{
                background-color: white;
            }}
        """)
        
        self.setLayout(layout)

    def create_group(self):
        # Get selected members
        selected_members = []
        for checkbox in self.member_checkboxes:
            if checkbox.isChecked():
                selected_members.append(checkbox.text())
        
        # Get group name
        group_name = self.group_name_edit.text().strip()

        if not group_name:
            QtWidgets.QMessageBox.warning(self, "警告", "请输入群名称")
            return
            
        if not selected_members:
            QtWidgets.QMessageBox.warning(self, "警告", "请选择至少一个成员")
            return

        # Emit signal with group name and members
        self.message_to_send.emit(group_name, selected_members)
        self.close()