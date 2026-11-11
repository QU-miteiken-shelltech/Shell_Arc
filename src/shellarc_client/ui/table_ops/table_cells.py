from typing import Optional, TYPE_CHECKING
from collections.abc import Iterable

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidgetItem, QDialog, QLineEdit,
    QPushButton, QMessageBox, QGridLayout,
    QComboBox, QSplitter
)
from PySide6.QtGui import QIntValidator, QRegularExpressionValidator
from PySide6.QtCore import Qt, QRegularExpression

from shellarc_msk.mskdn.metanode import MSKDN_Metanode
from shellarc_msk.mskdn.node import MSKDN_VNode
from shellarc_msk.mskdn.abstract_edge import MSKDN_AbstEdge
from shellarc_msk.mskob.containercoll_obj import MSK_ContainerCollection
from shellarc_msk.mskob.property_obj import MSK_Property
if TYPE_CHECKING:
    from shellarc_client.ui.table_ops.table_ops_ui import MSK_TableView

class TableCell(QTableWidgetItem):
    def __init__(self, 
                 field_name: Optional[str]=None,
                 metanode: Optional[MSKDN_Metanode]=None,
                 upstream_cells: Optional[list[tuple[int, int]]]=None,
                 derived_property: Optional[MSK_Property]=None,
                 max_metanode_num: int=10,
                 display_nodes: Optional[list[int]]=None,
                 parent=None
                 ) -> None:
        super().__init__(parent)
        self.field_name = field_name
        self.upstream_cells = upstream_cells
        self.derived_property = derived_property
        self.metanode = metanode if metanode is not None else MSKDN_Metanode(iterable=[])
        self.max_metanode_num = max_metanode_num
        if metanode is None:
            self.display_nodes = None
        elif display_nodes is not None:
            self.display_nodes = display_nodes 
        else:
            self.display_nodes = [self.metanode.prim_node] 
        if self.metanode and self.metanode.prim_node is not None:
            self.set_display()

    def set_display(self):
        diaplay_node_list = [
            self.metanode[i].address.value 
            for i in self.display_nodes
            if i < len(self.metanode)
        ]
        display_text = ", ".join(diaplay_node_list)
        self.setText(display_text)
        

class CellEditDialog(QDialog):
    def __init__(self, 
                 cell: TableCell,
                 parent=None
                 ) -> None:
        super().__init__(parent)
        self.cell = cell
        dialog_lo = QVBoxLayout()
        dialog_lo.addWidget(QLabel(f"Field name : {cell.field_name}"))
        if (cell.derived_property is not None and 
            cell.upstream_cells is not None and 
            cell.display_nodes is not None):
            display_node_lo = QHBoxLayout()
            display_node_lo.addWidget(QLabel("Display nodes : "))
            self.display_node_input = QLineEdit(" ".join([str(n) for n in cell.display_nodes]))
            validator = QRegularExpressionValidator(QRegularExpression(r"^\d+(\s\d+)*\s?$|^$"), self)
            self.display_node_input.setValidator(validator)
            display_node_lo.addWidget(self.display_node_input)
            dialog_lo.addLayout(display_node_lo)
            dialog_lo.addWidget(QLabel(f"Upstreams : {",".join([str(cell) for cell in cell.upstream_cells])}"))
            dialog_lo.addWidget(QLabel(f"Property : {cell.derived_property.prop_name}"))

        for i,node in enumerate(cell.metanode):
            dialog_lo.addWidget(QSplitter(Qt.Orientation.Vertical))
            dialog_lo.addWidget(QLabel(f"Container : {node.entity.container_index}"))
            dialog_lo.addWidget(QLabel(f"Node index : {i}"))
            dialog_lo.addWidget(QLabel(f"Property : {node.prop.prop_name}"))
            dialog_lo.addWidget(QLabel(f"Type : {node.address.type.type_name}"))
            dialog_lo.addWidget(QLabel(f"Value : {node.address.value}"))

        self.setLayout(dialog_lo)

    def set_display_nodes(self) -> None:
        if (self.cell.derived_property is None or
            self.cell.upstream_cells is None or 
            self.cell.display_nodes is None):
            return
        self.cell.display_nodes = [int(n) for n in self.display_node_input.text().split(" ")]
        self.cell.set_display()

class HeaderEditDialog(QDialog):
    def __init__(self, 
                 logical_index: int,
                 is_vertical: bool,
                 table,
                 parent=None
                 ) -> None:
        super().__init__(parent)
        self.field_name = self.parentWidget().parentWidget().field_name
        
        self.table = table
        self.logical_index = logical_index
        self.is_vertical = is_vertical
        dialog_lo = QVBoxLayout()

        iterator_lo = QGridLayout()
        field_label = QLabel("Field : ")
        iterator_lo.addWidget(field_label, 0, 0)
        self.field_name_label = QLabel(self.field_name)
        iterator_lo.addWidget(self.field_name_label, 0, 1)
        property_label = QLabel("Property :")
        iterator_lo.addWidget(property_label, 1, 0)
        self.property_combo = QComboBox()
        self.property_combo.clear()
        self.property_combo.addItems([x[0].prop_name for x in self.parentWidget().parentWidget().field_members])
        iterator_lo.addWidget(self.property_combo, 1, 1)
        start_pos_label = QLabel("Start at : ")
        iterator_lo.addWidget(start_pos_label, 2, 0)
        self.start_pos_input = QLineEdit("1") #1-start
        self.start_pos_input.setValidator(QIntValidator(bottom=1))
        iterator_lo.addWidget(self.start_pos_input, 2, 1)
        dialog_lo.addLayout(iterator_lo)

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_header)
        dialog_lo.addWidget(apply_btn)

        self.setLayout(dialog_lo)

    def apply_header(self):
        header_pos = self.logical_index
        start_pos = int(self.start_pos_input.text()) - 1 if self.start_pos_input.text() else 0

        key_property = self.parentWidget().parentWidget().field_members[self.property_combo.currentIndex()][0]
        iterator = []
        appeared = []
        for container in MSK_ContainerCollection(field_name=self.field_name).container_iter():
            entity = container.request_entity(requesting_prop=key_property)
            entity_value = entity.address.value
            if entity_value in appeared:
                continue
            iterator.append(entity)
            appeared.append(entity_value)
        iterator.sort(
            key=lambda x : x.address.value
        )

        if self.is_vertical:
            current_col_num = self.table.columnCount()
            if current_col_num < start_pos + len(iterator):
                self.table.setColumnCount(start_pos + len(iterator))
                for col in range(start_pos, start_pos + len(iterator)):
                    metanode = MSKDN_Metanode(
                        iterable=[MSKDN_VNode(entity=iterator[col - start_pos])]
                    )
                    cell = TableCell(
                        field_name=self.field_name,
                        metanode=metanode
                    )
                    self.table.setItem(header_pos, col, cell)
        else:
            current_row_num = self.table.rowCount()
            if current_row_num < start_pos + len(iterator):
                self.table.setRowCount(start_pos + len(iterator))
                for row in range(start_pos, start_pos + len(iterator)):
                    metanode = MSKDN_Metanode(
                        iterable=[MSKDN_VNode(entity=iterator[row - start_pos])]
                    )
                    cell = TableCell(
                        field_name=self.field_name,
                        metanode=metanode
                    )
                    self.table.setItem(row, header_pos, cell)
        self.accept()

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

    def get_abst_edge(self) -> MSK_Property:
        target_property = self.parentWidget().parentWidget().field_members[self.property_combo.currentIndex()][0]
        return target_property

    def get_max_length(self) -> int:
        return int(self.max_length_input.text())




