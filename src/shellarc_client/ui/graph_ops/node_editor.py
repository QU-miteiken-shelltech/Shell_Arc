from __future__ import annotations
from typing import Optional

from PySide6.QtCore import (
    QRectF, Qt, QPoint
)
from PySide6.QtGui import (
    QPalette, QPen
)
from PySide6.QtWidgets import (
    QApplication, QGraphicsItem, QGraphicsScene, 
    QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsLineItem,
    QGraphicsSimpleTextItem
)
from PySide6.QtCore import QLineF

from shellarc_msk.mskdn.metanode import MSKDN_Metanode
from shellarc_msk.mskdn.node import MSKDN_VNode
from shellarc_msk.mskdn.directional_edge import MSKDN_DirectionalEdge
from shellarc_client.ui.graph_ops.property_editors import NodePropertyEditor, WirePropertyEditor

class MSKDN_PortWidget(QGraphicsEllipseItem):
    R = 6
 
    def __init__(self, 
                 affiliated_node: MSKDN_NodeWidget, 
                 is_output: bool
                 ):
        QGraphicsEllipseItem.__init__(self, -self.R, -self.R, 2 * self.R, 2 * self.R, affiliated_node)
        self.affiliated_node = affiliated_node
        self.is_output = is_output
        self.setBrush(QApplication.palette().base())
 
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.scene().begin_wire_drag(self, event.scenePos())
            event.accept()
        else:
            super().mousePressEvent(event)
 
 
class MSKDN_NodeWidget(QGraphicsRectItem):
    WIDTH = 140
    HEADER = 24
    ROW = 22
 
    def __init__(self, 
                 metanode: MSKDN_Metanode, 
                 input_num: int,
                 output_num: int
                 ):
        QGraphicsRectItem.__init__(self)
        self.metanode = metanode
        self.setBrush(QApplication.palette().base())
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.input_num = input_num
        self.output_num = output_num
        QGraphicsSimpleTextItem(self.metanode.get_prim_node().address.value, self).setPos(6, 3)
        self.relayout()

 
    def on_ports_changed(self):
        self.relayout()
 
    def relayout(self):
        rows = max(self.input_num, self.output_num, 1)
        self.setRect(0, 0, self.WIDTH, self.HEADER + rows * self.ROW)
        for i in range(self.input_num):
            y = self.HEADER + self.ROW * (i + 0.5)
            box = port.label.boundingRect()
            port.setPos(0, y)
        for i, port in enumerate(self.outputs):
            y = self.HEADER + self.ROW * (i + 0.5)
            box = port.label.boundingRect()
            port.setPos(self.WIDTH, y)
 
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            NodePropertyEditor(node_widget=self).exec()
        super().mouseDoubleClickEvent(event)

    def itemChange(self, change, value):
        # if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
        #     self.refresh_wires()
        return super().itemChange(change, value)

 
 
class MSKDN_WireHandleWidget(QGraphicsEllipseItem):
    """ワイヤー中点の小さな丸。ダブルクリックを受け付ける。"""
    R = 5

    def __init__(self, wire):
        super().__init__(-self.R, -self.R, 2 * self.R, 2 * self.R, wire)
        self.setBrush(QApplication.palette().base())
        self.setPen(QPen(QApplication.palette().color(QPalette.ColorRole.Text), 1.5))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        # 受け取らないとダブルクリックが届かないので、押下を受理する
        event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            WirePropertyEditor(wire_widget=self.parentItem()).exec()
        event.accept()


class MSKDN_WireWidget(MSKDN_DirectionalEdge, QGraphicsLineItem):
    def __init__(self, 
                 directional_edge: MSKDN_DirectionalEdge
                 ):
        QGraphicsLineItem.__init__(self)
        self.upstream = directional_edge.upstream
        self.downstream = directional_edge.downstream
        self.drag_pos = None
        self.handle = MSKDN_WireHandleWidget(self)
        self.setPen(QPen(QApplication.palette().color(QPalette.ColorRole.Text), 2))
        self.setZValue(-1)          
        self.refresh()
 
    def refresh(self):
        p1 = self.start_port.scenePos()
        if self.end_port is not None:
            p2 = self.end_port.scenePos()
        else:
            p2 = self.drag_pos if self.drag_pos is not None else p1
        self.setLine(QLineF(p1, p2))
        handle = getattr(self, 'handle', None)
        if handle is not None:
            handle.setVisible(self.end_port is not None)   
            handle.setPos((p1 + p2) / 2)
 
 
class MSKDN_NodeScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_wire = None
 
    def add_node(self, 
                 metanode: MSKDN_Metanode, 
                 input_num: int=1, 
                 output_num: int=1, 
                 pos=QPoint(0,0)
                 ):
        node = MSKDN_NodeWidget(
            metanode=metanode,
            input_num=input_num,
            output_num=output_num
        )
        node.setPos(pos)
        self.addItem(node)
        return node
 
    def connect_ports(self, a, b):
        """向きは自動で 出力->入力 にそろえる。繋げない組み合わせなら None。"""
        if not a.can_connect(b):
            return None
        out, inp = (a, b) if a.is_output else (b, a)
        wire = MSKDN_WireWidget(
            directional_edge=MSKDN_DirectionalEdge(
                upstream=out.affiliated_node,
                downstream=inp.affiliated_node
            )
        )
        self.addItem(wire)
        return wire
 
    def begin_wire_drag(self, 
                        port: MSKDN_PortWidget, 
                        scene_pos):
        wire = MSKDN_WireWidget(
            directional_edge=MSKDN_DirectionalEdge(
                upstream=port.affiliated_node
            )
        )          
        wire.drag_pos = scene_pos
        wire.refresh()
        self.addItem(wire)
        self._drag_wire = wire
 
    def mouseMoveEvent(self, event):
        if self._drag_wire is not None:
            self._drag_wire.drag_pos = event.scenePos()
            self._drag_wire.refresh()
            return
        super().mouseMoveEvent(event)
 
    def mouseReleaseEvent(self, event):
        wire = self._drag_wire
        if wire is not None:
            self._drag_wire = None
            self.removeItem(wire)             
            pos = event.scenePos()
            for item in self.items(QRectF(pos.x() - 8, pos.y() - 8, 16, 16)):
                if isinstance(item, MSKDN_PortWidget):
                    self.connect_ports(wire.start_port, item)
                    break
        super().mouseReleaseEvent(event)
