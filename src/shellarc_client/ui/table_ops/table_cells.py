from typing import Optional, TYPE_CHECKING
from collections.abc import Iterable
from functools import partial
import re

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidgetItem, QDialog, QLineEdit,
    QPushButton, QMessageBox, QGridLayout,
    QComboBox, QSplitter, QScrollArea,
    QWidget, QCheckBox
)
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import Qt

from shellarc_msk.mskdn.metanode import MSKDN_Metanode
from shellarc_msk.mskdn.node import MSKDN_VNode
from shellarc_msk.mskob.containercoll_obj import MSK_ContainerCollection
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskob.adress_obj import MSK_Address
from shellarc_msk.mskob.entity_obj import MSK_Entity
from shellarc_engine.mskio import read_msk
if TYPE_CHECKING:
    from shellarc_client.ui.table_ops.table_ops_ui import MSK_TableView

class TableCell(QTableWidgetItem):
    def __init__(self, 
                 field_name: Optional[str]=None,
                 metanode: Optional[MSKDN_Metanode]=None,
                 upstream_cells: Optional[list[tuple[int, int]]]=None,
                 derived_property: Optional[MSK_Property]=None,
                 max_metanode_num: int=10,
                 item_display: Optional[str]=None,
                 nodes_display: Optional[str]=None,
                 parent=None
                 ) -> None:
        super().__init__(parent)
        self.field_name = field_name
        self.upstream_cells = upstream_cells
        self.derived_property = derived_property
        self.metanode = metanode if metanode is not None else MSKDN_Metanode(iterable=[])
        self.max_metanode_num = max_metanode_num
        self.item_display = "VAL" if item_display is None else str(item_display)
        if metanode is None:
            self.nodes_display = None
        elif nodes_display is not None:
            self.nodes_display = nodes_display 
        else:
            self.nodes_display = str(self.metanode.prim_node)
        if self.metanode and self.metanode.prim_node is not None:
            self.set_display()

    def set_display(self):
        code_str = self.item_display
        VAL = "compile_test"
        try:
            compile(code_str, "<string>", "eval")
        except (SyntaxError, ValueError):
            self.item_display = "VAL"
        nodes_display_list = [
            self.metanode[idx].address.value 
            for idx in range(len(self.metanode))
        ]
        nodes_display_list = [
            eval(code_str) for VAL in nodes_display_list
        ]
        def replace_func(m):
            num_str, excl = m.groups()
            if excl == "!": return num_str 
            idx = int(num_str)
            return (
                nodes_display_list[idx] 
                if idx < len(nodes_display_list) and idx >= 0 
                else ""
            )
        display_text = re.sub(r"(\d+)(!?)", replace_func, self.nodes_display)
        self.setText(display_text)

