import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QPushButton, QGridLayout, QScrollArea,
    QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QLabel
)
from PySide6.QtCore import QStringListModel

from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item
from shellarc_core.cloudio.io_spreadsheet import GCP_IO
from shellarc_core.cfg.spreadsheet_map_io import SpreadsheetMap_IO as SMap_IO


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Button Grid")
        self.resize(800, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QVBoxLayout(main_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        self.make_buttons()
        self.make_list()
        self.make_util_btns()

        self.selected_items_buffer = {}

        main_widget.setLayout(self.main_layout)


    def make_buttons(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(2)
        spreadsheet_cache = GCP_IO().spreadsheet_cache
        smap_io = SMap_IO()
        cfg_io = Cfg_IO()
        vert_offset = smap_io.get_vert_offset()
        spreadsheet_map = smap_io.get_spreadsheet_map_raw()

        grid.addWidget(QLabel("カット"), 0, 0)

        col = 1
        for item_name, item_idx in spreadsheet_map["items_0"].items():
            if not item_name.endswith("_progress"):
                continue
            progress_name = item_name.removesuffix("_progress")
            progress_name_jpn = cfg_io.get_cfg_setting(Cfg_item.COMPONENT, progress_name, "diaplay")
            grid.addWidget(QLabel(progress_name_jpn), 0, col)
            col += 1

        total_cut_num = len(spreadsheet_cache) - vert_offset + 1
        for row in range(1, total_cut_num):
            row_data = spreadsheet_cache[vert_offset + row - 1]
            grid.addWidget(QLabel(str(row)), row, 0)
            col = 1
            for item_name, item_idx in spreadsheet_map["items_0"].items():
                if not item_name.endswith("_progress"):
                    continue

                progress = row_data[item_idx - 1]
                btn = QPushButton(f"{row},{col}")
                btn.setFixedSize(50, 30)
                if progress == "作業中":
                    btn.setStyleSheet("background-color: yellow;")
                elif progress == "完了":
                    btn.setStyleSheet("background-color: green;")
                else:
                    btn.setStyleSheet("background-color: red;")
                    btn.setEnabled(False)

                btn.clicked.connect(
                    lambda checked=False, r=row, c=col: self.select_item_action(r, c)
                )

                grid.addWidget(btn, row, col)
                col += 1

        scroll_area.setWidget(container)
        self.main_layout.addWidget(scroll_area)

    def make_list(self):
        self.list_to_dl = QListWidget()
        self.list_to_dl.itemSelectionChanged.connect(self.list_item_selected)
        self.main_layout.addWidget(self.list_to_dl)

    def make_util_btns(self):
        container = QWidget()
        h_layout = QHBoxLayout()
        h_layout.addStretch()
        self.delete_btn = QPushButton("選択項目を削除")
        self.delete_btn.clicked.connect(self.delete_selected)
        h_layout.addWidget(self.delete_btn)
        self.delete_btn.hide()
        dl_btn = QPushButton("ダウンロード")
        dl_btn.clicked.connect(self.download_selected)
        h_layout.addWidget(dl_btn)
        reset_btn = QPushButton("リセット")
        reset_btn.clicked.connect(self.reset_selection)
        h_layout.addWidget(reset_btn)
        container.setLayout(h_layout)
        self.main_layout.addWidget(container)

    def select_item_action(self, 
                           row: int,
                           col: int):
        current_items = [self.list_to_dl.item(i).text() for i in range(0, self.list_to_dl.count())]
        item_to_add_display = f"{row}-{col}をダウンロード"
        item_to_add_internal = f"{row}-{col}_internal"
        if item_to_add_display in current_items:
            return 
        self.list_to_dl.addItem(f"{row}-{col}をダウンロード")
        self.selected_items_buffer[item_to_add_display] = item_to_add_internal

    def list_item_selected(self):
        if self.list_to_dl.selectedItems():
            self.delete_btn.show()
        else:
            self.delete_btn.hide()

    def delete_selected(self):
        selected_items = self.list_to_dl.selectedItems()
        for selected_item in selected_items:
            if selected_item.text() in self.selected_items_buffer:
                del self.selected_items_buffer[selected_item.text()]
            self.list_to_dl.takeItem(self.list_to_dl.row(selected_item))


    def download_selected(self):
        print("Hello")

    def reset_selection(self):
        self.list_to_dl.clear()




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec())
