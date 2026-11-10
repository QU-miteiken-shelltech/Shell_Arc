from typing import Optional
from ast import literal_eval
import math

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QComboBox, QPushButton, QAbstractItemView,
    QDialog, QLineEdit, QSpinBox, 
)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, 
    QColor, QPolygonF)

from shellarc_client.ui.table_ops.table_cells import (
    TableCell, CellEditDialog, HeaderEditDialog,
    BuildAbstEdgeDialog
)

from shellarc_msk.mskob.field_obj import MSK_Field
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskdn.abstract_edge import MSKDN_AbstEdge
from shellarc_msk.mskdn.hypergraph import MSKDN_Hypergraph
from shellarc_msk.mskdn.metanode import MSKDN_Metanode



class MSK_TableView(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.itemDoubleClicked.connect(self.item_double_clicked)
        self.horizontalHeader().sectionDoubleClicked.connect(self.hor_header_double_clicked)
        self.verticalHeader().sectionDoubleClicked.connect(self.vert_header_double_clicked)

        self.setRowCount(1)
        self.setColumnCount(1)
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                self.setItem(row, col, TableCell())

        self._arrow_info = []

    def change_row_num(self, new_num: int):
        original_num = self.rowCount() 
        self.setRowCount(new_num)


    def change_col_num(self, new_num: int):
        original_num = self.columnCount() 
        self.setColumnCount(new_num)


    def item_double_clicked(self, clicked_item):
        print(clicked_item)
        CellEditDialog(cell=clicked_item).exec()

    def vert_header_double_clicked(self, logical_index):
        HeaderEditDialog(
            logical_index=logical_index,
            is_vertical=True,
            table=self,
            parent=self
        ).exec()

    def hor_header_double_clicked(self, logical_index):
        HeaderEditDialog(
            logical_index=logical_index,
            is_vertical=False,
            table=self,
            parent=self
        ).exec()

    def _cell_at(self, pos):
        index = self.indexAt(pos)
        if not index.isValid():
            return None
        return index.column(), index.row()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            cell = self._cell_at(pos)
            if cell is not None:
                self._arrow_info.append(
                    (pos, pos, cell)
                )
        super().mousePressEvent(event)  

    def mouseMoveEvent(self, event):
        if self._arrow_info:
            self._arrow_info[-1] = (
                self._arrow_info[-1][0],
                event.position().toPoint(),
                self._arrow_info[-1][2]
            )
            self.viewport().update()  
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._arrow_info:
            start_cell = self._arrow_info[-1][2]
            end_cell = self._cell_at(event.position().toPoint())
            is_sameendpos = (
                end_cell == self._cell_at(self._arrow_info[len(self._arrow_info) - 2][1])
                if len(self._arrow_info) > 1 
                else True
            )
            is_samestartpos = (
                start_cell == self._cell_at(self._arrow_info[len(self._arrow_info) - 2][0])
                if len(self._arrow_info) > 1 
                else False
            )
            if (end_cell is None or 
                start_cell == end_cell or 
                not is_sameendpos or
                is_samestartpos):
                self._arrow_info.pop(-1)
                self.viewport().update()
        super().mouseReleaseEvent(event)

    def link_table_cell(self,
                        arrow_info: dict[str, list]
                        ) -> None:
        def link_cell(target_prop: MSK_Property, 
                      upstream_cells: list[tuple[int, int]],
                      derivitive_cell: tuple[int, int]
                      ):
            print(upstream_cells)
            abst_edge = hypergraph.get_abstract_edge(
                upstream_metanodes=[
                    self.item(p[1], p[0]).metanode 
                    for p in upstream_cells 
                    if p is not None],
                target_prop=target_prop,
                max_count=10
            )
            self.setItem(
                derivitive_cell[1],
                derivitive_cell[0],
                TableCell(
                    field_name=field_name, 
                    metanode=abst_edge.derivitive,
                    upstream_cells=upstream_cells,
                    derived_property=target_prop
                )
            )

        field_name = self.parentWidget().field_name
        hypergraph = MSKDN_Hypergraph(field_name=field_name)
        if len(arrow_info["upstreams"]) > 1:
            build_abst_edge_dialog = BuildAbstEdgeDialog(self)
            result = build_abst_edge_dialog.exec()
            if result == QDialog.DialogCode.Accepted:
                target_prop = build_abst_edge_dialog.get_abst_edge()
                link_cell(
                    target_prop=target_prop, 
                    upstream_cells=arrow_info["upstreams"],
                    derivitive_cell=arrow_info["derivitive"][0]
                )
        elif len(arrow_info["upstreams"]) == 1:
            if arrow_info["upstreams"][0] is None:
                return
            original_item = self.item(
                arrow_info["upstreams"][0][1],
                arrow_info["upstreams"][0][0]
            )
            target_prop = original_item.derived_property
            upstream_cells = original_item.upstream_cells
            if target_prop is None or upstream_cells is None:
                return
            c1, c2 = arrow_info["upstreams"][0][0], arrow_info["derivitive"][0][0]
            r1, r2 = arrow_info["upstreams"][0][1], arrow_info["derivitive"][0][1]
            print("******")
            for col in range(min(c1, c2), max(c1, c2) + 1):
                for row in range(min(r1, r2), max(r1, r2) + 1):
                    my_upstream_cells = [
                        (
                            cell[0] if cell[0] != arrow_info["upstreams"][0][0] else col,
                            cell[1] if cell[1] != arrow_info["upstreams"][0][1] else row,
                        ) for cell in upstream_cells
                    ]
                    link_cell(
                        target_prop=target_prop, 
                        upstream_cells=my_upstream_cells,
                        derivitive_cell=(col, row)
                    )
                    # except Exception as e:
                    #     print(f"Link cell failed : col{col} row{row} due to error : {e}")
                    #     continue
            print("******")
        else:
            return

        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return and self._arrow_info:
            arrow_info = {
                "upstreams" : [], # list[tuple[int, int]]
                "derivitive" : [] # list[tuple[int, int]]
            }
            for arrow in self._arrow_info:
                arrow_info["upstreams"].append(arrow[2])
            arrow_info["derivitive"].append(self._cell_at(self._arrow_info[-1][1]))
            
            self.link_table_cell(arrow_info=arrow_info)

            self._arrow_info.clear()
            self.viewport().update()
            # try:
            #     self.link_table_cell(arrow_info=arrow_info)
            # except Exception as e:
            #     print(e)
            # finally:
            #     self._arrow_info.clear()
            #     self.viewport().update()
            #     super().keyPressEvent(event)
        elif event.key() == Qt.Key.Key_Escape and self._arrow_info:
            self._arrow_info.clear()
            self.viewport().update()
        super().keyPressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event) 
        if not self._arrow_info:
            return

        for arrow in self._arrow_info:
            p1 = QPointF(arrow[0])
            p2 = QPointF(arrow[1])
            if p1 == p2:
                return

            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            color = QColor("blue")
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color))

            painter.drawLine(p1, p2)
            angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
            size = 12
            left = QPointF(p2.x() - size * math.cos(angle - math.pi / 6),
                        p2.y() - size * math.sin(angle - math.pi / 6))
            right = QPointF(p2.x() - size * math.cos(angle + math.pi / 6),
                            p2.y() - size * math.sin(angle + math.pi / 6))
            painter.drawPolygon(QPolygonF([p2, left, right]))
            painter.end()


