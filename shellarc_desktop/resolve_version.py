from PySide6.QtWidgets import (
    QDialog, QWidget, QLabel, 
    QPushButton, QGridLayout, QVBoxLayout
)

from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item
from shellarc_core.cloudio.io_r2 import R2_IO

class ResolveWindow(QDialog):
    def __init__(self,
                 version_list: list,
                 file_prefix: str,
                 download_destination: str):
        super().__init__()
        self.setWindowTitle("バージョン処理")
        self.resize(400, 200)

        main_layout = QVBoxLayout(self)

        file_prefix = file_prefix.split("/")[-1]
        cut_num = file_prefix.split("_")[0].lstrip("cut")
        component = Cfg_IO().get_cfg_setting(Cfg_item.COMPONENT, file_prefix.split("_")[1], 'diaplay')
        main_layout.addWidget(QLabel(f"カット{cut_num} {component} は複数バージョンを持ちます\nどれにするかを選択してください : "))
        main_layout.addStretch()

        grid_layout = QGridLayout()
        grid_layout.addWidget(QLabel("提出時間"), 0, 0)
        grid_layout.addWidget(QLabel("ファイル名"), 0, 1)
        grid_layout.addWidget(QLabel("ダウンロード選択"), 0, 2)
        
        row = 1
        for version in version_list:
            timemark = version.split("/")[-1].split("_")[-1].split(".")[0]
            print(version)
            s = str(timemark)
            formatted_timemark = f"{s[0:4]}/{s[4:6]}/{s[6:8]} {s[8:10]}:{s[10:12]}:{s[12:14]}"

            select_btn = QPushButton("これにする")
            select_btn.clicked.connect(
                lambda checked=False,
                r2_path=version,
                download_destination=download_destination,
                btn_self=select_btn
                : self.version_selected(
                    r2_path=r2_path,
                    download_destination=download_destination,
                    btn_self=btn_self
                )
            )
            if row == 1:
                select_btn.setStyleSheet("border: 2px solid #007bff;")
            
            grid_layout.addWidget(QLabel(formatted_timemark), row, 0)
            grid_layout.addWidget(QLabel(version), row, 1)
            grid_layout.addWidget(select_btn, row, 2)

            row += 1

        main_layout.addLayout(grid_layout)
        main_layout.addStretch()

        go_next_btn = QPushButton("次へ")
        go_next_btn.clicked.connect(self.accept)
        main_layout.addWidget(go_next_btn)

    def version_selected(self,
                         r2_path: str,
                         download_destination: str,
                         btn_self: QPushButton):
        R2_IO().download_file(
            to_download_file=r2_path,
            download_destination=download_destination,
            file_naming=r2_path.split("/")[-1]
        )
        btn_self.setText("DL済み")
        btn_self.setStyleSheet("background-color: red;")
        btn_self.setEnabled(False)

