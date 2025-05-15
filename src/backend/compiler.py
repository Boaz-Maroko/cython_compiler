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

    def __init__(self, SRC_DIR: Path, OUTPUT_DIR: Path, ENTRY_POINT: Path = None,):
        super().__init__()
        self.setObjectName("Compiler")
        self.SRC_DIR: Path = SRC_DIR
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.BUILD_TEMP: Path = Path(self.temp_dir_obj.name)
        self.OUTPUT_DIR: Path = Path(OUTPUT_DIR)
        self.ENTRY_POINT = Path(ENTRY_POINT).resolve()

        if self.OUTPUT_DIR.exists():
            shutil.rmtree(self.OUTPUT_DIR, ignore_errors=True)
        

    def run(self):
        extension: List = []
        ignored_dirs: set = {"__pycache__", ".git", "venv", ".env", "env", ".env"}
        

        try:
            for root, dirs, files in os.walk(self.SRC_DIR):
                # Skip __pycache__ and virtual environment folders
                dirs[:] = [
                    d for d in dirs if d not in ignored_dirs and not d.endswith(("env", "venv")) and not self._is_venv_dir(root, d)
                    ]

                for file in files:
                    if file.endswith((".pyc", ".pyo")):
                        continue


                    abs_path: Path = Path(root) / file
                    rel_path: Path = abs_path.relative_to(self.SRC_DIR)

                    if Path(file).resolve() == self.ENTRY_POINT:
                        target_path: Path = self.OUTPUT_DIR / rel_path
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(abs_path, target_path)
                    elif file.endswith(".py") and not file.startswith("__init__"):
                        module_path: Path = ".".join(rel_path.with_suffix("").parts)
                        target_pyx_path: Path = self.BUILD_TEMP / rel_path.with_suffix(".pyx")
                        target_pyx_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(abs_path, target_pyx_path)

                        extension.append(Extension(
                            name=module_path,
                            sources=[str(target_pyx_path)]
                        ))
                    elif file == "__init__.py":
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

    def _is_venv_dir(self, root: str, dirname: str):
        venv_indicators: set = {"pyvenv.cfg", "Scripts", "bin", "lib", "Lib"}
        dir_path = Path(root) / dirname
        return any((dir_path / indicator).exists() for indicator in venv_indicators)




