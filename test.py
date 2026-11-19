import sys
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QColorDialog, QLabel, QPushButton, QVBoxLayout, QWidget


class ColorPickerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide カラーピッカー")
        self.resize(300, 160)

        self.label = QLabel("選択された色: なし")
        self.btn = QPushButton("色を選ぶ")
        self.btn.clicked.connect(self.open_color_dialog)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.btn)

    def open_color_dialog(self):
        # 初期色を指定してダイアログを開く（アルファ値も扱いたい場合は ShowAlphaChannel を指定）
        color: QColor = QColorDialog.getColor(
            QColor("#3498db"),
            self,
            "カラーピッカー",
            QColorDialog.ColorDialogOption.ShowAlphaChannel,
        )

        # キャンセルされた場合は isValid() が False になる
        if color.isValid():
            hex_code = color.name(QColor.NameFormat.HexArgb)  # 例: "#ff3498db"
            rgba = f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"
            self.label.setText(f"HEX: {hex_code}\nRGBA: {rgba}")
            self.label.setStyleSheet(
                f"background-color: {rgba}; color: white; padding: 8px; border-radius: 4px;"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorPickerApp()
    window.show()
    sys.exit(app.exec())
