from typing import Optional, Any, overload
import inspect

from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QDialog, QColorDialog,
    QPlainTextEdit, QCompleter, QLineEdit,
    QMessageBox
)
from PySide6.QtGui import QColor, QTextCursor, QKeyEvent

from PySide6.QtCore import Qt, QStringListModel

from shellarc_msk.mskob.container_obj import MSK_Container
from shellarc_msk.mskob.property_obj import MSK_Property
from shellarc_msk.mskob.type_obj import MSK_Type
from shellarc_engine.mount import mount_file_manager

class CustomTag(QLabel):
    def __init__(self, 
                 title: str, 
                 base_color: Optional[str]="#16a085",
                 expression: Optional[str]=None, 
                 parent=None):
        super().__init__(parent=parent, text=title)
        self.setStyleSheet(
            "QLabel {"
            f"   background-color: {base_color};"
            "   color: white;"
            "   padding: 2px;"
            "   font-size: 14px;"
            "}"
        )
        self.title = title
        self.expression = expression
        self.base_color = base_color
        if self.expression is not None:
            self.eval_expressions()

    def eval_expressions(self):
        working_expression = self.expression
        try:
            existing_properties = self.parentWidget().affiliated_container.get_existing_properties()
            existing_properties_dict: dict[str, MSK_Property] = { prop.prop_name : prop for prop in existing_properties }
            for prop_name in sorted([pname for pname in existing_properties_dict], key=len, reverse=True):
                if working_expression:  
                    working_expression = working_expression.replace(
                        prop_name, 
                        (f"self.parentWidget().affiliated_container.request_entity_from_str(prop_name=\"{prop_name}\", "
                         f"type_name=\"{existing_properties_dict[prop_name].prop_type.type_name}\")"
                         ".address.value")
                    )
            internal_funcs = [
                name
                for name, obj in CustomTag.__dict__.items()
                if (inspect.isfunction(obj) or isinstance(obj, (classmethod, staticmethod)) and
                    name.startswith("set"))
            ]
            for func_name in sorted(internal_funcs, key=len, reverse=True):
                if working_expression:  
                    working_expression = working_expression.replace(func_name, f"self.{func_name}")
            exec(working_expression)
        except Exception as e:
            pass
            # QMessageBox.warning(
            #     self,
            #     "Expression invalid", 
            #     f"The tag expression of tag {self.title} is invalid\nError : {e}"
            # )
        finally:
            print(working_expression)

    def set_color(self, hex_code: str):
        self.setStyleSheet(
            f"background-color: {hex_code};"
        )

    def set_fontcolor(self, hex_code: str):
        self.setStyleSheet(
            f"color: {hex_code};"
        )

    def set_text(self, text: str):
        self.setText(text)

    def set_fontsize(self, fontsize: int):
        self.setStyleSheet(f"font-size: {fontsize}px;")

    def set_padding(self, fontsize: int):
        self.setStyleSheet(f"padding: {fontsize}px;")

    def mouseDoubleClickEvent(self, event):
        result = TagCreatorDialog(
            title=self.title, 
            expression=self.expression,
            parent=self.parentWidget()
        ).exec()
        super().mouseDoubleClickEvent(event)


class CompletionPlainTextEdit(QPlainTextEdit):
    _POPUP_KEYS = (
        Qt.Key.Key_Return,
        Qt.Key.Key_Enter,
        Qt.Key.Key_Tab,
        Qt.Key.Key_Backtab,
        Qt.Key.Key_Escape,
    )

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._completer: Optional[QCompleter] = None

    def set_completer(self, completer: QCompleter) -> None:
        self._completer = completer

    def keyPressEvent(self, event: QKeyEvent):
        completer = self._completer
        if (
            completer is not None
            and completer.popup().isVisible()
            and event.key() in self._POPUP_KEYS
        ):
            event.ignore()
            return
        super().keyPressEvent(event)


