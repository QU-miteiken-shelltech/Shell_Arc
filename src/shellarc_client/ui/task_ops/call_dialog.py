from pathlib import Path
from functools import partial

from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel
)

from shellarc_msk.mskob.container_obj import MSK_Container
from shellarc_client.engine.transfer import workflows

class TaskCallDialog(QDialog):
    def __init__(self, 
                 affiliation: MSK_Container, 
                 file_path: Path,
                 parent=None):
        super().__init__(parent=parent)
        self.affiliation = affiliation
        self.file_path = file_path
        dialog_lo = QVBoxLayout()

        info_label = QLabel()
        info_label.setText(self._get_entity_values())
        dialog_lo.addWidget(info_label)

        file_path_label = QLabel(f"File : {file_path}")
        dialog_lo.addWidget(file_path_label)

        btn_lo = QHBoxLayout()
        for call_action in workflows.available_actions():
            btn = QPushButton(call_action)
            btn.clicked.connect(partial(
                workflows.run_workflow,
                call_action,
                self.affiliation,
                self.file_path
            ))
            btn_lo.addWidget(btn)
        dialog_lo.addLayout(btn_lo)

        self.setLayout(dialog_lo)

    def _get_entity_values(self) -> str:
        return "\n".join([f"{e.prop.prop_name} - {e.address.value}" for e in self.affiliation])

    def call_workflow(self):
        pass