class TableOpsUi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lo = QVBoxLayout(self)
        self.field_combo = QComboBox()
        self.field_combo.clear()
        self.field_combo.addItems(MSK_Field.field_names())
        self.field_combo.currentIndexChanged.connect(self.switch_field)
        self.switch_field()
        self.lo.addWidget(self.field_combo)

        rowcol_num_lo = QHBoxLayout()
        rowcol_num_lo.setAlignment(Qt.AlignmentFlag.AlignLeft)
        row_num_label = QLabel("Row : ")
        row_num_label.setFixedWidth(80)
        rowcol_num_lo.addWidget(row_num_label)
        self.row_num_spin = QSpinBox()
        self.row_num_spin.setMinimum(1)
        self.row_num_spin.setMaximum(1000)
        self.row_num_spin.setFixedWidth(80)
        self.row_num_spin.valueChanged.connect(self.change_row_num)
        rowcol_num_lo.addWidget(self.row_num_spin)

        col_num_label = QLabel("Column : ")
        col_num_label.setFixedWidth(80)
        rowcol_num_lo.addWidget(col_num_label)
        self.col_num_spin = QSpinBox()
        self.col_num_spin.setMinimum(1)
        self.col_num_spin.setMaximum(1000)
        self.col_num_spin.setFixedWidth(80)
        self.col_num_spin.valueChanged.connect(self.change_col_num)
        rowcol_num_lo.addWidget(self.col_num_spin)
        self.lo.addLayout(rowcol_num_lo)

        self.msk_table_view = MSK_TableView()
        self.lo.addWidget(self.msk_table_view)
        self.setLayout(self.lo)

    def switch_field(self):
        new_field_name = self.field_combo.currentText()
        current_field = MSK_Field(field_name=new_field_name)
        self.field_members = [p for p in current_field.field_ls]
        self.field_name = new_field_name

    def change_row_num(self, new_val):
        self.msk_table_view.change_row_num(new_num=new_val)

    def change_col_num(self, new_val):
        self.msk_table_view.change_col_num(new_num=new_val)