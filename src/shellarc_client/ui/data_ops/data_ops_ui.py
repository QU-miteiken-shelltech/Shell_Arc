import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QGroupBox, QLabel, QPushButton, 
    QLineEdit, QSpacerItem, QSizePolicy, 
    QComboBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView,
)

from shellarc_msk.mskob.field_obj import MSK_Field
from shellarc_msk.mskob.containercoll_obj import MSK_ContainerCollection
from shellarc_msk.mskob.container_obj import MSK_Container
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.adress_obj import MSK_Address
from shellarc_msk.mskob.type_obj import MSK_Type
from shellarc_msk.mskob.entity_obj import MSK_Entity
from shellarc_msk.mskut.path_solver import MSKUT_PathSolver


from shellarc_client.engine.mskio import create_msk


class DataOpsUi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_built = False
        self.context_field_name = None

        self.lo = QVBoxLayout(self)

        # --- where the new data set lives: folder path + Browse + Initialize
        init_btn = QPushButton("Initialize")
        init_btn.clicked.connect(self.check_folder)
        self.lo.addWidget(init_btn)

        self.setLayout(self.lo)

    # ------------------------------------------------------------------ build
    def build_ui(self):
        if self._is_built:          # "Initialize" pressed twice must not duplicate the sections
            return
        self._is_built = True
        self._build_field_section()
        self._build_element_section()
        self._build_table_section()

    def _build_field_section(self):
        create_field_lo = QHBoxLayout()
        create_field_label = QLabel("Field : ")
        create_field_lo.addWidget(create_field_label)
        self.create_field_input = QLineEdit("")
        self.create_field_input.setPlaceholderText("New field name")
        create_field_lo.addWidget(self.create_field_input)
        create_field_btn = QPushButton("Create")
        create_field_btn.clicked.connect(self.create_field)
        create_field_lo.addWidget(create_field_btn)
        self.lo.addLayout(create_field_lo)
        self.lo.addItem(
            QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

    def _build_element_section(self):
        element_editing_lo = QHBoxLayout()

        # Type
        type_box = QGroupBox("Type")
        type_creator_lo = QVBoxLayout(type_box)
        self.type_input = QLineEdit("")
        self.type_input.setPlaceholderText("New Type")
        type_creator_lo.addWidget(self.type_input)
        type_creator_btn = QPushButton("Create")
        type_creator_btn.clicked.connect(self.create_type)
        type_creator_lo.addWidget(type_creator_btn)
        type_creator_lo.addStretch(1)
        element_editing_lo.addWidget(type_box)

        # Property
        property_box = QGroupBox("Property")
        property_creator_lo = QVBoxLayout(property_box)
        self.property_input = QLineEdit("")
        self.property_input.setPlaceholderText("New Property")
        property_creator_lo.addWidget(self.property_input)
        self.property_type_combo = QComboBox()
        property_creator_lo.addWidget(self.property_type_combo)
        property_creator_btn = QPushButton("Create")
        property_creator_btn.clicked.connect(self.create_property)
        property_creator_lo.addWidget(property_creator_btn)
        add_prop_to_field_btn = QPushButton("Add to Field")
        add_prop_to_field_btn.clicked.connect(self.add_prop_to_field)
        property_creator_lo.addWidget(add_prop_to_field_btn)
        property_creator_lo.addStretch(1)
        element_editing_lo.addWidget(property_box)

        # Definition of the field that is currently selected (read-only)
        def_box = QGroupBox("Field definition")
        def_lo = QVBoxLayout(def_box)
        self.field_def_table = QTableWidget(0, 2)
        self.field_def_table.setHorizontalHeaderLabels(["Property", "Type"])
        self.field_def_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.field_def_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.field_def_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        def_lo.addWidget(self.field_def_table)
        element_editing_lo.addWidget(def_box, 1)

        self.lo.addLayout(element_editing_lo)

    def _build_table_section(self):
        table_box = QGroupBox("Containers")
        table_lo = QVBoxLayout(table_box)

        bar_lo = QHBoxLayout()
        bar_lo.addWidget(QLabel("Field : "))
        self.field_combo = QComboBox()
        self.field_combo.setMinimumWidth(160)
        self.field_combo.currentTextChanged.connect(self.on_field_changed)
        bar_lo.addWidget(self.field_combo)
        reload_btn = QPushButton("Reload")
        reload_btn.clicked.connect(self.reload_table)
        bar_lo.addWidget(reload_btn)
        bar_lo.addStretch(1)
        add_container_btn = QPushButton("Add Container")
        add_container_btn.clicked.connect(self.add_container)
        bar_lo.addWidget(add_container_btn)
        table_lo.addLayout(bar_lo)

        # one row per container; column 0 = container id (read-only), then one column per property
        self.container_table = QTableWidget(0, 1)
        self.container_table.setHorizontalHeaderLabels(["container id"])
        self.container_table.setAlternatingRowColors(True)
        self.container_table.horizontalHeader().setStretchLastSection(True)
        self.container_table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.AnyKeyPressed
        )
        self.container_table.cellChanged.connect(self.on_cell_changed)
        table_lo.addWidget(self.container_table, 1)

        self.lo.addWidget(table_box, 1)

    # ------------------------------------------------------------------ view helpers (no store access)
    def set_field_choices(self, names):
        self.field_combo.blockSignals(True)
        self.field_combo.clear()
        self.field_combo.addItems(names)
        self.field_combo.blockSignals(False)

    def set_type_choices(self, names):
        self.property_type_combo.clear()
        self.property_type_combo.addItems(names)

    def set_field_definition(self, defs):
        """defs: list of (property name, type name)"""
        self.field_def_table.setRowCount(len(defs))
        for r, (prop, typ) in enumerate(defs):
            self.field_def_table.setItem(r, 0, QTableWidgetItem(prop))
            self.field_def_table.setItem(r, 1, QTableWidgetItem(typ))

    def set_table(self, columns, rows):
        """columns: property column labels; rows: list of (container id, [cell texts])."""
        t = self.container_table
        t.blockSignals(True)       # filling the table must not fire on_cell_changed
        t.clear()
        t.setColumnCount(1 + len(columns))
        t.setHorizontalHeaderLabels(["container id"] + list(columns))
        t.setRowCount(len(rows))
        for r, (cid, cells) in enumerate(rows):
            id_item = QTableWidgetItem(cid)
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            t.setItem(r, 0, id_item)
            for c, text in enumerate(cells):
                t.setItem(r, 1 + c, QTableWidgetItem(text))
        t.resizeColumnsToContents()
        t.blockSignals(False)

    # ------------------------------------------------------------------ callbacks (print only)
    def browse_folder(self):
        print("browse_folder")

    def check_folder(self):
        # if not os.listdir('/your/path'):
        #     print("Not empty")
        #     return
        msk_root = MSKUT_PathSolver().mskfs_space
        if os.listdir(str(msk_root)):
            print("Not empty" + str(msk_root))
            return
        self.build_ui()

    def create_field(self):
        new_field_name = self.create_field_input.text()
        if not new_field_name:
            return
        new_field = create_msk.create_field(
            new_field_name=new_field_name
        )
        self.context_field_name = new_field_name
        self.field_combo.clear()
        self.field_combo.addItems(MSK_Field.field_names())
        self.field_combo.setCurrentText(new_field_name)
        self.create_field_input.setText("")

    def create_type(self) -> MSK_Type:
        new_type_name = self.type_input.text()
        if not new_type_name:
            return
        new_type = create_msk.create_type(
            type_name=new_type_name
        )
        self.property_type_combo.clear()
        self.property_type_combo.addItems([t.type_name for t in MSK_Type.list_types()])
        return new_type

    def create_property(self) -> MSK_Property:
        new_property_name = self.property_input.text()
        new_property_type_name = self.property_type_combo.currentText()
        if not new_property_name or not new_property_type_name:
            return
        new_property = create_msk.create_property(
            prop_type=MSK_Type(type_name=new_property_type_name),
            prop_name=new_property_name
        )
        return new_property

    def add_prop_to_field(self):
        new_property = self.create_property()
        create_msk.add_field_def(
            field_name=self.context_field_name,
            new_type=new_property.prop_type,
            new_property=new_property
        )
        row_count = self.field_def_table.rowCount() + 1
        self.field_def_table.setRowCount(row_count)
        self.field_def_table.setItem(row_count - 1, 0, QTableWidgetItem(new_property.prop_name))
        self.field_def_table.setItem(row_count - 1, 1, QTableWidgetItem(new_property.prop_type.type_name))

    def on_field_changed(self, text=None):
        if text is None:
            return
        self.context_field_name = text

    def reload_table(self):
        context_field = MSK_Field(field_name=self.context_field_name)
        self.container_table.clear()
        self.container_table.setRowCount(0)
        self.container_table.setColumnCount(len(context_field.field_ls) + 1)
        header_labels = ["container id"] + [e[0].prop_name for e in context_field.field_ls]
        self.container_table.setHorizontalHeaderLabels(header_labels)
        prop_col_num = {
            header_item : i for i, header_item in enumerate(header_labels)
        }
        coll = MSK_ContainerCollection(field_name=self.context_field_name)
        k = 0
        for container in coll.container_iter():
            self.container_table.setItem(k, 0, QTableWidgetItem(container.container_index))
            for entity in container:
                self.container_table.setItem(k, prop_col_num[entity.prop.prop_name], QTableWidgetItem(container.container_index))
            k += 1

    def add_container(self):
        print("add_container")

    def on_cell_changed(self, row=None, column=None):
        print("on_cell_changed")