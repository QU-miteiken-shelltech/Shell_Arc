from __future__ import annotations

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QGraphicsView, QMenu, QVBoxLayout, 
    QWidget
)

from shellarc_client.ui.graph_ops.node_editor import MSKDN_NodeScene

class GraphOpsUi(QWidget):
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MSKDN Node Editor")
        self.scene = MSKDN_NodeScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
 
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        self.resize(800, 500)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position: QPoint):
        menu = QMenu(self)
        add_node_A = menu.addAction("NodeA")
        add_node_B = menu.addAction("NodeB")
        add_node_C = menu.addAction("NodeC")

        glob_pos = self.mapToGlobal(position)
        view_pos = self.view.mapFromGlobal(glob_pos)
        scene_pos = self.view.mapToScene(view_pos)
        action = menu.exec(glob_pos)

        if action == add_node_A:
            self.scene.add_node("A", outputs=["out"], pos=scene_pos)
        elif action == add_node_B:
            self.scene.add_node("B", inputs=["in1", "in2"], outputs=["out"], pos=scene_pos)
        elif action == add_node_C:
            self.scene.add_node("C", inputs=["in"], pos=scene_pos)