from __future__ import annotations

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

#from shellarc_msk.mskdn.msk_nodes import MSKDN_Node, MSKDN_Port, MSKDN_Wire
from shellarc_client.ui.graph_ops.property_editors import NodePropertyEditor, WirePropertyEditor

class MSKDN_PortWidget(MSKDN_Port, QGraphicsEllipseItem):
    R = 6
 
    def __init__(self, node, name, is_output):
        QGraphicsEllipseItem.__init__(self, -self.R, -self.R, 2 * self.R, 2 * self.R, node)
        MSKDN_Port.__init__(self, node, name, is_output)
        self.setBrush(QApplication.palette().base())
 
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.scene().begin_wire_drag(self, event.scenePos())
            event.accept()
        else:
            super().mousePressEvent(event)
 
 
class MSKDN_NodeWidget(MSKDN_Node, QGraphicsRectItem):
    WIDTH = 140
    HEADER = 24
    ROW = 22
 
    def __init__(self, title="Node"):
        QGraphicsRectItem.__init__(self)
        MSKDN_Node.__init__(self, title)
        self.setBrush(QApplication.palette().base())
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        QGraphicsSimpleTextItem(title, self).setPos(6, 3)
        self.relayout()
 
    def create_port(self, name, is_output):
        port = MSKDN_PortWidget(self, name, is_output)
        port.label = QGraphicsSimpleTextItem(name, self)
        return port
 
    def on_ports_changed(self):
        self.relayout()
 
    def relayout(self):
        rows = max(len(self.inputs), len(self.outputs), 1)
        self.setRect(0, 0, self.WIDTH, self.HEADER + rows * self.ROW)
        for i, port in enumerate(self.inputs):
            y = self.HEADER + self.ROW * (i + 0.5)
            box = port.label.boundingRect()
            port.setPos(0, y)
            port.label.setPos(10, y - box.height() / 2)
        for i, port in enumerate(self.outputs):
            y = self.HEADER + self.ROW * (i + 0.5)
            box = port.label.boundingRect()
            port.setPos(self.WIDTH, y)
            port.label.setPos(self.WIDTH - 10 - box.width(), y - box.height() / 2)
        self.refresh_wires()
 
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            NodePropertyEditor(node_widget=self).exec()
        super().mouseDoubleClickEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.refresh_wires()
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


class MSKDN_WireWidget(MSKDN_Wire, QGraphicsLineItem):
    def __init__(self, start_port, end_port=None):
        QGraphicsLineItem.__init__(self)
        self.drag_pos = None
        self.handle = MSKDN_WireHandleWidget(self)
        MSKDN_Wire.__init__(self, start_port, end_port)
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
            handle.setVisible(self.end_port is not None)   # ドラッグ中の仮配線では隠す
            handle.setPos((p1 + p2) / 2)
 
 
class MSKDN_NodeScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_wire = None
 
    def add_node(self, title, inputs=(), outputs=(), pos=QPoint(0,0)):
        node = MSKDN_NodeWidget(title)
        for name in inputs:
            node.add_input(name)
        for name in outputs:
            node.add_output(name)
        node.setPos(pos)
        self.addItem(node)
        return node
 
    def connect_ports(self, a, b):
        """向きは自動で 出力->入力 にそろえる。繋げない組み合わせなら None。"""
        if not a.can_connect(b):
            return None
        out, inp = (a, b) if a.is_output else (b, a)
        wire = MSKDN_WireWidget(out, inp)
        self.addItem(wire)
        return wire
 
    # --- ポートからのドラッグ接続 ---------------------------------------------
    def begin_wire_drag(self, port, scene_pos):
        wire = MSKDN_WireWidget(port)           # 仮配線 (ポートには登録されない)
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
            self.removeItem(wire)               # 先に仮配線を消してから、下のポートを探す
            pos = event.scenePos()
            for item in self.items(QRectF(pos.x() - 8, pos.y() - 8, 16, 16)):
                if isinstance(item, MSKDN_PortWidget):
                    self.connect_ports(wire.start_port, item)
                    break
        super().mouseReleaseEvent(event)
