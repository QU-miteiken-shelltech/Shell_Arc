from __future__ import annotations
from functools import partial

from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QPainter, QAction
from PySide6.QtWidgets import (
    QGraphicsView, QMenu, QVBoxLayout, 
    QWidget, QComboBox, QGridLayout,
    QLabel
)

from shellarc_client.ui.graph_ops.node_editor import MSKDN_NodeScene
from shellarc_msk.mskob.field_obj import MSK_Field
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskdn.hypergraph import MSKDN_Hypergraph
from shellarc_msk.mskdn.metanode import MSKDN_Metanode
from shellarc_msk.mskdn.node import MSKDN_VNode
from shellarc_msk.mskob.containercoll_obj import MSK_ContainerCollection

class GraphOpsUi(QWidget):
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MSKDN Node Editor")
        self.scene = MSKDN_NodeScene(self)
 
        lo = QVBoxLayout(self)
        lo.setContentsMargins(0, 0, 0, 0)

        settings_lo = QGridLayout()
        settings_lo.addWidget(QLabel("Field : "), 0, 0)
        self.field_combo = QComboBox()
        self.field_combo.clear()
        self.field_combo.addItems(MSK_Field.field_names())
        settings_lo.addWidget(self.field_combo, 0, 1)

        settings_lo.addWidget(QLabel("Pivot property : "), 1, 0)
        self.pivot_property_combo = QComboBox()
        self.pivot_property_combo.clear()
        settings_lo.addWidget(self.pivot_property_combo, 1, 1)
        self.pivot_property = None

        settings_lo.addWidget(QLabel("Pivot value : "), 2, 0)
        self.pivot_value_combo = QComboBox()
        self.pivot_value_combo.clear()
        settings_lo.addWidget(self.pivot_value_combo, 2, 1)
        self.pivot_value = None

        settings_lo.addWidget(QLabel("Display property : "), 3, 0)
        self.display_property_combo = QComboBox()
        self.display_property_combo.clear()
        settings_lo.addWidget(self.display_property_combo, 3, 1)
        self.display_property = None
        lo.addLayout(settings_lo)

        self.field_combo.currentIndexChanged.connect(self.switch_field)
        self.pivot_property_combo.currentIndexChanged.connect(self.switch_pivot_property)
        self.pivot_value_combo.currentIndexChanged.connect(self.switch_pivot_value)
        self.display_property_combo.currentIndexChanged.connect(self.switch_display_property)
        self.switch_field()
        self.switch_display_property()

        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        lo.addWidget(self.view)

        self.setLayout(lo)

        self.resize(800, 500)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.build_context_menu)

    def switch_field(self):
        new_field_name = self.field_combo.currentText()
        current_field = MSK_Field(field_name=new_field_name)
        self.field_members = [p for p in current_field.field_ls]
        self.field_name = new_field_name
        self.pivot_property_combo.clear()
        self.display_property_combo.clear()
        for field_item in current_field.field_ls:
            self.pivot_property_combo.addItem(
                field_item[0].prop_name,  field_item[0]
            )
            self.display_property_combo.addItem(
                field_item[0].prop_name,  field_item[0]
            )

    def switch_pivot_property(self):
        pivot_property : MSK_Property = self.pivot_property_combo.currentData()
        self.pivot_property = pivot_property
        values = []
        appeared = []
        for container in MSK_ContainerCollection(field_name=self.field_name).container_iter():
            entity = container.request_entity(requesting_prop=pivot_property)
            entity_value = entity.address.value
            if entity_value in appeared:
                continue
            values.append(entity)
            appeared.append(entity_value)
        values.sort(
            key=lambda x : x.address.value
        )
        self.pivot_value_combo.clear()
        for v in values:
            self.pivot_value_combo.addItem(
                v.address.value, v
            )

    def switch_pivot_value(self):
        pivot_value_entity = self.pivot_value_combo.currentData()
        self.pivot_vnode = MSKDN_VNode(entity=pivot_value_entity)

    def switch_display_property(self):
        self.display_property = self.display_property_combo.currentData()

    def build_context_menu(self, position: QPoint):
        menu = QMenu(self)
        menu.clear()

        glob_pos = self.mapToGlobal(position)
        view_pos = self.view.mapFromGlobal(glob_pos)
        scene_pos = self.view.mapToScene(view_pos)

        pivot_metanode = MSKDN_Metanode(
            iterable=[self.pivot_vnode]
        )
        hypergraph = MSKDN_Hypergraph(field_name=self.field_name)
        abst_edge = hypergraph.get_abstract_edge(
            upstream_metanodes=[pivot_metanode],
            target_prop=self.display_property,
            max_count=100
        )
        available_metanode = abst_edge.derivitive
        for available_vnode in available_metanode:
            action = menu.addAction(available_vnode.address.value)
            action.setData(MSKDN_Metanode(iterable=[available_vnode]))
            action.triggered.connect(lambda checked=False, a=action, p=scene_pos: self.spawn_node(a, p))

        menu.exec(glob_pos)

    def spawn_node(self, action: QAction, spawn_pos: QPointF):
        if isinstance(action, QAction):
            metanode : MSKDN_Metanode = action.data()  
            self.scene.add_node(
                metanode=metanode,
                input_num=1,
                output_num=1,
                pos=spawn_pos
            )