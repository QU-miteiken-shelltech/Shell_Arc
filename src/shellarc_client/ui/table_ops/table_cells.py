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
from PySide6.QtGui import QIntValidator, QRegularExpressionValidator
from PySide6.QtCore import Qt, QRegularExpression

from shellarc_msk.mskdn.metanode import MSKDN_Metanode
from shellarc_msk.mskdn.node import MSKDN_VNode
from shellarc_msk.mskdn.abstract_edge import MSKDN_AbstEdge
from shellarc_msk.mskob.containercoll_obj import MSK_ContainerCollection
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_msk.mskob.adress_obj import MSK_Address
if TYPE_CHECKING:
    from shellarc_client.ui.table_ops.table_ops_ui import MSK_TableView

class TableCell(QTableWidgetItem):
    def __init__(self, 
                 field_name: Optional[str]=None,
                 metanode: Optional[MSKDN_Metanode]=None,
                 upstream_cells: Optional[list[tuple[int, int]]]=None,
                 derived_property: Optional[MSK_Property]=None,
                 max_metanode_num: int=10,
                 display_form: Optional[str]=None,
                 display_nodes: Optional[str]=None,
                 parent=None
                 ) -> None:
        super().__init__(parent)
        self.field_name = field_name
        self.upstream_cells = upstream_cells
        self.derived_property = derived_property
        self.metanode = metanode if metanode is not None else MSKDN_Metanode(iterable=[])
        self.max_metanode_num = max_metanode_num
        self.display_form = "VAL" if display_form is None else str(display_form)
        if metanode is None:
            self.display_nodes = None
        elif display_nodes is not None:
            self.display_nodes = display_nodes 
        else:
            self.display_nodes = str(self.metanode.prim_node)
        if self.metanode and self.metanode.prim_node is not None:
            self.set_display()

    def set_display(self):
        code_str = self.display_form
        VAL = "compile_test"
        try:
            compile(code_str, "<string>", "eval")
        except (SyntaxError, ValueError):
            self.display_form = "VAL"
        display_nodes_list = [
            self.metanode[idx].address.value 
            for idx in range(len(self.metanode))
        ]
        display_nodes_list = [
            eval(code_str) for VAL in display_nodes_list
        ]
        def replace_func(m):
            num_str, excl = m.groups()
            if excl == "!": return num_str 
            idx = int(num_str)
            return display_nodes_list[idx] if idx < len(display_nodes_list) else ""
        display_text = re.sub(r"(\d+)(!?)", replace_func, self.display_nodes)
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

        display_form_lo = QHBoxLayout()
        display_form_lo.addWidget(QLabel("Display form : "))
        self.display_form_input = QLineEdit(cell.display_form)
        self.display_form_input.setPlaceholderText("Python")
        self.display_form_input.returnPressed.connect(self.set_display_nodes)
        display_form_lo.addWidget(self.display_form_input)
        self.dialog_lo.addLayout(display_form_lo)

        if (cell.derived_property is not None and 
            cell.upstream_cells is not None and 
            cell.display_nodes is not None):
            display_node_lo = QHBoxLayout()
            display_node_lo.addWidget(QLabel("Display nodes : "))
            self.display_node_input = QLineEdit(cell.display_nodes)
            self.display_node_input.returnPressed.connect(self.set_display_nodes)
            display_node_lo.addWidget(self.display_node_input)
            self.dialog_lo.addLayout(display_node_lo)

            self.dialog_lo.addWidget(QSplitter(Qt.Orientation.Vertical))
            self.dialog_lo.addWidget(QLabel(f"Upstreams : {",".join([str(cell) for cell in cell.upstream_cells])}"))
            self.dialog_lo.addWidget(QLabel(f"Property : {cell.derived_property.prop_name}"))

        self.mutable_checkbox = QCheckBox("Mutable")
        self.mutable_checkbox.setChecked(False)
        self.mutable_checkbox.stateChanged.connect(self.init_items_view)
        self.dialog_lo.addWidget(self.mutable_checkbox)

        self.init_items_view()

        self.setLayout(self.dialog_lo)

    def init_items_view(self):
        while self.dialog_lo.count():
            widget = self.dialog_lo.takeAt(0).widget()
            if widget is not None:
                widget.deleteLater()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_lo = QVBoxLayout(scroll_widget)

        for i,node in enumerate(self.cell.metanode):
            scroll_lo.addWidget(QSplitter(Qt.Orientation.Vertical))
            scroll_lo.addWidget(QLabel(f"Container : {node.container_index}"))
            scroll_lo.addWidget(QLabel(f"Node index : {i}"))
            scroll_lo.addWidget(QLabel(f"Property : {node.prop.prop_name}"))
            scroll_lo.addWidget(QLabel(f"Type : {node.address.type.type_name}"))
            if not self.mutable_checkbox.isChecked():
                scroll_lo.addWidget(QLabel(f"Value : {node.address.value}"))
            else:
                value_edit_lo = QHBoxLayout()
                value_edit_lo.addWidget(QLabel("Value : "))
                value_input = QLineEdit(node.address.value)
                value_edit_lo.addWidget(value_input)
                value_apply_btn = QPushButton("Apply")
                value_apply_btn.setMaximumWidth(65)
                value_apply_btn.clicked.connect(
                    partial(
                        self.edit_value,
                        container_index=node.container_index,
                        prop=node.prop,
                        address=node.address
                    )
                )
                value_edit_lo.addWidget(value_apply_btn)
                scroll_lo.addLayout(value_edit_lo)

        scroll_area.setWidget(scroll_widget)
        self.dialog_lo.addWidget(scroll_area)

    def edit_value(self, 
                   container_index : MSK_HexIndex,
                   prop: MSK_Property,
                   address: MSK_Address
                   ) -> None:
        print(f"container_index = {container_index}"
              f"property = {prop.prop_name}"
              f"address = {address.value}"
        )
        return
        coll = MSK_ContainerCollection(field_name=self.field_name)
        new_entity = coll.write_entity(
            container_index=container_index,
            prop=prop,
            adress=address,
            do_override=True
        )


    def set_display_nodes(self) -> None:
        if (self.cell.derived_property is None or
            self.cell.upstream_cells is None or 
            self.cell.display_nodes is None):
            return
        self.cell.display_nodes = self.display_node_input.text().strip()
        self.cell.display_form = self.display_form_input.text().strip()
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
        self.start_pos_input = QLineEdit("2") #1-start
        self.start_pos_input.setValidator(QIntValidator(bottom=1))
        iterator_lo.addWidget(self.start_pos_input, 2, 1)

        max_output_count_label = QLabel("Max. count : ")
        iterator_lo.addWidget(max_output_count_label, 3, 0)
        self.max_count_input = QLineEdit("")
        self.max_count_input.setValidator(QIntValidator(bottom=1))
        iterator_lo.addWidget(self.max_count_input, 3, 1)
        dialog_lo.addLayout(iterator_lo)

        self.sort_by_num_checkbox = QCheckBox("Sort by numbers if found")
        self.sort_by_num_checkbox.setChecked(True)
        dialog_lo.addWidget(self.sort_by_num_checkbox)

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
        iterator = [x for x in iterator if x.address.value is not None]

        def extract_number(x: str) -> str:
            numbers = re.findall(r"\d+", x)
            return int(numbers[0]) if len(numbers) == 1 else x
        if self.sort_by_num_checkbox.isChecked():
            iterator.sort(
                key=lambda x : extract_number(x.address.value)
            )
        else:
            iterator.sort(
                key=lambda x : x.address.value
            )
        if self.max_count_input.text():
            max_count = int(self.max_count_input.text())
            iterator = iterator[: max_count] if max_count <= len(iterator) else iterator

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




