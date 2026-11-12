from __future__ import annotations

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
        pivot_property : MSK_Property = self.pivot_property_combo.currentData()
        pivot_value_entity = self.pivot_value_combo.currentData()
        self.available_metanodes: list[MSKDN_Metanode] = []
        for container in MSK_ContainerCollection(field_name=self.field_name).container_iter():
            entity = container.request_entity(requesting_prop=pivot_property)
            if entity.address.value == pivot_value_entity.address.value:
                self.available_metanodes.append(
                    MSKDN_Metanode.container_to_metanode(
                        container=container
                    )
                )

    def switch_display_property(self):
        if not self.available_metanodes:
            return
        self.display_property = self.display_property_combo.currentData()
        for metanode in self.available_metanodes:
            for i, entity in enumerate(metanode):
                if entity.prop == self.display_property:
                    metanode.prim_node = i
                    break

    def build_context_menu(self, position: QPoint):
        menu = QMenu(self)
        menu.clear()

        glob_pos = self.mapToGlobal(position)
        view_pos = self.view.mapFromGlobal(glob_pos)
        scene_pos = self.view.mapToScene(view_pos)

        for available_metanode in self.available_metanodes:
            action = menu.addAction(available_metanode.get_prim_node().address.value)
            action.setData(available_metanode)
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