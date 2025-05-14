from PySide6.QtWidgets import QApplication
from src.GUI import MainWindow


# Run the app
def run_app():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
