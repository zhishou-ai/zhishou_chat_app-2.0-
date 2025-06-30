from PyQt6 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(413, 609)
        
        # Main color theme (RGB: 7, 193, 96)
        self.main_color = "rgb(7, 193, 96)"
        self.main_color_hover = "rgb(6, 173, 86)"
        
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        # Header banner
        self.dui_xian_shi = QtWidgets.QLabel(parent=self.centralwidget)
        self.dui_xian_shi.setGeometry(QtCore.QRect(0, 0, 411, 81))
        self.dui_xian_shi.setStyleSheet(f"""
            color: white;  
            font-family:"微软雅黑";
            background-color: {self.main_color};
            font-size: 20px;
            font-weight: bold;
            padding-left: 20px;
        """)
        self.dui_xian_shi.setObjectName("dui_xian_shi")
        
        # Group name label
        self.label = QtWidgets.QLabel(parent=self.centralwidget)
        self.label.setGeometry(QtCore.QRect(10, 100, 54, 16))
        self.label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.label.setObjectName("label")
        
        # Group name input
        self.wen_ben3 = QtWidgets.QTextEdit(parent=self.centralwidget)
        self.wen_ben3.setGeometry(QtCore.QRect(20, 130, 371, 31))
        self.wen_ben3.setStyleSheet("""
            background-color: rgb(255, 255, 255);  
            border: 1px solid #cccccc;  
            border-radius: 10px;         
            padding: 5px;               
            color: #666666;             
            font-size: 14px;            
        """)
        self.wen_ben3.setObjectName("wen_ben3")
        
        # Members selection label
        self.label_2 = QtWidgets.QLabel(parent=self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(10, 180, 71, 31))
        self.label_2.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.label_2.setObjectName("label_2")
        
        # Decorative area at bottom
        self.zhuang_shi = QtWidgets.QLabel(parent=self.centralwidget)
        self.zhuang_shi.setGeometry(QtCore.QRect(0, 470, 411, 91))
        self.zhuang_shi.setStyleSheet("background-color: rgb(244, 246, 244);")
        self.zhuang_shi.setText("")
        self.zhuang_shi.setObjectName("zhuang_shi")
        
        # 按钮容器 - 用于更好的布局控制
        self.button_container = QtWidgets.QWidget(parent=self.centralwidget)
        self.button_container.setGeometry(QtCore.QRect(0, 470, 411, 91))
        self.button_container.setObjectName("button_container")
        
        # 创建按钮布局
        button_layout = QtWidgets.QHBoxLayout(self.button_container)
        button_layout.setContentsMargins(20, 20, 20, 20)  # 添加边距
        button_layout.setSpacing(20)  # 设置按钮间距
        
        # 添加弹簧使按钮居右
        button_layout.addStretch()
        
        # 取消按钮
        self.pushButton = QtWidgets.QPushButton(parent=self.button_container)
        self.pushButton.setMinimumSize(QtCore.QSize(85, 41))
        self.pushButton.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                font: 12px "微软雅黑";
                padding: 8px 16px;
                text-align: center;
                border-radius: 4px;
                border: 1px solid #ccc;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.pushButton.setObjectName("pushButton")
        button_layout.addWidget(self.pushButton)
        
        # 创建按钮
        self.fa_song_an_niu = QtWidgets.QPushButton(parent=self.button_container)
        self.fa_song_an_niu.setMinimumSize(QtCore.QSize(85, 41))
        self.fa_song_an_niu.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.main_color};
                color: white;
                font: italic bold 12px "微软雅黑";
                padding: 8px 16px;
                text-align: center;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {self.main_color_hover};
            }}
        """)
        self.fa_song_an_niu.setObjectName("fa_song_an_niu")
        button_layout.addWidget(self.fa_song_an_niu)
        
        # Set main window background
        self.centralwidget.setStyleSheet("background-color: white;")
        
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 413, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "创建群组"))
        self.dui_xian_shi.setText(_translate("MainWindow", "   创建新群聊"))
        self.label.setText(_translate("MainWindow", "群名称："))
        self.wen_ben3.setPlaceholderText(_translate("MainWindow", "输入群组名称..."))
        self.label_2.setText(_translate("MainWindow", "选择成员："))
        self.fa_song_an_niu.setText(_translate("MainWindow", "创建"))
        self.pushButton.setText(_translate("MainWindow", "取消"))


class CreateGroupWindow(QtWidgets.QMainWindow):
    group_created = QtCore.pyqtSignal(str, list)  # 信号：群名和成员列表
    
    def __init__(self, usernames, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("创建群组")
        
        # 创建成员列表控件
        self.members_list = QtWidgets.QListWidget(self.ui.centralwidget)
        self.members_list.setGeometry(QtCore.QRect(20, 210, 371, 240))
        self.members_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        self.members_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #e0f7fa;
                color: black;
            }
        """)
        
        # 添加成员到列表
        for username in usernames:
            item = QtWidgets.QListWidgetItem(username)
            self.members_list.addItem(item)
        
        # 连接信号
        self.ui.fa_song_an_niu.clicked.connect(self.create_group)
        self.ui.pushButton.clicked.connect(self.close)
        
        # 设置窗口背景
        self.setStyleSheet("background-color: white;")
        
        # 调整UI元素位置和大小
        self.adjust_ui_elements()
    
    def adjust_ui_elements(self):
        # 调整装饰标签位置
        self.ui.zhuang_shi.setGeometry(QtCore.QRect(0, 470, 411, 91))
        
        # 调整窗口大小
        self.resize(413, 609)
    
    def create_group(self):
        group_name = self.ui.wen_ben3.toPlainText().strip()
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


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    # 测试数据
    usernames = ["张三", "李四", "王五", "赵六", "钱七"]
    
    window = CreateGroupWindow(usernames)
    window.show()
    sys.exit(app.exec())