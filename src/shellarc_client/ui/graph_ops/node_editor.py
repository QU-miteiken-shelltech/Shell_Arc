from __future__ import annotations
from typing import Optional

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import QPalette, QPen
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
        # このポートに繋がっているワイヤー
        self.wires: list[MSKDN_WireWidget] = []
        self.setBrush(QApplication.palette().base())
        self.setCursor(Qt.CursorShape.CrossCursor)

    def can_connect(self, other) -> bool:
        """出力と入力の組で、別ノード同士で、まだ繋がっていなければ True。"""
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
    HEADER = 24
    ROW = 22

    def __init__(self, metanode: MSKDN_VNode,
                 input_num: int = 1,
                 output_num: int = 1
                 ):
        QGraphicsRectItem.__init__(self)
        self.metanode = metanode
        self.input_num = input_num
        self.output_num = output_num
        # setFlags より先に用意しておく（itemChange から参照されるため）
        self.inputs: list[MSKDN_PortWidget] = []
        self.outputs: list[MSKDN_PortWidget] = []
        self.setBrush(QApplication.palette().base())
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.title = QGraphicsSimpleTextItem(self.metanode.get_prim_node().prop.prop_name, self)
        self.title.setPos(6, 3)
        self.relayout()

    # ---- ポート管理 ----
    def set_port_counts(self, input_num: int, output_num: int):
        self.input_num = input_num
        self.output_num = output_num
        self.on_ports_changed()

    def on_ports_changed(self):
        self.relayout()

    def _sync_ports(self, ports: list[MSKDN_PortWidget], count: int, is_output: bool):
        """ports の数を count に合わせる。減らす場合は繋がっているワイヤーも消す。"""
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
        rows = max(self.input_num, self.output_num, 1)
        self.setRect(0, 0, self.WIDTH, self.HEADER + rows * self.ROW)
        for i, port in enumerate(self.inputs):
            port.setPos(0, self.HEADER + self.ROW * (i + 0.5))
        for i, port in enumerate(self.outputs):
            port.setPos(self.WIDTH, self.HEADER + self.ROW * (i + 0.5))
        self.refresh_wires()

    def refresh_wires(self):
        for port in self.inputs + self.outputs:
            port.refresh_wires()

    # ---- イベント ----
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


class MSKDN_WireWidget(QGraphicsLineItem):
    """
    ポート間の線。データとしての辺は self.edge (MSKDN_DirectionalEdge) に持たせる。
    確定済みワイヤー: start_port = 出力側, end_port = 入力側, edge あり
    ドラッグ中ワイヤー: start_port = 押したポート, end_port = None, edge = None
    """

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

    # 以前の upstream / downstream 属性との互換用
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
        """両端のポートに自分を登録する（ノード移動時に追従させるため）。"""
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
        """向きは自動で 出力->入力 にそろえる。繋げない組み合わせなら None。"""
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
        # ドラッグ中は仮の線だけ。辺 (edge) は接続が確定した時に作る。
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