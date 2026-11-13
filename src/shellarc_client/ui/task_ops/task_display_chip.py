from typing import Optional
from enum import StrEnum

from PySide6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout,
    QVBoxLayout, QLabel, QPushButton,
    QFileDialog
)
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import Signal, Qt

from shellarc_msk.mskob.container_obj import MSK_Container
from shellarc_msk.mskob.property_obj import MSK_Property

class FileHyperline(QLabel):
    file_hyperlink_clicked = Signal(str)

    def __init__(self, text: str, parent=None):
        super().__init__(text=text, parent=parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.file_hyperlink_clicked.emit(self.text())
        super().mouseDoubleClickEvent(event)


class TaskDisplayChip(QWidget):
    class TaskDisplayType(StrEnum):
        STAGED_ZONE = "staged_zone"
        DETECTED_ZONE = "detected_zone"
        UNSTAGED_ZONE = "unstaged_zone"
        UNBINDED_ZONE = "unbinded_zone"

    def __init__(self, 
                 affiliated_container: MSK_Container,
                 display_type: TaskDisplayType,
                 parent=None):
        super().__init__(parent=parent)
        self.affiliated_container = affiliated_container
        container_frame = QFrame()
        container_frame.setFrameShape(QFrame.Shape.StyledPanel)
        container_frame.setFrameShadow(QFrame.Shadow.Sunken)
        container_frame.setLineWidth(2)

        chip_lo = QVBoxLayout(container_frame)

        if display_type == self.TaskDisplayType.STAGED_ZONE:
            operation_lo = self.build_tracking_ui()
        elif display_type == self.TaskDisplayType.DETECTED_ZONE:
            operation_lo = self.build_detected_ui()
        elif display_type == self.TaskDisplayType.UNSTAGED_ZONE:
            operation_lo = self.build_unstaged_ui()

        chip_lo.addLayout(operation_lo)

        custom_tag_lo = QHBoxLayout()
        chip_lo.addLayout(custom_tag_lo)

        self.setLayout(chip_lo)

    def build_tracking_ui(self) -> QHBoxLayout:
        operation_lo = QHBoxLayout()
        chip_title = f" \
            {self.affiliated_container.request_entity(requesting_prop=MSK_Property(prop_name="cut_num", prop_type="CutNo"))} - \
            {self.affiliated_container.request_entity(requesting_prop=MSK_Property(prop_name="work", prop_type="Work"))} \
        "
        file_hyperlink = FileHyperline(chip_title)
        file_hyperlink.file_hyperlink_clicked.connect(self.file_hyperlink_clicked_callback)
        operation_lo.addWidget(file_hyperlink)
        operation_lo.addStretch()
        call_btn = QPushButton("Call")
        operation_lo.addWidget(call_btn)
        unstage_btn = QPushButton("Unstage")
        operation_lo.addWidget(unstage_btn)

        return operation_lo

    def build_detected_ui(self) -> QHBoxLayout:
        operation_lo = QHBoxLayout()
        chip_title = f" \
            {self.affiliated_container.request_entity(requesting_prop=MSK_Property(prop_name="cut_num", prop_type="CutNo"))} - \
            {self.affiliated_container.request_entity(requesting_prop=MSK_Property(prop_name="work", prop_type="Work"))} \
        "
        file_hyperlink = FileHyperline(chip_title)
        file_hyperlink.file_hyperlink_clicked.connect(self.file_hyperlink_clicked_callback)
        operation_lo.addWidget(file_hyperlink)
        operation_lo.addStretch()
        stage_btn = QPushButton("Stage")
        operation_lo.addWidget(stage_btn)
        unstage_btn = QPushButton("Unstage")
        operation_lo.addWidget(unstage_btn)

        return operation_lo

    def build_unstaged_ui(self) -> QHBoxLayout:
        operation_lo = QHBoxLayout()
        chip_title = f" \
            {self.affiliated_container.request_entity(requesting_prop=MSK_Property(prop_name="cut_num", prop_type="CutNo"))} - \
            {self.affiliated_container.request_entity(requesting_prop=MSK_Property(prop_name="work", prop_type="Work"))} \
        "
        file_hyperlink = FileHyperline(chip_title)
        file_hyperlink.file_hyperlink_clicked.connect(self.file_hyperlink_clicked_callback)
        operation_lo.addWidget(file_hyperlink)
        operation_lo.addStretch()
        stage_btn = QPushButton("Stage")
        operation_lo.addWidget(stage_btn)
        delete_btn = QPushButton("Delete")
        operation_lo.addWidget(delete_btn)

        return operation_lo

    def build_unbind_ui(self) -> QHBoxLayout:
        operation_lo = QHBoxLayout()
        chip_title = f" \
            {self.affiliated_container.request_entity(requesting_prop=MSK_Property(prop_name="cut_num", prop_type="CutNo"))} - \
            {self.affiliated_container.request_entity(requesting_prop=MSK_Property(prop_name="work", prop_type="Work"))} \
        "
        file_hyperlink = QLabel(chip_title)
        operation_lo.addWidget(file_hyperlink)
        operation_lo.addStretch()
        stage_btn = QPushButton("Bind")
        operation_lo.addWidget(stage_btn)

        return operation_lo

    def browse_file_to_bind(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open", "", "All files (*)")
        if filename:
            pass
    
    def file_hyperlink_clicked_callback(self, filepath: str):
        print(filepath)


        