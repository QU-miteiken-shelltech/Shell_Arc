from typing import Optional
from enum import StrEnum

from PySide6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout,
    QVBoxLayout, QLabel, QPushButton,
    QFileDialog
)
from PySide6.QtGui import QMouseEvent, QDesktopServices
from PySide6.QtCore import Signal, Qt, QUrl, Slot

from shellarc_msk.mskob.container_obj import MSK_Container
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.type_obj import MSK_Type
from shellarc_client.engine.config.read_config import ReadClientConfig
from shellarc_client.engine.mount import mount_file_manager

class FileHyperline(QLabel):
    file_hyperlink_clicked = Signal(str)

    def __init__(self, text: str, file_path: str, parent=None):
        super().__init__(text=text, parent=parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.file_path = file_path

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.file_hyperlink_clicked.emit(self.file_path)
        super().mouseDoubleClickEvent(event)


class TaskDisplayChip(QWidget):
    mount_status_changed_sig = Signal(str, str, object) 
    # Operation(= CALL, TRACK, UNTRACK, REMOVE), file_path, affiliation

    class TaskDisplayType(StrEnum):
        STAGED_ZONE = "staged_zone"
        DETECTED_ZONE = "detected_zone"
        UNSTAGED_ZONE = "unstaged_zone"
        UNBINDED_ZONE = "unbinded_zone"

    def __init__(self, 
                 file_path: str,
                 affiliated_container: MSK_Container | None,
                 display_type: TaskDisplayType,
                 allow_custom_tag: bool=True,
                 parent=None):
        super().__init__(parent=parent)
        self.affiliated_container = affiliated_container
        self.file_path = file_path
        if affiliated_container is None and display_type == self.TaskDisplayType.STAGED_ZONE:
            raise ValueError("An affiliated container must be designated in order to build a staged zone chip")
        
        container_frame = QFrame()
        container_frame.setFrameShape(QFrame.Shape.StyledPanel)
        container_frame.setFrameShadow(QFrame.Shadow.Sunken)
        container_frame.setLineWidth(2)

        chip_lo = QVBoxLayout(container_frame)

        operation_lo = self.switch_ui(display_type=display_type)
        chip_lo.addLayout(operation_lo)

        if allow_custom_tag:
            self.custom_tag_lo = QHBoxLayout()
            add_custom_tag_btn = QPushButton("Tag >") 
            add_custom_tag_btn.setFixedWidth(55)
            add_custom_tag_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28A745;
                    color: white;
                    border-radius: 60px;
                }
            """)
            self.custom_tag_lo.addWidget(add_custom_tag_btn)
            chip_lo.addLayout(self.custom_tag_lo)

        self.setLayout(chip_lo)

    def switch_ui(self, display_type: TaskDisplayType) -> QHBoxLayout:
        if display_type == self.TaskDisplayType.STAGED_ZONE:
            operation_lo = self.build_tracking_ui()
        elif display_type == self.TaskDisplayType.DETECTED_ZONE:
            operation_lo = self.build_detected_ui()
        elif display_type == self.TaskDisplayType.UNSTAGED_ZONE:
            operation_lo = self.build_unstaged_ui()
        return operation_lo

    def _build_chip_title(self):
        filter_elements = ReadClientConfig.get_config_item("file_linkage", "filter_property")
        # element = [prop, type]
        chip_title_ls = []
        for e in filter_elements:
            filter_property_name, filter_type_name = e[0], e[1]
            filter_type = MSK_Type(type_name=filter_type_name)
            filter_property = MSK_Property(prop_type=filter_type, prop_name=filter_property_name)
            entity = self.affiliated_container.request_entity(requesting_prop=filter_property)
            chip_title_ls.append(f"{filter_property_name} : {entity.address.value}")
        chip_title = " / ".join(chip_title_ls)
        return chip_title

    def build_tracking_ui(self) -> QHBoxLayout:
        operation_lo = QHBoxLayout()
        chip_title = self._build_chip_title()
        file_hyperlink = FileHyperline(text=chip_title, file_path=self.file_path)
        file_hyperlink.file_hyperlink_clicked.connect(self.file_hyperlink_clicked_callback)
        operation_lo.addWidget(file_hyperlink)
        operation_lo.addStretch()
        call_btn = QPushButton("Call")
        call_btn.clicked.connect(lambda: self.mount_status_changed(operation_type="CALL"))
        operation_lo.addWidget(call_btn)
        untrack_btn = QPushButton("Untrack")
        untrack_btn.clicked.connect(lambda: self.mount_status_changed(operation_type="UNTRACK"))
        operation_lo.addWidget(untrack_btn)

        return operation_lo

    def build_detected_ui(self) -> QHBoxLayout:
        operation_lo = QHBoxLayout()
        chip_title = f"{self.file_path}"
        file_hyperlink = FileHyperline(text=chip_title, file_path=self.file_path)
        file_hyperlink.file_hyperlink_clicked.connect(self.file_hyperlink_clicked_callback)
        operation_lo.addWidget(file_hyperlink)
        operation_lo.addStretch()
        track_btn = QPushButton("Track")
        track_btn.clicked.connect(lambda: self.mount_status_changed(operation_type="TRACK"))
        operation_lo.addWidget(track_btn)
        untrack_btn = QPushButton("Untrack")
        untrack_btn.clicked.connect(lambda: self.mount_status_changed(operation_type="UNTRACK"))
        operation_lo.addWidget(untrack_btn)

        return operation_lo

    def build_unstaged_ui(self) -> QHBoxLayout:
        operation_lo = QHBoxLayout()
        chip_title = f"{self.file_path}"
        file_hyperlink = FileHyperline(text=chip_title, file_path=self.file_path)
        file_hyperlink.file_hyperlink_clicked.connect(self.file_hyperlink_clicked_callback)
        operation_lo.addWidget(file_hyperlink)
        operation_lo.addStretch()
        track_btn = QPushButton("Track")
        track_btn.clicked.connect(lambda: self.mount_status_changed(operation_type="TRACK"))
        operation_lo.addWidget(track_btn)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.mount_status_changed(operation_type="REMOVE"))
        operation_lo.addWidget(remove_btn)

        return operation_lo

    # def build_unbind_ui(self) -> QHBoxLayout:
    #     operation_lo = QHBoxLayout()
    #     chip_title = f" \
    #         {self.affiliated_container.request_entity(requesting_prop=MSK_Property(prop_name="cut_num", prop_type="CutNo"))} - \
    #         {self.affiliated_container.request_entity(requesting_prop=MSK_Property(prop_name="work", prop_type="Work"))} \
    #     "
    #     file_hyperlink = QLabel(chip_title)
    #     operation_lo.addWidget(file_hyperlink)
    #     operation_lo.addStretch()
    #     stage_btn = QPushButton("Bind")
    #     operation_lo.addWidget(stage_btn)

    #     return operation_lo

    def mount_status_changed(self, operation_type: str):
        self.mount_status_changed_sig.emit(
            operation_type, 
            self.file_path,
            str(self.affiliated_container.container_index) if self.affiliated_container is not None else None
        )

    def browse_file_to_bind(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open", "", "All files (*)")
        if filename:
            pass
    
    def file_hyperlink_clicked_callback(self, file_path: str):
        local_url = QUrl.fromLocalFile(file_path)
        open_succed = QDesktopServices.openUrl(local_url)
        if not open_succed:
            raise f"path {file_path} not exist, or no application to open the file"

        