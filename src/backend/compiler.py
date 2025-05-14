from PySide6.QtCore import QObject, Signal
from pathlib import Path
import shutil
from typing import List
import os
from setuptools import setup, Extension
from Cython.Build import cythonize
import tempfile


class Compiler(QObject):
    finished: Signal = Signal()
    error: Signal = Signal(object)

    def __init__(self, SRC_DIR: Path, OUTPUT_DIR: Path, ENTRY_POINT: Path = None, VENV_DIR: Path = None):
        super().__init__()
        self.SRC_DIR: Path = SRC_DIR
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.BUILD_TEMP: Path = Path(self.temp_dir_obj.name)
        self.OUTPUT_DIR: Path = Path(OUTPUT_DIR)
        self.VENV_DIR = Path(VENV_DIR)
        self.ENTRY_POINT = Path(ENTRY_POINT)

    def run(self):
        extension: List = []
        ignored_dirs: List = ["__pycache__"]

        try:
            for root, dirs, files in os.walk(self.SRC_DIR):
                # Skip __pycache__ and virtual environment folders
                dirs[:] = [
                    d for d in dirs if d not in ignored_dirs and Path(d).resolve() != self.VENV_DIR.resolve()
                    ]

                for file in files:
                    if file.endswith((".pyc", ".pyo")):
                        continue

                    abs_path: Path = Path(root) / file
                    rel_path: Path = abs_path.relative_to(self.SRC_DIR)

                    if file.endswith(".py") and not file.startswith("__init__"):
                        module_path: Path = ".".join(rel_path.with_suffix("").parts)
                        target_pyx_path: Path = self.BUILD_TEMP / rel_path.with_suffix(".pyx")
                        target_pyx_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(abs_path, target_pyx_path)

                        extension.append(Extension(
                            name=module_path,
                            sources=[str(target_pyx_path)]
                        ))
                    elif file == "__init__.py" or abs_path == self.ENTRY_POINT.resolve():
                        target_path = self.OUTPUT_DIR / rel_path
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(abs_path, target_path)
                    else:
                        # Non-Python file -> copy to Output_Dir
                        target_data_path: Path = self.OUTPUT_DIR / rel_path
                        target_data_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(abs_path, target_data_path)
            # -----------------------
            # Build the extensions
            #------------------------
            setup(
                script_args=["build_ext", "--build-lib", str(self.OUTPUT_DIR)],
                ext_modules=cythonize(
                    extension,
                    compiler_directives = {"language_level": "3"},
                    build_dir=str(self.BUILD_TEMP / "cython_c_build"),
                )
            )

            self.finished.emit()
        except Exception as e:
            print(f"Encountered the following error\n{e}")
            self.error.emit(e)
        finally:
            self.temp_dir_obj.cleanup()