class CellEditDialog(QDialog):
    def __init__(self, 
                 cell: TableCell,
                 parent=None
                 ) -> None:
        super().__init__(parent)
        self.cell = cell
        self.dialog_lo = QVBoxLayout()
        self.dialog_lo.addWidget(QLabel(f"Field name : {cell.field_name}"))

        item_display_lo = QHBoxLayout()
        item_display_lo.addWidget(QLabel("Item display : "))
        self.item_display_input = QLineEdit(cell.item_display)
        self.item_display_input.setPlaceholderText("Python")
        self.item_display_input.returnPressed.connect(self.set_nodes_display)
        item_display_lo.addWidget(self.item_display_input)
        self.dialog_lo.addLayout(item_display_lo)

        if (cell.derived_property is not None and 
            cell.upstream_cells is not None and 
            cell.nodes_display is not None):
            display_node_lo = QHBoxLayout()
            display_node_lo.addWidget(QLabel("Nodes display : "))
            self.display_node_input = QLineEdit(cell.nodes_display)
            self.display_node_input.returnPressed.connect(self.set_nodes_display)
            display_node_lo.addWidget(self.display_node_input)
            self.dialog_lo.addLayout(display_node_lo)

            self.dialog_lo.addWidget(QSplitter(Qt.Orientation.Vertical))
            self.dialog_lo.addWidget(QLabel(f"Upstreams : {",".join([str(cell) for cell in cell.upstream_cells])}"))
            self.dialog_lo.addWidget(QLabel(f"Property : {cell.derived_property.prop_name}"))

        self.mutable_checkbox = QCheckBox("Mutable")
        self.mutable_checkbox.setChecked(False)
        self.mutable_checkbox.stateChanged.connect(self.init_items_view)
        self.dialog_lo.addWidget(self.mutable_checkbox)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.scroll_lo = QVBoxLayout(scroll_widget)
        self.init_items_view()
        scroll_area.setWidget(scroll_widget)
        self.dialog_lo.addWidget(scroll_area)

        self.setLayout(self.dialog_lo)

    def init_items_view(self):
        while self.scroll_lo.count():
            widget = self.scroll_lo.takeAt(0).widget()
            if widget is not None:
                widget.deleteLater()

        for i, node in enumerate(self.cell.metanode):
            self.scroll_lo.setSpacing(4)
            self.scroll_lo.addWidget(QSplitter(Qt.Orientation.Vertical))
            self.scroll_lo.addWidget(QLabel(f"Container : {node.container_index}"))
            self.scroll_lo.addWidget(QLabel(f"Node index : {i}"))
            self.scroll_lo.addWidget(QLabel(f"Property : {node.prop.prop_name}"))
            self.scroll_lo.addWidget(QLabel(f"Type : {node.address.type.type_name}"))
            if not self.mutable_checkbox.isChecked():
                self.scroll_lo.addWidget(QLabel(f"Value : {node.address.value}"))
            else:
                value_edit_lo = QHBoxLayout()
                value_edit_lo.addWidget(QLabel("Value : "))
                self.value_edit_input = QLineEdit(node.address.value)
                value_edit_lo.addWidget(self.value_edit_input)
                value_apply_btn = QPushButton("Apply")
                value_apply_btn.setMaximumWidth(65)
                value_apply_btn.clicked.connect(
                    partial(
                        self.edit_value,
                        container_index=node.container_index,
                        prop=node.prop,
                        cell_index_in_metanode=i
                    )
                )
                value_edit_lo.addWidget(value_apply_btn)
                self.scroll_lo.addLayout(value_edit_lo)


    def edit_value(self,
                   container_index: MSK_HexIndex,
                   prop: MSK_Property,
                   cell_index_in_metanode: int
                   ) -> None:
        coll = MSK_ContainerCollection(field_name=self.cell.field_name)
        address = MSK_Address(
            adress_type=prop.prop_type,
            adress_value=self.value_edit_input.text()
        )
        print(self.value_edit_input.text() + " new")
        new_entity = coll.write_entity(
            container_index=container_index,
            prop=prop,
            adress=address,
            do_override=True
        )
        self.cell.metanode[cell_index_in_metanode].entity = new_entity
        self.init_items_view()


    def set_nodes_display(self) -> None:
        if (self.cell.derived_property is None or
            self.cell.upstream_cells is None or 
            self.cell.nodes_display is None):
            return
        self.cell.nodes_display = self.display_node_input.text().strip()
        self.cell.item_display = self.item_display_input.text().strip()
        self.cell.set_display()

class BuildAbstEdgeDialog(QDialog):
    def __init__(self, 
                 parent=None
                 ) -> None:
        super().__init__(parent)
        self.field_name = self.parentWidget().parentWidget().field_name

        dialog_lo = QVBoxLayout()
        dialog_lo.addWidget(QLabel(f"Field : {self.field_name}"))

        property_lo = QHBoxLayout()
        property_lo.addWidget(QLabel("Target property : ")) 
        self.property_combo = QComboBox()
        self.property_combo.clear()
        self.property_combo.addItems([x[0].prop_name for x in self.parentWidget().parentWidget().field_members])
        property_lo.addWidget(self.property_combo)
        dialog_lo.addLayout(property_lo)

        max_length_lo = QHBoxLayout()
        max_length_lo.addWidget(QLabel("Max length : "))
        self.max_length_input = QLineEdit("10")
        self.max_length_input.setValidator(QIntValidator(bottom=1))
        max_length_lo.addWidget(self.max_length_input)
        dialog_lo.addLayout(max_length_lo)

        apply_btn = QPushButton("Apply abstract edge")
        apply_btn.clicked.connect(self.accept)
        dialog_lo.addWidget(apply_btn)

        self.setLayout(dialog_lo)

    def get_derived_property(self) -> MSK_Property:
        target_property = self.parentWidget().parentWidget().field_members[self.property_combo.currentIndex()][0]
        return target_property

    def get_max_length(self) -> int:
        return int(self.max_length_input.text())




