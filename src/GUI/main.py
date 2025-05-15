from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QThread
from src.backend.helpers import load_styles
from src.backend import Compiler, Installer
from pathlib import Path


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # Variables
        self.SOURCE_DIR = None
        self.OUTPUT_DIR = None
        self.ENV = None
        self.ENTRY_POINT = None

        self.dir = None

        self.resize(800, 600)
        self.setWindowTitle("Compiler")
        self.setup_ui()
        self.setStyleSheet(load_styles(Path(__file__).parent / "styles" / "style.qss"))
        

    def setup_ui(self):
        # Create the main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setObjectName("main_layout")

        # Create interface to get source dir
        # Frame
        self.source_frame = QFrame()

        # Layout
        self.source_layout = QHBoxLayout()
        self.source_layout.setObjectName("source_layout")
        self.source_dir_label = QLabel("Source", self)
        self.source_input = QLineEdit(self)
        self.source_input.setPlaceholderText("Enter path to your project source folder")
        self.source_browse_button = QPushButton("Browse", self)
        self.source_layout.addWidget(self.source_dir_label,)
        self.source_layout.addWidget(self.source_input,)
        self.source_layout.addWidget(self.source_browse_button,)
        self.source_frame.setLayout(self.source_layout)

        # Create interface to get destination dir
        # Frame
        self.dest_frame = QFrame()

        # Layout
        self.dest_layout = QHBoxLayout()
        self.dest_layout.setObjectName("dest_layout")
        self.dest_dir_label = QLabel("Dest", self)
        self.dest_input = QLineEdit(self)
        self.dest_input.setPlaceholderText("Enter path to output directory")
        self.dest_browse_button = QPushButton("Browse", self)
        self.dest_layout.addWidget(self.dest_dir_label,)
        self.dest_layout.addWidget(self.dest_input,)
        self.dest_layout.addWidget(self.dest_browse_button,)
        self.dest_frame.setLayout(self.dest_layout)

        # Create interface to get entry dir
        # Frame
        self.entry_frame = QFrame()

        # Layout
        self.entry_layout = QHBoxLayout()
        self.entry_layout.setObjectName("entry_layout")
        self.entry_dir_label = QLabel("Entry", self)
        self.entry_input = QLineEdit(self)
        self.entry_input.setPlaceholderText("Enter path to project entry point")
        self.entry_browse_button = QPushButton("Browse", self)
        self.entry_layout.addWidget(self.entry_dir_label,)
        self.entry_layout.addWidget(self.entry_input,)
        self.entry_layout.addWidget(self.entry_browse_button,)
        self.entry_frame.setLayout(self.entry_layout)

        # create the compile button
        self.compile_button = QPushButton("Compile")

        # Add lhe controls to the main layout
        self.main_layout.addWidget(self.source_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.entry_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.dest_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.compile_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Connect Buttons
        self.source_browse_button.clicked.connect(lambda: self._get_dir_path("source"))
        self.dest_browse_button.clicked.connect(lambda: self._get_dir_path("dest"))
        self.entry_browse_button.clicked.connect(lambda: self._get_file_path("entry"))
        
        

        self.compile_button.clicked.connect(self._compile)

    def _get_dir_path(self, id: str):
        dir_path: Path = QFileDialog.getExistingDirectory(
            self,
            "Open Directory",
            dir = self.dir if self.dir != None else ""
        )
        if Path(dir_path).exists:
            if id == "source":
                self.SOURCE_DIR = dir_path
                self.source_input.setText(self.SOURCE_DIR)
                self.dir = self.SOURCE_DIR
            elif id == "dest":
                self.OUTPUT_DIR = dir_path
                self.dest_input.setText(self.OUTPUT_DIR)

    def _get_file_path(self, id) -> None:
        """Get's the entry point file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose the Project Entry Point",
            self.dir if self.dir != None else "",
        )
        if Path(file_path).exists():
            self.ENTRY_POINT = file_path
            if id == "entry":
                self.ENTRY_POINT = file_path
                self.entry_input.setText(self.ENTRY_POINT)
    
    def _compile(self):
        self._prepare_compiler("Compiler_Thread")
        if not hasattr(self, 'thread') or not self.thread.isRunning():
            self._prepare(True)
            self.worker = Compiler(self.SOURCE_DIR, self.OUTPUT_DIR, self.ENTRY_POINT)
            
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(lambda: self._prepare(False))
            self.worker.error.connect(self._handle_errors)
            self.worker.finished.connect(self._install_dependencies)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)

            self.thread.start()
        else:
            QMessageBox.information(
                self,
                "Info",
                "Compilation is in progress"
            )
    def _prepare_compiler(self, name: str = None):
        # create a thread
        self.thread: QThread = QThread(self)
        self.thread.setObjectName(name)
        

    def _prepare(self, state: bool) -> None:
        self.source_browse_button.setDisabled(state)
        self.dest_browse_button.setDisabled(state)
        self.entry_browse_button.setDisabled(state)
        self.source_input.setDisabled(state)
        self.dest_input.setDisabled(state)
        self.entry_input.setDisabled(state)
        self.compile_button.setDisabled(state)

    def _install_dependencies(self) -> None:
        """Install project dependencies"""
        self._prepare_compiler("Installer_Thread")
        self.dependencies_worker = Installer(Path(self.OUTPUT_DIR))

        self.dependencies_worker.moveToThread(self.thread)
        self.thread.started.connect(self.dependencies_worker.run)
        self.dependencies_worker.errors.connect(self._handle_errors)
        self.dependencies_worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def _handle_errors(self, error):
        QMessageBox.warning(
            self,
            "Error",
            f"Encountered the following errors\n{error}",
        )
        if hasattr(self, "thread"):
            try:
                if hasattr(self, "worker"):
                    self.worker.deleteLater()
                elif hasattr(self, "dependencies_worker"):
                    self.dependencies_worker.deleteLater()
            except:
                pass 
        
