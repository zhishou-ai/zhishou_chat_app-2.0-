import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTreeView, QVBoxLayout, QWidget
from PyQt6.QtCore import QDir
from PyQt6.QtGui import QFileSystemModel


class TreeViewExample(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 TreeView 示例")
        self.setGeometry(100, 100, 600, 400)

        # 创建主部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 创建 TreeView
        self.tree_view = QTreeView()

        # 创建文件系统模型
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())  # 设置根路径为系统根目录

        # 将模型设置到 TreeView
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(QDir.rootPath()))  # 显示根目录

        # 隐藏不需要的列
        self.tree_view.setHeaderHidden(False)
        self.tree_view.hideColumn(1)  # 隐藏大小列
        self.tree_view.hideColumn(2)  # 隐藏类型列
        self.tree_view.hideColumn(3)  # 隐藏修改日期列

        # 添加到布局
        layout.addWidget(self.tree_view)

        # 设置样式
        self.tree_view.setStyleSheet("""
            QTreeView {
                font-size: 14px;
                show-decoration-selected: 1;
            }
            QTreeView::item:hover {
                background: #e7effd;
                border: 1px solid #bfcde4;
            }
            QTreeView::item:selected {
                background: #6ea1f1;
                color: white;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TreeViewExample()
    window.show()
    sys.exit(app.exec())