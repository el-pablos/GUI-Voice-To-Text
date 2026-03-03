"""Custom widgets untuk UI Transkrip Wawancara."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.ffmpeg import SUPPORTED_EXTENSIONS


class FileDropZone(QListWidget):
    """Widget drag-and-drop untuk input file audio/video."""

    files_added = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        self.setMinimumHeight(120)
        self.setStyleSheet(
            "QListWidget { border: 2px dashed #888; border-radius: 8px; "
            "background: #f8f8f8; padding: 8px; }"
        )

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        files = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(path)
                self.addItem(str(path))
            elif path.is_dir():
                for f in sorted(path.iterdir()):
                    if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                        files.append(f)
                        self.addItem(str(f))
        if files:
            self.files_added.emit(files)


class ConfigPanel(QGroupBox):
    """Panel konfigurasi transkrip."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Konfigurasi", parent)
        layout = QVBoxLayout(self)

        # Bahasa
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("Bahasa:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["id", "en", "ja", "zh", "ko", "auto"])
        lang_row.addWidget(self.lang_combo)
        layout.addLayout(lang_row)

        # Model
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large-v3"])
        self.model_combo.setCurrentText("base")
        model_row.addWidget(self.model_combo)
        layout.addLayout(model_row)

        # Format export
        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("Format:"))
        self.fmt_checks: dict[str, QCheckBox] = {}
        for fmt in ["txt", "md", "srt", "vtt", "json", "docx"]:
            cb = QCheckBox(fmt)
            if fmt == "txt":
                cb.setChecked(True)
            self.fmt_checks[fmt] = cb
            fmt_row.addWidget(cb)
        layout.addLayout(fmt_row)

        # Opsi
        opts_row = QHBoxLayout()
        self.cache_check = QCheckBox("Gunakan cache Redis")
        self.cache_check.setChecked(True)
        opts_row.addWidget(self.cache_check)
        self.filler_check = QCheckBox("Hapus filler (eee, anu)")
        opts_row.addWidget(self.filler_check)
        layout.addLayout(opts_row)

        # Diarization
        diar_row = QHBoxLayout()
        diar_row.addWidget(QLabel("Speaker:"))
        self.diar_combo = QComboBox()
        self.diar_combo.addItems(["none", "heuristic"])
        diar_row.addWidget(self.diar_combo)
        layout.addLayout(diar_row)

    def get_formats(self) -> list[str]:
        return [fmt for fmt, cb in self.fmt_checks.items() if cb.isChecked()]

    def get_language(self) -> str:
        return self.lang_combo.currentText()

    def get_model(self) -> str:
        return self.model_combo.currentText()

    def get_use_cache(self) -> bool:
        return self.cache_check.isChecked()

    def get_remove_filler(self) -> bool:
        return self.filler_check.isChecked()

    def get_diarization_mode(self) -> str:
        return self.diar_combo.currentText()


class ProgressPanel(QGroupBox):
    """Panel progress bar + info stage."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Progress", parent)
        layout = QVBoxLayout(self)

        self.stage_label = QLabel("Siap")
        layout.addWidget(self.stage_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

    def update_progress(self, stage: str, progress: float) -> None:
        self.stage_label.setText(stage)
        self.progress_bar.setValue(int(progress * 100))

    def reset(self) -> None:
        self.stage_label.setText("Siap")
        self.progress_bar.setValue(0)


class LogPanel(QGroupBox):
    """Panel log output."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Log", parent)
        layout = QVBoxLayout(self)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)

    def append_log(self, message: str) -> None:
        self.log_text.append(message)
