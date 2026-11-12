from __future__ import annotations
from typing import Optional

from PySide6.QtCore import (
    Qt, QLineF, QPointF, 
    QRectF
)
from PySide6.QtGui import (
    QPalette, QPen, QColor, 
    QBrush
)
from PySide6.QtWidgets import (
    QApplication, QGraphicsItem, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsLineItem,
    QGraphicsSimpleTextItem
)

from shellarc_msk.mskdn.metanode import MSKDN_Metanode
from shellarc_msk.mskdn.node import MSKDN_VNode
from shellarc_msk.mskdn.directional_edge import MSKDN_DirectionalEdge
from shellarc_client.ui.graph_ops.property_editors import NodePropertyEditor, WirePropertyEditor


class MSKDN_PortWidget(QGraphicsEllipseItem):
    R = 6

    def __init__(self,
                 affiliated_node: MSKDN_NodeWidget,
                 is_output: bool,
                 index: int = 0
                 ):
        QGraphicsEllipseItem.__init__(self, -self.R, -self.R, 2 * self.R, 2 * self.R, affiliated_node)
        self.affiliated_node = affiliated_node
        self.is_output = is_output
        self.index = index
        self.wires: list[MSKDN_WireWidget] = []
        self.setBrush(QApplication.palette().base())
        self.setCursor(Qt.CursorShape.CrossCursor)

    def can_connect(self, other) -> bool:
        if not isinstance(other, MSKDN_PortWidget) or other is self:
            return False
        if other.is_output == self.is_output:
            return False
        if other.affiliated_node is self.affiliated_node:
            return False
        return not any(w.other_port(self) is other for w in self.wires)

    def refresh_wires(self):
        for wire in list(self.wires):
            wire.refresh()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.scene().begin_wire_drag(self, event.scenePos())
            event.accept()
        else:
            super().mousePressEvent(event)


class MSKDN_NodeWidget(QGraphicsRectItem):
    WIDTH = 140
    HEIGHT = 65

    def __init__(self, 
                 metanode: MSKDN_Metanode,
                 input_num: int = 1,
                 output_num: int = 1
                 ):
        QGraphicsRectItem.__init__(self)
        self.metanode = metanode
        self.input_num = input_num
        self.output_num = output_num
        self.inputs: list[MSKDN_PortWidget] = []
        self.outputs: list[MSKDN_PortWidget] = []
        self.setBrush(QApplication.palette().base())
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.title = QGraphicsSimpleTextItem(self.metanode.get_prim_node().address.value, self)
        font = self.title.font()
        font.setPointSize(20)
        self.title.setFont(font)
        self.title.setPos(
            (self.WIDTH  - self.title.boundingRect().width()) / 2,
            (self.HEIGHT - self.title.boundingRect().height()) / 2
        )
        self.relayout()

    def set_port_counts(self, input_num: int, output_num: int):
        self.input_num = input_num
        self.output_num = output_num
        self.on_ports_changed()

    def on_ports_changed(self):
        self.relayout()

    def _sync_ports(self, ports: list[MSKDN_PortWidget], count: int, is_output: bool):
        while len(ports) < count:
            ports.append(MSKDN_PortWidget(self, is_output, len(ports)))
        while len(ports) > count:
            port = ports.pop()
            for wire in list(port.wires):
                wire.remove()
            if port.scene() is not None:
                port.scene().removeItem(port)
            else:
                port.setParentItem(None)

    def relayout(self):
        self._sync_ports(self.inputs, self.input_num, is_output=False)
        self._sync_ports(self.outputs, self.output_num, is_output=True)
        self.setRect(0, 0, self.WIDTH, self.HEIGHT)
        for i, port in enumerate(self.inputs):
            port.setPos((self.WIDTH / (len(self.inputs) + 1)) * (i + 1), 0)
        for i, port in enumerate(self.outputs):
            port.setPos((self.WIDTH / (len(self.outputs) + 1)) * (i + 1), self.HEIGHT)
        self.refresh_wires()

    def refresh_wires(self):
        for port in self.inputs + self.outputs:
            port.refresh_wires()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            NodePropertyEditor(node_widget=self).exec()
        super().mouseDoubleClickEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.refresh_wires()
        return super().itemChange(change, value)

    def colorize_border(self, color: QColor):
        self.setPen(color)

    def colorize_block(self, color: QColor):
        self.setBrush(color)

    def set_border_thickness(self, thickness: int):
        pen = self.pen()
        pen.setWidth(thickness)
        self.setPen(pen)


