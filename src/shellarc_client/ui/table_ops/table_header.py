from typing import Optional, TYPE_CHECKING

from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QDialog, 
    QLineEdit, QPushButton, QGridLayout,
    QComboBox, QCheckBox
)
from PySide6.QtGui import QIntValidator

from shellarc_msk.mskdn.metanode import MSKDN_Metanode
from shellarc_msk.mskdn.node import MSKDN_VNode
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.entity_obj import MSK_Entity
from shellarc_client.ui.table_ops.table_cells import TableCell
from shellarc_engine.mskio import read_msk
from shellarc_engine.tables import table_capture

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

        step_label = QLabel("Step : ")
        iterator_lo.addWidget(step_label, 4, 0)
        self.step_input = QLineEdit("1")
        self.step_input.setValidator(QIntValidator(bottom=1))
        iterator_lo.addWidget(self.step_input, 4, 1)

        repetition_label = QLabel("Repetition : ")
        iterator_lo.addWidget(repetition_label, 5, 0)
        self.repetition_input = QLineEdit("1")
        self.repetition_input.setValidator(QIntValidator(bottom=1, top=600))
        iterator_lo.addWidget(self.repetition_input, 5, 1)
        dialog_lo.addLayout(iterator_lo)

        self.sort_by_num_checkbox = QCheckBox("Sort by numbers if found")
        self.sort_by_num_checkbox.setChecked(True)
        dialog_lo.addWidget(self.sort_by_num_checkbox)

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_header)
        dialog_lo.addWidget(apply_btn)

        self.setLayout(dialog_lo)

    def apply_header(self):
        repetition = int(self.repetition_input.text())
        start_pos = int(self.start_pos_input.text()) - 1 if self.start_pos_input.text() else 0
        max_count = int(self.max_count_input.text()) if self.max_count_input.text() else None
        key_property = self.parentWidget().parentWidget().field_members[self.property_combo.currentIndex()][0]
        step = int(self.step_input.text()) if self.step_input.text() else 1
        do_sort_by_num=self.sort_by_num_checkbox.isChecked()
        header_builder = BuildHeader(
            field_name=self.field_name,
            table=self.table,
            is_vertical=self.is_vertical
        )
        iterator = header_builder.solve_header(
            key_property=key_property,
            max_count=max_count,
            do_sort_by_num=do_sort_by_num
        )
        initial_start_pos = start_pos
        for _ in range(repetition):
            next_start_pos = header_builder.write_header(
                header_pos=self.logical_index,
                start_pos=start_pos,
                step=step,
                iterator=iterator
            )
            start_pos = next_start_pos
        table_capture.set_header(
            is_vertical=self.is_vertical,
            header_pos=self.logical_index,
            repetition=repetition,
            start_pos=initial_start_pos + 1,
            max_count=max_count,
            step=step,
            key_property=self.property_combo.currentText(),
            do_sort_by_num=do_sort_by_num
        )
        self.accept()

class BuildHeader:
    def __init__(self, 
                 field_name: str, 
                 table, 
                 is_vertical: bool):
        self.field_name = field_name
        self.table = table
        self.is_vertical = is_vertical

    def solve_header(self,
                     key_property: MSK_Property,
                     max_count: Optional[int]=None,
                     do_sort_by_num: bool=True
                     ) -> list[MSK_Entity]:
        iterator = read_msk.get_entities_by_property(
            target_field_name=self.field_name,
            requested_property=key_property,
            eluminate_duplication=True,
            eluminate_none=True,
            sort_flag=2 if do_sort_by_num else 1
        )
        if max_count is not None:
            iterator = iterator[: max_count] if max_count <= len(iterator) else iterator
        return iterator

    def write_header(self, 
                     header_pos: int,
                     start_pos: int, 
                     step: int,
                     iterator: list[MSK_Entity]
                     ) -> int:
        writing_pos = start_pos
        if self.is_vertical:
            current_col_num = self.table.columnCount()
            if current_col_num < start_pos + len(iterator):
                self.table.setColumnCount(start_pos + len(iterator) * step)
                for col in range(0, len(iterator)):
                    writing_pos = start_pos + (col * step)
                    metanode = MSKDN_Metanode(
                        iterable=[MSKDN_VNode(entity=iterator[col])]
                    )
                    cell = TableCell(
                        field_name=self.field_name,
                        metanode=metanode
                    )
                    self.table.setItem(header_pos, writing_pos, cell)
            self.table.header_pos["rows"].append(header_pos)
        else:
            current_row_num = self.table.rowCount()
            if current_row_num < start_pos + len(iterator):
                self.table.setRowCount(start_pos + len(iterator) * step)
                for row in range(0, len(iterator)):
                    writing_pos = start_pos + (row * step)
                    metanode = MSKDN_Metanode(
                        iterable=[MSKDN_VNode(entity=iterator[row])]
                    )
                    cell = TableCell(
                        field_name=self.field_name,
                        metanode=metanode
                    )
                    self.table.setItem(writing_pos, header_pos, cell)
            self.table.header_pos["cols"].append(header_pos)
        return writing_pos + step