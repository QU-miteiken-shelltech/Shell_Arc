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
from shellarc_client.ui.data_ops.data_ops_ui import DataOpsUi


class MainWindow(QMainWindow):
    def __init__(self, is_clean_mode: bool):
        super().__init__()
        self.is_clean_mode = is_clean_mode

        self.setWindowTitle("ShellArc 2027")
        self.setMinimumSize(950,650)
        # self.showMaximized()

        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.setCentralWidget(self.tab_widget)

        self._init_tabs()

    def _init_tabs(self):
        print("DATA")
        data_ops_tab = DataOpsUi()
        self.tab_widget.addTab(data_ops_tab, "Data")
        if self.is_clean_mode:
            return

        print("CALL")
        call_ops_tab = CallOpsUi()
        self.tab_widget.addTab(call_ops_tab, "Call")

        print("TASK")
        self.task_ops_tab = TaskOpsUi()
        self.tab_widget.addTab(self.task_ops_tab, "Task")

        print("CHAT")
        task_ops_tab = ChatOpsUi()
        self.tab_widget.addTab(task_ops_tab, "Chat")

        print("TABLE")
        table_ops_tab = TableOpsUi()
        self.tab_widget.addTab(table_ops_tab, "Table")

        print("GRAPH")
        graph_ops_tab = GraphOpsUi()
        self.tab_widget.addTab(graph_ops_tab, "Graph")

        print("PACKAGE")
        package_ops_tab = PackageOpsUi()
        self.tab_widget.addTab(package_ops_tab, "Package")

        print("START")

    def on_tab_changed(self, index: int):
        current_tab_widget = self.tab_widget.widget(index)
        if not hasattr(self, "task_ops_tab"):
            return
        if current_tab_widget == self.task_ops_tab:
            self.task_ops_tab.build_ui()

