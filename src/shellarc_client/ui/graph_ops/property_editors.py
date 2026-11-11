from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit
)

if TYPE_CHECKING:
    from shellarc_client.ui.graph_ops.node_editor import MSKDN_NodeWidget

class NodePropertyEditor(QDialog):
    def __init__(self, 
                 node_widget: MSKDN_NodeWidget, 
                 parent=None
                 ):
        super().__init__(parent)
        self.setFixedSize(500, 300)
        self.metanode = node_widget.metanode
        
        dialog_lo = QVBoxLayout()
        btn = QPushButton("Test")
        dialog_lo.addWidget(btn)
        self.setLayout(dialog_lo)

class WirePropertyEditor(QDialog):
    def __init__(self, wire_widget, parent=None):
        super().__init__(parent)
        self.setFixedSize(500, 300)
        self.wire_widget = wire_widget

        dialog_lo = QVBoxLayout()
        self.expression_editor = QTextEdit("")
        self.expression_editor.setPlainText(
            "" if self.wire_widget.wire_expression is None else self.wire_widget.wire_expression
        )
        dialog_lo.addWidget(self.expression_editor)
        set_expression_btn = QPushButton("Set")
        set_expression_btn.clicked.connect(self.set_wire_expression)
        dialog_lo.addWidget(set_expression_btn)
        self.setLayout(dialog_lo)

    def set_wire_expression(self):
        self.wire_widget.wire_expression = self.expression_editor.toPlainText()
