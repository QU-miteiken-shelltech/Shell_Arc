from typing import Optional
import math

from PySide6.QtWidgets import (
    QTableWidget, QAbstractItemView, QDialog
)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, 
    QColor, QPolygonF)

from shellarc_client.ui.table_ops.table_cells import (
    TableCell, CellEditDialog, HeaderEditDialog,
    BuildAbstEdgeDialog
)

from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskdn.hypergraph import MSKDN_Hypergraph


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

        self.header_pos = {"rows": [], "cols": []}
        self._arrow_info = []

    def item_double_clicked(self, clicked_item):
        print(clicked_item)
        cell_edit_dialog = CellEditDialog(cell=clicked_item)
        cell_edit_dialog.exec()
        cell_edit_dialog.set_display_nodes()

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

    def link_cell(self,
                  field_name: str,
                  target_prop: MSK_Property, 
                  upstream_cells: list[tuple[int, int]],
                  derivitive_cell: tuple[int, int],
                  max_metanode_num: int,
                  display_form: Optional[str]=None,
                  display_nodes: Optional[str]=None
                  ) -> None:
        hypergraph = MSKDN_Hypergraph(field_name=field_name)
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
                derived_property=target_prop,
                max_metanode_num=max_metanode_num,
                display_form=display_form,
                display_nodes=display_nodes
            )
        )

    def link_table_cells(self,
                         arrow_info: dict[str, list]
                         ) -> None:
        field_name = self.parentWidget().field_name
        if len(arrow_info["upstreams"]) > 1:
            build_abst_edge_dialog = BuildAbstEdgeDialog(self)
            result = build_abst_edge_dialog.exec()
            if result == QDialog.DialogCode.Accepted:
                target_prop = build_abst_edge_dialog.get_abst_edge()
                max_metanode_num = build_abst_edge_dialog.get_max_length()
                self.link_cell(
                    field_name= field_name,
                    target_prop=target_prop, 
                    upstream_cells=arrow_info["upstreams"],
                    derivitive_cell=arrow_info["derivitive"][0],
                    max_metanode_num=max_metanode_num
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
            max_metanode_num = original_item.max_metanode_num
            display_nodes = original_item.display_nodes
            display_form = original_item.display_form
            if target_prop is None or upstream_cells is None:
                return
            c1, c2 = arrow_info["upstreams"][0][0], arrow_info["derivitive"][0][0]
            r1, r2 = arrow_info["upstreams"][0][1], arrow_info["derivitive"][0][1]

            for col in range(min(c1, c2), max(c1, c2) + 1):
                for row in range(min(r1, r2), max(r1, r2) + 1):
                    my_upstream_cells = []
                    for upstream_cell in upstream_cells:
                        if (upstream_cell[0] in self.header_pos["cols"] and
                            upstream_cell[1] in self.header_pos["rows"]):
                            raise ValueError("Upstream cell is inside overlapping headers")
                        if upstream_cell[0] in self.header_pos["cols"]:
                            my_upstream_col = upstream_cell[0]
                            row_offset = upstream_cell[1] - arrow_info["upstreams"][0][1]
                            my_upstream_row = row + row_offset
                        if upstream_cell[1] in self.header_pos["rows"]:
                            my_upstream_row = upstream_cell[1]
                            col_offset = upstream_cell[0] - arrow_info["upstreams"][0][0]
                            my_upstream_col = col + col_offset
                        my_upstream_cells.append((my_upstream_col, my_upstream_row))
                    # my_upstream_cells = [
                    #     (
                    #         cell[0] if cell[0] != arrow_info["upstreams"][0][0] else col,
                    #         cell[1] if cell[1] != arrow_info["upstreams"][0][1] else row,
                    #     ) for cell in upstream_cells
                    # ]
                    try:
                        self.link_cell(
                            field_name=field_name,
                            target_prop=target_prop, 
                            upstream_cells=my_upstream_cells,
                            derivitive_cell=(col, row),
                            max_metanode_num=max_metanode_num,
                            display_form=display_form,
                            display_nodes=display_nodes
                        )
                    except Exception as e:
                        print(f"Link cell failed : col{col} row{row} due to error : {e}")
                        continue
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
            try:
                self.link_table_cells(arrow_info=arrow_info)
            except Exception as e:
                print(e)
            finally:
                self._arrow_info.clear()
                self.viewport().update()
                super().keyPressEvent(event)
                return
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