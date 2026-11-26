import shutil

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QDialog, QGroupBox, 
    QFileDialog, QMessageBox, QScrollArea, 
    QSplitter
)
from PySide6.QtCore import Slot, Qt

from shellarc_msk.mskob.container_obj import MSK_Container
from shellarc_msk.mskob.hexindex_obj import MSK_HexIndex
from shellarc_client.ui.task_ops.task_display_chip import TaskDisplayChip
from shellarc_client.ui.task_ops.task_register_dialog import RegisterTaskDialog
from shellarc_client.ui.task_ops.call_dialog import TaskCallDialog
from shellarc_engine.mount import mount_file_manager
from shellarc_engine.config.read_config import ReadClientConfig


class TaskOpsUi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lo = QVBoxLayout(self)
        self.setLayout(self.lo)

    def build_ui(self):
        while self.lo.count():
            widget = self.lo.takeAt(0).widget()
            if widget is not None:
                widget.deleteLater()

        scan_lo = QHBoxLayout()
        scan_lo.addStretch()
        reload_btn = QPushButton("Reload")
        reload_btn.setFixedWidth(60)
        reload_btn.clicked.connect(self.build_ui)
        scan_lo.addWidget(reload_btn)
        scan_btn = QPushButton("Scan")
        scan_btn.setFixedWidth(60)
        scan_btn.clicked.connect(self.scan_mount_dir)
        scan_lo.addWidget(scan_btn)
        import_btn = QPushButton("Import")
        import_btn.setFixedWidth(60)
        import_btn.clicked.connect(self.import_to_mount)
        scan_lo.addWidget(import_btn)
        self.lo.addLayout(scan_lo)

        mount_file_info = mount_file_manager.get_mount_file_info()
        group_splitter = QSplitter(Qt.Orientation.Vertical)

        tracking_gp = QGroupBox("Tracking")
        tracking_gp_outer_lo = QVBoxLayout(tracking_gp)
        tracking_scroll_area = QScrollArea()
        tracking_scroll_area.setWidgetResizable(True)
        tracking_gp_outer_lo.addWidget(tracking_scroll_area)
        tracking_scroll_widget = QWidget()
        tracking_gp_lo = QVBoxLayout(tracking_scroll_widget)
        tracking_scroll_area.setWidget(tracking_scroll_widget)
        for file_path, file_info in mount_file_info.get("tracking", {}).items():
            task_display_item = TaskDisplayChip(
                file_path=file_path,
                affiliated_container=MSK_Container(
                    field_name=ReadClientConfig.get_config_item("file_linkage", "record_field"),
                    container_index=MSK_HexIndex(file_info.get("affiliation", None))
                ),
                display_type=TaskDisplayChip.TaskDisplayType.STAGED_ZONE,
                allow_custom_tag=True,
                master_ui_widget=self
            )
            tracking_gp_lo.addWidget(task_display_item)
            task_display_item.mount_status_changed_sig.connect(self.mount_status_changed)
        tracking_gp_lo.addStretch()
        group_splitter.addWidget(tracking_gp)

        detected_gp = QGroupBox("Detected")
        detected_gp_outer_lo = QVBoxLayout(detected_gp)
        detected_scroll_area = QScrollArea()
        detected_scroll_area.setWidgetResizable(True)
        detected_gp_outer_lo.addWidget(detected_scroll_area)
        detected_scroll_widget = QWidget()
        detected_gp_lo = QVBoxLayout(detected_scroll_widget)
        detected_scroll_area.setWidget(detected_scroll_widget)
        for file_path in mount_file_info.get("detected", []):
            task_display_item = TaskDisplayChip(
                file_path=file_path,
                affiliated_container=None,
                display_type=TaskDisplayChip.TaskDisplayType.DETECTED_ZONE,
                allow_custom_tag=True
            )
            task_display_item.mount_status_changed_sig.connect(self.mount_status_changed)
            detected_gp_lo.addWidget(task_display_item)
        detected_gp_lo.addStretch()
        group_splitter.addWidget(detected_gp)

        untracked_gp = QGroupBox("Untracked")
        untracked_gp_outer_lo = QVBoxLayout(untracked_gp)
        untracked_scroll_area = QScrollArea()
        untracked_scroll_area.setWidgetResizable(True)
        untracked_gp_outer_lo.addWidget(untracked_scroll_area)
        untracked_scroll_widget = QWidget()
        untracked_gp_lo = QVBoxLayout(untracked_scroll_widget)
        untracked_scroll_area.setWidget(untracked_scroll_widget)
        for file_path in mount_file_info.get("untracked", []):
            task_display_item = TaskDisplayChip(
                file_path=file_path,
                affiliated_container=None,
                display_type=TaskDisplayChip.TaskDisplayType.UNSTAGED_ZONE,
                allow_custom_tag=True
            )
            untracked_gp_lo.addWidget(task_display_item)
            task_display_item.mount_status_changed_sig.connect(self.mount_status_changed)
        untracked_gp_lo.addStretch()
        group_splitter.addWidget(untracked_gp)

        group_splitter.setSizes([1, 1, 1])
        self.lo.addWidget(group_splitter)

    def scan_mount_dir(self):
        mount_info = mount_file_manager.scan_mounted_dir()
        if not mount_info["detected"]:
            QMessageBox.information(
                self, 
                "Up to date", 
                "No edited or new items detected in the mount directory"
            )
        else:
            result = RegisterTaskDialog(mount_info=mount_info, parent=self).exec()
            if result == QDialog.DialogCode.Accepted or result == QDialog.DialogCode.Rejected:
                self.build_ui()

    def import_to_mount(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select a file", "", "Any file (*)")
        if not filename:
            return
        mount_file_manager.copy_to_mount(src_filepath=filename)
        self.scan_mount_dir()

    @Slot(str, str, object)
    def mount_status_changed(self, 
                             operation_type: str, 
                             file_path: str, 
                             affiliation: MSK_Container | None
                             ) -> None:
        try:
            if operation_type == "TRACK":
                mount_file_manager.write_file_status(
                    info={"detected": [file_path]}
                ) 
                self.scan_mount_dir()
            elif operation_type == "UNTRACK":
                mount_file_manager.write_file_status(
                    info={"untracked": [file_path]}
                ) 
            elif operation_type == "REMOVE":
                ignored_dir = mount_file_manager.mounted_dir / "ignore"
                if not ignored_dir.exists():
                    ignored_dir.mkdir(parents=True, exist_ok=False)
                shutil.copy2(file_path, ignored_dir)
                mount_file_manager.write_file_status(
                    info={"remove": [file_path]}
                ) 
            elif operation_type == "CALL":
                if affiliation is None:
                    raise ValueError(
                        "Files without an affiliated MSK_Container is not subjected to MSK Call Operation "
                    )
                TaskCallDialog(
                    affiliation=affiliation,
                    file_path=file_path,
                    parent=self
                ).exec()
            else:
                raise ValueError("Unknown operation type")
        except Exception as e:
            print(e)
        finally:
            if operation_type != "TRACK":
                self.build_ui()

