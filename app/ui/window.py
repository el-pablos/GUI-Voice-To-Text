"""Main window UI — PySide6 desktop application."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.pipeline import run_pipeline
from app.ui.state import AppState
from app.ui.widgets import ConfigPanel, FileDropZone, LogPanel, ProgressPanel

logger = logging.getLogger(__name__)


class TranscribeWorker(QObject):
    """Worker thread buat transkrip supaya UI tidak freeze."""

    progress = Signal(str, float)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, file_path: Path, state: AppState) -> None:
        super().__init__()
        self.file_path = file_path
        self.state = state

    @Slot()
    def run(self) -> None:
        try:
            result = run_pipeline(
                input_path=self.file_path,
                output_dir=self.state.output_dir,
                formats=self.state.formats,
                language=self.state.language,
                model_size=self.state.model_size,
                use_cache=self.state.use_cache,
                remove_filler=self.state.remove_filler,
                diarization_mode=self.state.diarization_mode,
                progress_callback=self._on_progress,
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    def _on_progress(self, stage: str, progress: float) -> None:
        self.progress.emit(stage, progress)


class MainWindow(QMainWindow):
    """Window utama Transkrip Wawancara."""

    def __init__(self) -> None:
        super().__init__()
        self.state = AppState()
        self._threads: list[QThread] = []

        self.setWindowTitle("Transkrip Wawancara — Voice to Text")
        self.setMinimumSize(700, 600)

        self._setup_ui()
        self._setup_logging()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # File drop zone
        self.drop_zone = FileDropZone()
        self.drop_zone.files_added.connect(self._on_files_added)
        layout.addWidget(self.drop_zone)

        # Buttons row
        btn_row = QHBoxLayout()
        self.btn_browse = QPushButton("📂 Pilih File")
        self.btn_browse.clicked.connect(self._browse_files)
        btn_row.addWidget(self.btn_browse)

        self.btn_folder = QPushButton("📁 Pilih Folder")
        self.btn_folder.clicked.connect(self._browse_folder)
        btn_row.addWidget(self.btn_folder)

        self.btn_output = QPushButton("💾 Folder Output")
        self.btn_output.clicked.connect(self._set_output_dir)
        btn_row.addWidget(self.btn_output)

        self.btn_clear = QPushButton("🗑️ Bersihkan")
        self.btn_clear.clicked.connect(self._clear_files)
        btn_row.addWidget(self.btn_clear)
        layout.addLayout(btn_row)

        # Config panel
        self.config_panel = ConfigPanel()
        layout.addWidget(self.config_panel)

        # Progress
        self.progress_panel = ProgressPanel()
        layout.addWidget(self.progress_panel)

        # Action buttons
        action_row = QHBoxLayout()
        self.btn_start = QPushButton("▶️ Mulai Transkrip")
        self.btn_start.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "font-size: 14px; padding: 8px 16px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #45a049; }"
            "QPushButton:disabled { background-color: #ccc; }"
        )
        self.btn_start.clicked.connect(self._start_transcribe)
        action_row.addWidget(self.btn_start)

        self.btn_open_output = QPushButton("📂 Buka Output")
        self.btn_open_output.clicked.connect(self._open_output_dir)
        action_row.addWidget(self.btn_open_output)

        self.btn_open_log = QPushButton("📋 Buka Log")
        self.btn_open_log.clicked.connect(self._open_log_dir)
        action_row.addWidget(self.btn_open_log)
        layout.addLayout(action_row)

        # Log panel
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)

    def _setup_logging(self) -> None:
        """Setup logging ke file + UI panel."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

    def _on_files_added(self, files: list[Path]) -> None:
        self.state.input_files.extend(files)
        self.log_panel.append_log(f"Ditambahkan {len(files)} file")

    def _browse_files(self) -> None:
        from app.core.ffmpeg import SUPPORTED_EXTENSIONS

        exts = " ".join(f"*{e}" for e in sorted(SUPPORTED_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Pilih File Audio/Video",
            "",
            f"Media Files ({exts});;All Files (*)",
        )
        if files:
            paths = [Path(f) for f in files]
            for p in paths:
                self.drop_zone.addItem(str(p))
            self.state.input_files.extend(paths)
            self.log_panel.append_log(f"Dipilih {len(paths)} file")

    def _browse_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Pilih Folder Audio/Video")
        if folder:
            from app.core.ffmpeg import SUPPORTED_EXTENSIONS

            folder_path = Path(folder)
            files = [f for f in sorted(folder_path.iterdir())
                     if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]
            for f in files:
                self.drop_zone.addItem(str(f))
            self.state.input_files.extend(files)
            self.log_panel.append_log(f"Folder: {len(files)} file ditemukan")

    def _set_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Pilih Folder Output")
        if folder:
            self.state.output_dir = Path(folder)
            self.log_panel.append_log(f"Output dir: {folder}")

    def _clear_files(self) -> None:
        self.drop_zone.clear()
        self.state.input_files.clear()
        self.progress_panel.reset()
        self.log_panel.append_log("File list dibersihkan")

    def _start_transcribe(self) -> None:
        if not self.state.input_files:
            QMessageBox.warning(self, "Peringatan", "Belum ada file yang dipilih!")
            return

        # Update state dari config panel
        self.state.formats = self.config_panel.get_formats()
        self.state.language = self.config_panel.get_language()
        self.state.model_size = self.config_panel.get_model()
        self.state.use_cache = self.config_panel.get_use_cache()
        self.state.remove_filler = self.config_panel.get_remove_filler()
        self.state.diarization_mode = self.config_panel.get_diarization_mode()

        if not self.state.formats:
            QMessageBox.warning(self, "Peringatan", "Pilih minimal satu format export!")
            return

        self.btn_start.setEnabled(False)
        self.state.is_processing = True
        self.state.results.clear()
        self._process_next_file(0)

    def _process_next_file(self, index: int) -> None:
        if index >= len(self.state.input_files):
            self._on_all_done()
            return

        file_path = self.state.input_files[index]
        self.log_panel.append_log(f"[{index + 1}/{len(self.state.input_files)}] {file_path.name}")

        thread = QThread()
        worker = TranscribeWorker(file_path, self.state)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.progress.connect(self.progress_panel.update_progress)
        worker.finished.connect(lambda r: self._on_file_done(r, index))
        worker.error.connect(lambda e: self._on_file_error(e, index))
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)

        self._threads.append(thread)
        thread.start()

    def _on_file_done(self, result: dict, index: int) -> None:
        self.state.results.append(result)
        self.log_panel.append_log(f"✅ Selesai: {result.get('input', 'unknown')}")
        self._process_next_file(index + 1)

    def _on_file_error(self, error: str, index: int) -> None:
        self.state.results.append({"error": error})
        self.log_panel.append_log(f"❌ Error: {error}")
        self._process_next_file(index + 1)

    def _on_all_done(self) -> None:
        self.state.is_processing = False
        self.btn_start.setEnabled(True)
        self.progress_panel.update_progress("Semua selesai!", 1.0)

        success = sum(1 for r in self.state.results if "error" not in r)
        total = len(self.state.results)
        self.log_panel.append_log(f"Selesai semua! {success}/{total} berhasil.")

        QMessageBox.information(
            self,
            "Selesai",
            f"Transkrip selesai!\n{success}/{total} file berhasil.\nOutput di: {self.state.output_dir}",
        )

    def _open_output_dir(self) -> None:
        path = str(self.state.output_dir.resolve())
        if sys.platform == "win32":
            os.startfile(path)
        else:
            subprocess.Popen(["xdg-open", path])

    def _open_log_dir(self) -> None:
        path = str(Path("logs").resolve())
        if sys.platform == "win32":
            os.startfile(path)
        else:
            subprocess.Popen(["xdg-open", path])
