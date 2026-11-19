import re

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QDialog,
    QWidget, QLabel, QComboBox,
    QPushButton, QMessageBox, QScrollArea
)
from PySide6.QtCore import QEvent

from shellarc_client.engine.config.read_config import ReadClientConfig
from shellarc_client.engine.mount import mount_file_manager
from shellarc_client.engine.mskio import read_msk
from shellarc_msk.mskob.entity_obj import MSK_Entity
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.type_obj import MSK_Type
from shellarc_msk.mskdn.metanode import MSKDN_Metanode
from shellarc_msk.mskdn.node import MSKDN_VNode

class RegisterFileItem(QWidget):
    def __init__(self, 
                 file_path: str, 
                 linkage_settings: dict[str, list[MSK_Entity]],
                 parent=None):
        super().__init__(parent=parent)
        self.combo_dict: dict[str, QComboBox] = {}
        self.file_path = file_path

        item_lo = QVBoxLayout()
        item_lo.addWidget(QLabel(self.file_path))

        linkage_setting_lo = QHBoxLayout()
        for link_prop, entities in linkage_settings.items():
            linkage_setting_lo.addWidget(QLabel(f"{link_prop} : "))
            linkage_combo = QComboBox()
            linkage_combo.clear()
            for entity in entities:
                linkage_combo.addItem(
                    entity.address.value, entity
                )
            linkage_setting_lo.addWidget(linkage_combo)
            self.combo_dict[link_prop] = linkage_combo
        linkage_setting_lo.addStretch()
        track_btn = QPushButton("Track")
        track_btn.setFixedWidth(65)
        track_btn.clicked.connect(self.track_file)
        linkage_setting_lo.addWidget(track_btn)
        untrack_btn = QPushButton("Untrack")
        untrack_btn.setFixedWidth(65)
        untrack_btn.clicked.connect(self.untrack_file)
        linkage_setting_lo.addWidget(untrack_btn)
        hold_btn = QPushButton("Hold")
        hold_btn.setFixedWidth(65)
        hold_btn.clicked.connect(self.hold_file)
        linkage_setting_lo.addWidget(hold_btn)
        item_lo.addLayout(linkage_setting_lo)

        self.setLayout(item_lo)

    def remove_self(self):
        self.setParent(None)
        self.deleteLater()

    def track_file(self):
        metanodes = []
        conditions = []
        for _, combo_obj in self.combo_dict.items():
            entity: MSK_Entity = combo_obj.currentData()
            metanodes.append(MSKDN_Metanode(iterable=[MSKDN_VNode(entity=entity)]))
            conditions.append((entity.prop, entity.address))
        affiliated_containers = read_msk.filter_container(
            field_name=ReadClientConfig.get_config_item("file_linkage", "record_field"),
            conditions=conditions,
            max_count=1
        )
        affiliated_container_index = str(affiliated_containers[0].container_index)
        parent_widget = self.parentWidget()
        while parent_widget is not None:
            if isinstance(parent_widget, QDialog):
                break
            parent_widget = parent_widget.parentWidget()
        duplicated_file_path = mount_file_manager.check_container_duplication(
            container_index=affiliated_container_index,
            extra_source=parent_widget.task_settings_info["tracked"]
        )
        if duplicated_file_path is not None:
            container_info = " ".join([f"{c[0].prop_name} : {c[1].value}" for c in conditions])
            reply = QMessageBox.question(
                self, 
                "Confirmation", 
                (f"File affiliated to {container_info} already exist ({duplicated_file_path}).\n"
                 "Are you sure that you want to overwrite it?"),
                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        parent_widget.task_settings_info["tracked"].setdefault(
            self.file_path, {}).setdefault("affiliation", affiliated_container_index)
        self.remove_self()

    def untrack_file(self):
        self.parentWidget().task_settings_info["untracked"].append(self.file_path)
        self.remove_self()

    def hold_file(self):
        self.parentWidget().task_settings_info["detected"].append(self.file_path)
        self.remove_self()

class RegisterTaskDialog(QDialog):
    def __init__(self, 
                 mount_info: dict, 
                 parent=None):
        super().__init__(parent=parent)
        self.task_settings_info: dict[str, list] = {
            "tracked": {},
            "untracked": [],
            "detected": []
        }
        dialog_lo = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_lo = QVBoxLayout(scroll_widget)
        filter_elements = ReadClientConfig.get_config_item("file_linkage", "filter_property")
        # element = [prop, type]
        linkage_settings = {}
        for e in filter_elements:
            filter_property_name, filter_type_name = e[0], e[1]
            entities = read_msk.get_entities_by_property(
                target_field_name=ReadClientConfig.get_config_item("file_linkage", "record_field"),
                requested_property=MSK_Property(
                    prop_type=MSK_Type(type_name=filter_type_name),
                    prop_name=filter_property_name
                ),
                eluminate_duplication=True
            )
            def extract_number(x: str) -> str:
                numbers = re.findall(r"\d+", x)
                return int(numbers[0]) if len(numbers) == 1 else x
            entities.sort(
                key=lambda x : extract_number(x.address.value)
            )
            linkage_settings[filter_property_name] = entities

        for file_path in mount_info["detected"]:
            item = RegisterFileItem(
                file_path=file_path,
                linkage_settings=linkage_settings,
                parent=self
            )
            scroll_lo.addWidget(item)
        scroll_lo.addStretch()
        scroll_area.setWidget(scroll_widget)
        dialog_lo.addWidget(scroll_area)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(lambda: self.close_dialog(do_accept=True))
        dialog_lo.addWidget(close_btn)
        self.setLayout(dialog_lo)

    def childEvent(self, event):
        super().childEvent(event)
        if event.type() == QEvent.Type.ChildRemoved:
            if isinstance(event.child(), RegisterFileItem):
                remaining = self.findChildren(RegisterFileItem)
                if len(remaining) == 0:
                    self.close_dialog()

    def close_dialog(self, do_accept: bool=True):
        remaining_items = self.findChildren(RegisterFileItem)
        for remaining_item in remaining_items:
            self.task_settings_info["detected"].append(remaining_item.file_path)
        mount_file_manager.update_scanned_time()
        mount_file_manager.write_file_status(
            info=self.task_settings_info
        )
        if do_accept:
            self.accept()

    def closeEvent(self, arg__1):
        self.close_dialog(do_accept=False)
        return super().closeEvent(arg__1)