class MSKDN_WireHandleWidget(QGraphicsEllipseItem):
    R = 5

    def __init__(self, wire):
        super().__init__(-self.R, -self.R, 2 * self.R, 2 * self.R, wire)
        self.setBrush(QApplication.palette().base())
        self.setPen(QPen(QApplication.palette().color(QPalette.ColorRole.Text), 1.5))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            WirePropertyEditor(wire_widget=self.parentItem()).exec()
        event.accept()


class MSKDN_WireWidget(QGraphicsLineItem):

    def __init__(self,
                 start_port: MSKDN_PortWidget,
                 end_port: Optional[MSKDN_PortWidget] = None,
                 edge: Optional[MSKDN_DirectionalEdge] = None
                 ):
        QGraphicsLineItem.__init__(self)
        self.start_port = start_port
        self.end_port = end_port
        self.edge = edge
        self.drag_pos: Optional[QPointF] = None
        self.setPen(QPen(QApplication.palette().color(QPalette.ColorRole.Text), 2))
        self.setZValue(-1)
        self.handle = MSKDN_WireHandleWidget(self)
        self.refresh()

    @property
    def upstream(self):
        return self.edge.upstream if self.edge is not None else None

    @property
    def downstream(self):
        return self.edge.downstream if self.edge is not None else None

    def other_port(self, port: MSKDN_PortWidget) -> Optional[MSKDN_PortWidget]:
        if port is self.start_port:
            return self.end_port
        if port is self.end_port:
            return self.start_port
        return None

    def attach(self):
        for port in (self.start_port, self.end_port):
            if port is not None and self not in port.wires:
                port.wires.append(self)

    def detach(self):
        for port in (self.start_port, self.end_port):
            if port is not None and self in port.wires:
                port.wires.remove(self)

    def remove(self):
        self.detach()
        if self.scene() is not None:
            self.scene().removeItem(self)

    def refresh(self):
        p1 = self.start_port.scenePos()
        if self.end_port is not None:
            p2 = self.end_port.scenePos()
        else:
            p2 = self.drag_pos if self.drag_pos is not None else p1
        self.setLine(QLineF(p1, p2))
        self.handle.setVisible(self.end_port is not None)
        self.handle.setPos((p1 + p2) / 2)


class MSKDN_NodeScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_wire: Optional[MSKDN_WireWidget] = None

    def add_node(self,
                 metanode: MSKDN_Metanode,
                 input_num: int = 1,
                 output_num: int = 1,
                 pos: Optional[QPointF] = None
                 ):
        node = MSKDN_NodeWidget(
            metanode=metanode,
            input_num=input_num,
            output_num=output_num
        )
        node.setPos(pos if pos is not None else QPointF(0, 0))
        self.addItem(node)
        return node

    def connect_ports(self, a: MSKDN_PortWidget, b: MSKDN_PortWidget):
        if not a.can_connect(b):
            return None
        out, inp = (a, b) if a.is_output else (b, a)
        edge = MSKDN_DirectionalEdge(
            upstream=out.affiliated_node,
            downstream=inp.affiliated_node
        )
        wire = MSKDN_WireWidget(start_port=out, end_port=inp, edge=edge)
        wire.attach()
        self.addItem(wire)
        return wire

    def begin_wire_drag(self,
                        port: MSKDN_PortWidget,
                        scene_pos):
        wire = MSKDN_WireWidget(start_port=port)
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
                if isinstance(item, MSKDN_PortWidget) and wire.start_port.can_connect(item):
                    self.connect_ports(wire.start_port, item)
                    break
        super().mouseReleaseEvent(event)