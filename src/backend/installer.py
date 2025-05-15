from PySide6.QtCore import QObject, Signal
import subprocess
import sys
from pathlib import Path


# Create a worker object that installs
class Installer(QObject):
    finished: Signal = Signal()
    errors: Signal = Signal(object)

    def __init__(self, output_dir: Path):
        super().__init__()
        self.setObjectName("Installer")
        self.OUTPUT_DIR = Path(output_dir).resolve()
        self.requirement_file: Path = self.OUTPUT_DIR / "requirements.txt"
        self.python_exe = sys.executable
    
    def run(self):
        if self.requirement_file.exists():
            try:
                self._create_venv("venv")
                # Install requirements using venv's pip
                pip_exe = str(self.venv_output_dir / "Scripts" / "pip.exe")
                subprocess.run([
                    pip_exe, "install", "-r", "requirements.txt"
                ],
                check=True,
                cwd=self.OUTPUT_DIR
                )
            except Exception as e:
                self.errors.emit(e)
            finally:
                self.finished.emit()
        else:
            pass

    def _create_venv(self, name: str):
        self.venv_output_dir = self.OUTPUT_DIR / name
        try:
            subprocess.run([self.python_exe, "-m", "venv", self.venv_output_dir], check=True, cwd=self.OUTPUT_DIR)
        except Exception as e:
            self.errors.emit(e)
        

    
        
