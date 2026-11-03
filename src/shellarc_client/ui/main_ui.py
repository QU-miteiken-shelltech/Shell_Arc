import sys
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget,
    QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt

from shellarc_client.ui.call_ops.call_ops_ui import CallOpsUi
from shellarc_client.ui.task_ops.task_ops_ui import TaskOpsUi
from shellarc_client.ui.chat_ops.chat_ops_ui import ChatOpsUi
from shellarc_client.ui.table_ops.table_ops_ui import TableOpsUi
from shellarc_client.ui.graph_ops.graph_ops_ui import GraphOpsUi
from shellarc_client.ui.package_ops.package_ops_ui import PackageOpsUi


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ShellArc 2027")
        self.showMaximized()

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self._init_tabs()

    def _init_tabs(self):
        call_ops_tab = CallOpsUi()
        self.tab_widget.addTab(call_ops_tab, "Call")

        task_ops_tab = TaskOpsUi()
        self.tab_widget.addTab(task_ops_tab, "Task")

        task_ops_tab = ChatOpsUi()
        self.tab_widget.addTab(task_ops_tab, "Chat")

        table_ops_tab = TableOpsUi()
        self.tab_widget.addTab(table_ops_tab, "Table")

        graph_ops_tab = GraphOpsUi()
        self.tab_widget.addTab(graph_ops_tab, "Graph")

        package_ops_tab = PackageOpsUi()
        self.tab_widget.addTab(package_ops_tab, "Package")