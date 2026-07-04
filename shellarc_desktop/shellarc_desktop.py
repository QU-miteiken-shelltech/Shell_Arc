import sys
import re
import requests
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QPushButton, QGridLayout, QScrollArea,
    QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QLabel, QCheckBox,
    QFileDialog, QDialog
)
from PySide6.QtCore import QStringListModel

from shellarc_core.cloudio.io_r2 import R2_IO
from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item
from shellarc_core.cloudio.io_spreadsheet import GCP_IO
from shellarc_core.cfg.spreadsheet_map_io import SpreadsheetMap_IO as SMap_IO

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.append(str(Path(__file__).resolve().parent))
from resolve_version import ResolveWindow

class DownloadReportDialog(QDialog):
    def __init__(self,
                 fail_list: list,
                 download_destination: str):
        super().__init__()
        self.setWindowTitle("ダウンロード結果")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"{download_destination} にダウンロードしました"))
        if not fail_list:
            layout.addWidget(QLabel("全ファイルダウンロード成功"))
        else:
            for failed_item in fail_list:
                layout.addWidget(QLabel(f"{failed_item} が存在しません"))
        self.setLayout(layout)

class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ShellArc Desktop")
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
        self.fail_list = []

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
                progress_name = item_name.removesuffix("_progress")

                progress = row_data[item_idx - 1]
                btn = QPushButton(f"{row}-{cfg_io.get_cfg_setting(Cfg_item.COMPONENT, progress_name, 'diaplay')}")
                btn.setFixedSize(85, 35)
                if progress == "作業中":
                    if f"{progress_name}_PIC" in spreadsheet_map["items_0"]:
                        person = row_data[spreadsheet_map["items_0"][f"{progress_name}_PIC"] - 1]
                    else:
                        person = " "
                    btn.setText(person)
                    btn.setStyleSheet("background-color: #f9dc5c;")
                elif progress == "完了":
                    if f"{progress_name}_PIC" in spreadsheet_map["items_0"]:
                        person = row_data[spreadsheet_map["items_0"][f"{progress_name}_PIC"] - 1]
                    else:
                        person = " "
                    btn.setText(person)
                    btn.setStyleSheet("background-color: #81b29a;")
                else:
                    btn.setStyleSheet("background-color: #ff8b94;")
                    btn.setEnabled(False)

                btn.clicked.connect(
                    lambda checked=False,
                    cut=row,
                    progress=progress_name
                    : self.select_item_action(
                        cut=cut,
                        progress=progress)
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
        self.latest_only_checkbox = QCheckBox("最新のみ")
        h_layout.addWidget(self.latest_only_checkbox)
        self.latest_only_checkbox.setChecked(True)
        container.setLayout(h_layout)
        self.main_layout.addWidget(container)

    def select_item_action(self,
                           cut: int, 
                           progress: str):
        current_items = [self.list_to_dl.item(i).text() for i in range(0, self.list_to_dl.count())]
        cfg_io = Cfg_IO()
        item_to_add_display = f"カット{cut} - {cfg_io.get_cfg_setting(Cfg_item.COMPONENT, progress, 'diaplay')}"
        if progress != "layout":
            item_to_add_internal = f"{cfg_io.get_cfg_setting(Cfg_item.COLL_NAME)}/stage/cut{cut}_{progress}"
        else:
            item_to_add_internal = f"storyboard/cut{cut}.png"
        if item_to_add_display in current_items:
            return 
        self.list_to_dl.addItem(item_to_add_display)
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
        current_items = [self.list_to_dl.item(i) for i in range(0, self.list_to_dl.count())]
        if not current_items:
            return
        file_dialog = QFileDialog()
        file_dialog.setDirectory(str(Path.home() / "Downloads"))
        download_destination = file_dialog.getExistingDirectory(self, "フォルダ選択")
        if not download_destination:
            return
        for item in current_items:
            file_prefix = self.selected_items_buffer[item.text()]
            print(f"START : {file_prefix}")
            try:
                if not file_prefix.startswith("storyboard"):
                    self._dl_from_r2(
                        file_prefix=file_prefix,
                        download_destination=download_destination
                        )
                else:
                    self._dl_storyboard(
                        r2_path=file_prefix,
                        download_destination=download_destination
                        )
            except:
                continue
            print(file_prefix)
        self.list_to_dl.clear()
        DownloadReportDialog(
            fail_list=self.fail_list,
            download_destination=download_destination
        ).exec()
        self.fail_list = []

    def reset_selection(self):
        self.list_to_dl.clear()

    def _dl_from_r2(self,
                    file_prefix: str,
                    download_destination: str):
        r2_io = R2_IO()
        paths = r2_io.get_paths_with_prefix(file_prefix=file_prefix)
        if paths is None:
            self.fail_list.append(file_prefix)
            return
        def extract_timemark(paths):
                match = re.search(r"_(\d+)\.[^.]+$", paths)
                if match:
                    return int(match.group(1))
                return -1 
        if len(paths) > 1 and not self.latest_only_checkbox.isChecked():
            ResolveWindow(
                version_list=sorted(paths, key=extract_timemark, reverse=True),
                file_prefix=file_prefix,
                download_destination=download_destination
            ).exec()
        else:
            latest_path = max(paths, key=extract_timemark)
            r2_io.download_file(
                to_download_file=latest_path,
                download_destination=download_destination,
                file_naming=latest_path.split("/")[-1]
            )

    def _dl_storyboard(self,
                       r2_path: str,
                       download_destination: str):
        url_prefix = Cfg_IO().get_cfg_setting(Cfg_item.STORYBOARD_URL)
        image_url = f"{url_prefix}/{r2_path}"
        response = requests.get(image_url)
        if response.status_code != 200:
            self.fail_list.append(r2_path)
            return
        with open(Path(download_destination) / f"layout_{r2_path.split('/')[-1]}", "wb") as f:
            f.write(response.content)
        




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec())
