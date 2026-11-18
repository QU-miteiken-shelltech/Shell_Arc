import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from shellarc_client.ui.main_ui import MainWindow


def main():
    app = QApplication(sys.argv)

    splash_img_path = Path(__file__).resolve().parents[2] / "resources/splash.png"
    splash_pixmap = QPixmap(splash_img_path)
    splash_pixmap = splash_pixmap.scaled(
        950, 950,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )
    splash = QSplashScreen(splash_pixmap)
    splash.show()
    splash.showMessage(
        "Resolving initial data ...", 
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, 
        Qt.GlobalColor.white
    )

    window = MainWindow()
    window.show()
    splash.finish(window)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()