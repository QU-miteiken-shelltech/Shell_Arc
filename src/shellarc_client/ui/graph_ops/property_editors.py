from __future__ import annotations
from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel,
    QWidget, QGraphicsView, QGraphicsScene
)
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent

if TYPE_CHECKING:
    from shellarc_client.ui.graph_ops.node_editor import MSKDN_NodeWidget
from shellarc_client.ui.graph_ops.block_expression_editor import ExpressionBlockLabel, BlockyExpressionEditor




class NodePropertyEditor(QDialog):
    def __init__(self, 
                 node_widget: MSKDN_NodeWidget, 
                 parent=None
                 ):
        super().__init__(parent)
        self.setFixedWidth(700)
        self.metanode = node_widget.metanode

        dialog_lo = QHBoxLayout()

        metanode_view_lo = QVBoxLayout()
        for vnode in node_widget.metanode:
            property_label = ExpressionBlockLabel(
                text=f"\
                    Property : {vnode.prop.prop_name}\n \
                    Type : {vnode.address.type.type_name}\n \
                    Value : {vnode.address.value}",
                data=vnode.prop,
                name=vnode.prop.prop_name  # variable name used in the generated code
            )
            metanode_view_lo.addWidget(property_label)
            metanode_view_lo.addStretch()

        dialog_lo.addLayout(metanode_view_lo)

        blocky_expression_lo = QVBoxLayout()
        blocky_expression_editor = BlockyExpressionEditor()
        blocky_expression_lo.addWidget(blocky_expression_editor)
        blocky_expression_editor.set_operations(
            {"node color to": "node_widget.colorize_block(__CUSTOM__)"}
        )
        dialog_lo.addLayout(blocky_expression_lo)
        
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