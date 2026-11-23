import sys
import argparse
from pathlib import Path

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from shellarc_client.ui.main_ui import MainWindow


def main():
    if __debug__:
        import shutil
        import atexit
        shutil.copytree(
            src="/Users/shiinaayame/Documents/test_sa2027/msk",
            dst="/Users/shiinaayame/Documents/test_sa2027/msk_1",
            dirs_exist_ok=True
        )
        atexit.register(recover_space)

    parser = argparse.ArgumentParser(description="ツールの説明文をここに書きます")
    parser.add_argument("-c", "--clean", action="store_true", help="Clean start")
    args = parser.parse_args()

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

    window = MainWindow(is_clean_mode=args.clean)
    window.show()
    splash.finish(window)

    sys.exit(app.exec())

def recover_space():
    confirmation = str(input("Recover from backup dir (/Users/shiinaayame/Documents/test_sa2027/msk_1)?"))
    if confirmation in ["Y", "y"]:
        import shutil
        shutil.copytree(
            src="/Users/shiinaayame/Documents/test_sa2027/msk_1",
            dst="/Users/shiinaayame/Documents/test_sa2027/msk",
            dirs_exist_ok=True
        )
        shutil.rmtree("/Users/shiinaayame/Documents/test_sa2027/msk_1")
    print("Bye")

if __name__ == "__main__":
    main()