class TagCreatorDialog(QDialog):
    def __init__(self, title: Optional[str]=None, expression: Optional[str]=None, parent=None):
        super().__init__(parent=parent)
        print(self.parentWidget());print("***")
        self.affiliated_container: MSK_Container = self.parentWidget().affiliated_container
        self.title = title
        self.expression = expression

        dialog_lo = QVBoxLayout()
        base_color_lo = QHBoxLayout()
        base_color_label = QLabel("Base color : ")
        base_color_lo.addWidget(base_color_label)
        self.base_color = "#16a085"
        self.base_color_btn = QPushButton("Select")
        self.base_color_btn.clicked.connect(
            lambda: self.open_color_dialog(target_object=self.base_color_btn)
        )
        base_color_lo.addWidget(self.base_color_btn)
        dialog_lo.addLayout(base_color_lo)
        dialog_lo.addSpacing(5)

        self.usable_properties = {prop.prop_name : prop for prop in self.affiliated_container.get_existing_properties()}
        usable_properties_label = QLabel("Usable properties : \n" + " / ".join([p for p in self.usable_properties]))
        dialog_lo.addWidget(usable_properties_label)

        tag_title_lo = QHBoxLayout()
        if self.title is None:
            tag_title_label = QLabel("Tag title : ")
            tag_title_lo.addWidget(tag_title_label)
            self.tag_title_input = QLineEdit("")
            self.tag_title_input.setPlaceholderText("Tag title ...")
            tag_title_lo.addWidget(self.tag_title_input)
        else:
            tag_title_label = QLabel(f"Tag title : {self.title}")
            tag_title_lo.addWidget(tag_title_label)
        dialog_lo.addLayout(tag_title_lo)

        self.expression_editor = CompletionPlainTextEdit("")
        self.expression_editor.setPlaceholderText("Tag expression ...")
        if self.expression is not None:
            self.expression_editor.setPlainText(self.expression)
        preset_func_list = [
            name
            for name, obj in CustomTag.__dict__.items()
            if (inspect.isfunction(obj) or isinstance(obj, (classmethod, staticmethod)) and 
                name.startswith("set"))
        ]
        completer_model = QStringListModel([p for p in self.usable_properties] + preset_func_list, self)

        self._completer = QCompleter(completer_model, self)
        self._completer.setWidget(self.expression_editor)
        self.expression_editor.set_completer(self._completer)  
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._inserting_completion = False
        self._completer.activated.connect(self._insert_completion)
        self.expression_editor.textChanged.connect(self._update_completer)

        dialog_lo.addWidget(self.expression_editor)

        color_pick_lo = QHBoxLayout()
        color_pick_lo.addStretch()
        color_pick_btn = QPushButton("Color")
        color_pick_btn.clicked.connect(self.color_code_input)
        color_pick_lo.addWidget(color_pick_btn)
        dialog_lo.addLayout(color_pick_lo)

        dialog_lo.addSpacing(5)
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_tag)
        dialog_lo.addWidget(create_btn)

        if self.title is not None:
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(self.delete_tag)
            dialog_lo.addWidget(delete_btn)

        self.setLayout(dialog_lo)

    @overload
    def open_color_dialog(self, target_object: Any) -> None:
        ...

    @overload
    def open_color_dialog(self) -> str:
        ...

    def open_color_dialog(self, target_object: Optional[Any] = None):
        color: QColor = QColorDialog.getColor(
            QColor("#16a085"),
            self,
            "Color picker"
        )
        if color.isValid():
            hex_code = color.name(QColor.NameFormat.HexArgb)
            if target_object is not None:
                self.base_color = hex_code 
                rgba = f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"
                target_object.setText(hex_code)
                target_object.setStyleSheet(
                    f"background-color: {rgba}; color: white;"
                )
                return None
            else:
                return hex_code
        return None

    def color_code_input(self) -> None:
        color = self.open_color_dialog()
        if color is None:
            return
        cursor = self.expression_editor.textCursor()
        cursor.insertText(f"\"{color}\"")

    def create_tag(self):
        if self.title is None:
            self.title=self.tag_title_input.text() if self.tag_title_input.text() else "MyTag"
        self.expression = self.expression_editor.toPlainText()
        mount_file_manager.write_tag_info(
            file_path=self.parentWidget().file_path,
            new_tag_title=self.title,
            new_tag_expression=self.expression,
            new_tag_basecolor=self.base_color
        )
        self.accept()

    def delete_tag(self):
        if self.title is None:
            return
        mount_file_manager.delete_tag_info(
            file_path=self.parentWidget().file_path,
            tag_title=self.title
        )
        self.accept()

    def _current_token(self) -> str:
        cursor = self.expression_editor.textCursor()
        block_text = cursor.block().text()
        pos_in_block = cursor.positionInBlock()

        start = pos_in_block
        while start > 0 and (block_text[start - 1].isalnum() or block_text[start - 1] in "_.-"):
            start -= 1

        return block_text[start:pos_in_block]

    def _update_completer(self):
        if self._inserting_completion:
            return

        prefix = self._current_token()
        if not prefix:
            self._completer.popup().hide()
            return

        if prefix != self._completer.completionPrefix():
            self._completer.setCompletionPrefix(prefix)

        rect = self.expression_editor.cursorRect()
        popup = self._completer.popup()
        rect.setWidth(
            popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width()
        )
        self._completer.complete(rect)

        first_index = self._completer.completionModel().index(0, 0)
        if first_index.isValid():
            popup.setCurrentIndex(first_index)

    def _insert_completion(self, completion: str):
        self._inserting_completion = True
        try:
            cursor = self.expression_editor.textCursor()
            prefix_len = len(self._completer.completionPrefix())
            if prefix_len > 0:
                cursor.movePosition(
                    QTextCursor.MoveOperation.Left,
                    QTextCursor.MoveMode.KeepAnchor,
                    prefix_len,
                )
            cursor.insertText(completion)
            self.expression_editor.setTextCursor(cursor)
        finally:
            self._inserting_completion = False