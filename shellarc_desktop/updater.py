from pathlib import Path
import os
import datetime
import json

from PySide6.QtWidgets import (
    QDialog, QLabel, QPushButton, 
    QVBoxLayout, QCheckBox
)

from shellarc_core.cloudio.io_r2 import R2_IO

class AskRestartDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("再起動してください")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"アップデートが成功しました\nShellArc Desktopを再起動してください"))
        self.setLayout(layout)

class UpdateWindow(QDialog):
    def __init__(self,
                 update_available_status: int):
        super().__init__()
        self.setWindowTitle("アップデート")
        self.resize(400, 200)
        self.update_file_paths = R2_IO().get_paths_with_prefix(file_prefix="update/desktop_updates")

        main_layout = QVBoxLayout(self)

        main_layout.addWidget(QLabel("最新版がリリースされました\nアップデートしますか"))
        if update_available_status == 2:
            urgent_notice = QLabel("重大な修正アップデートです")
            urgent_notice.setStyleSheet("color: red")
            main_layout.addWidget(urgent_notice)
        main_layout.addStretch()

        self.delete_old_checkbox = QCheckBox("旧バージョンを削除")
        self.delete_old_checkbox.setChecked(True)
        main_layout.addWidget(self.delete_old_checkbox)

        update_btn = QPushButton("アップデート")
        update_btn.setStyleSheet("background-color: #4288C6")
        update_btn.clicked.connect(self.do_update)
        main_layout.addWidget(update_btn)

        dismiss_btn = QPushButton("辞退")
        dismiss_btn.clicked.connect(self.dismiss_update)
        main_layout.addWidget(dismiss_btn)


    def do_update(self):
        download_destination = Path(__file__).resolve().parent
        r2_io = R2_IO()
        for update_path in self.update_file_paths:
            script_name = update_path.split("/")[-1]
            if not script_name:
                continue
            current_script = download_destination / script_name
            if current_script.exists() and not self.delete_old_checkbox.isChecked():
                renamed_name = f"{current_script.stem}_old{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}{current_script.suffix}"
                os.rename(download_destination / script_name, download_destination / renamed_name)
            r2_io.download_file(
                to_download_file=update_path,
                download_destination=str(download_destination),
                file_naming=str(script_name)
            )
        self.accept()

    def dismiss_update(self):
        download_destination = Path(__file__).resolve().parent
        R2_IO().download_file(
            to_download_file="update/desktop_update/update_info.json",
            download_destination=str(download_destination),
            file_naming="update_info.json"
        )
        self.reject()

    @staticmethod
    def check_available_update() -> int:
        r2_io = R2_IO()
        update_file_paths = r2_io.get_paths_with_prefix(file_prefix="update/desktop_update/update_info.json")
        if update_file_paths is None:
            return 0
        
        download_destination = Path(__file__).resolve().parent
        update_log_file = download_destination / "update_info.json"
        if update_file_paths.exists():
            with open(update_log_file, "r", encoding="utf-8") as f:
                update_num = json.load(f).get("index", "0")
        else:
             update_num = None
        r2_io.download_file(
            to_download_file="update/desktop_updates/update_info.json",
            download_destination=str(download_destination),
            file_naming="update_info_tmp.json"
        )
        with open(download_destination / "update_info_tmp.json", "r", encoding="utf-8") as f:
            server_update_num = json.load(f).get("index", "0")
        os.unlink(download_destination / "update_info_tmp.json")
        if str(update_num) == str(server_update_num):
            return 0
        
        is_urgent = r2_io.get_paths_with_prefix(file_prefix="update/desktop_updates/urgent") is not None
        return 2 if is_urgent else 1