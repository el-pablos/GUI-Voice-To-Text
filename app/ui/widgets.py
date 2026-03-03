"""Custom widgets untuk GUI Voice To Text — modern responsive layout."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.ffmpeg import SUPPORTED_EXTENSIONS


# ────────────────────────────────────────────────────────────────
# Drop Area — area drag & drop visual
# ────────────────────────────────────────────────────────────────
class FileDropZone(QFrame):
    """Area drag-and-drop dengan indikator visual."""

    files_dropped = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(80)
        self.setMaximumHeight(100)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel("📂")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 28px; border: none; background: transparent;")
        layout.addWidget(icon_label)

        text_label = QLabel("Seret file audio/video ke sini")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet("font-size: 12px; color: #888; border: none; background: transparent;")
        layout.addWidget(text_label)

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        files: list[Path] = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(path)
            elif path.is_dir():
                for f in sorted(path.iterdir()):
                    if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                        files.append(f)
        if files:
            self.files_dropped.emit(files)


# ────────────────────────────────────────────────────────────────
# File Table — tabel daftar file dengan status
# ────────────────────────────────────────────────────────────────
class FileTable(QTableWidget):
    """Tabel file dengan kolom Nama, Ukuran, Durasi, Status."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, 4, parent)
        self.setHorizontalHeaderLabels(["Nama File", "Ukuran", "Durasi", "Status"])
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

    def add_file(self, path: Path, duration: str = "-", status: str = "Queued") -> None:
        """Tambah baris file ke tabel."""
        row = self.rowCount()
        self.insertRow(row)

        size = _format_size(path.stat().st_size) if path.exists() else "-"

        self.setItem(row, 0, QTableWidgetItem(path.name))
        self.setItem(row, 1, QTableWidgetItem(size))
        self.setItem(row, 2, QTableWidgetItem(duration))
        self.setItem(row, 3, QTableWidgetItem(status))

    def update_status(self, row: int, status: str) -> None:
        """Update kolom status di baris tertentu."""
        if 0 <= row < self.rowCount():
            item = self.item(row, 3)
            if item:
                item.setText(status)

    def update_duration(self, row: int, duration: str) -> None:
        """Update kolom durasi."""
        if 0 <= row < self.rowCount():
            item = self.item(row, 2)
            if item:
                item.setText(duration)

    def get_selected_rows(self) -> list[int]:
        """Dapatkan index baris yang dipilih."""
        return sorted({idx.row() for idx in self.selectedIndexes()})

    def remove_rows(self, rows: list[int]) -> None:
        """Hapus baris-baris (dari terakhir dulu biar index aman)."""
        for row in sorted(rows, reverse=True):
            self.removeRow(row)


# ────────────────────────────────────────────────────────────────
# Config Panel — pengaturan transkrip
# ────────────────────────────────────────────────────────────────
class ConfigPanel(QGroupBox):
    """Panel konfigurasi transkrip, termasuk opsi TXT advanced."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("⚙️ Pengaturan", parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Bahasa
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("Bahasa:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["id", "en", "ja", "zh", "ko", "auto"])
        lang_row.addWidget(self.lang_combo)
        lang_row.addStretch()
        layout.addLayout(lang_row)

        # Model
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large-v3"])
        self.model_combo.setCurrentText("base")
        model_row.addWidget(self.model_combo)
        model_row.addStretch()
        layout.addLayout(model_row)

        # Format export
        fmt_label = QLabel("Format export:")
        layout.addWidget(fmt_label)
        fmt_row = QHBoxLayout()
        self.fmt_checks: dict[str, QCheckBox] = {}
        for fmt in ["txt", "md", "srt", "vtt", "json", "docx"]:
            cb = QCheckBox(fmt.upper())
            if fmt == "txt":
                cb.setChecked(True)
            self.fmt_checks[fmt] = cb
            fmt_row.addWidget(cb)
        layout.addLayout(fmt_row)

        # Opsi umum
        opts_row = QHBoxLayout()
        self.cache_check = QCheckBox("Cache Redis")
        self.cache_check.setChecked(True)
        opts_row.addWidget(self.cache_check)
        self.filler_check = QCheckBox("Hapus filler")
        opts_row.addWidget(self.filler_check)
        layout.addLayout(opts_row)

        # Diarization
        diar_row = QHBoxLayout()
        diar_row.addWidget(QLabel("Speaker:"))
        self.diar_combo = QComboBox()
        self.diar_combo.addItems(["none", "heuristic"])
        diar_row.addWidget(self.diar_combo)
        diar_row.addStretch()
        layout.addLayout(diar_row)

        # Opsi TXT Advanced
        adv_label = QLabel("Opsi TXT Advanced:")
        adv_label.setStyleSheet("margin-top: 8px; font-weight: bold;")
        layout.addWidget(adv_label)

        self.txt_timestamp_check = QCheckBox("Sertakan timestamp di TXT")
        self.txt_timestamp_check.setChecked(False)
        layout.addWidget(self.txt_timestamp_check)

        self.txt_speaker_check = QCheckBox("Sertakan label speaker di TXT")
        self.txt_speaker_check.setChecked(False)
        layout.addWidget(self.txt_speaker_check)

        layout.addStretch()

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

    def get_txt_include_timestamps(self) -> bool:
        return self.txt_timestamp_check.isChecked()

    def get_txt_include_speaker(self) -> bool:
        return self.txt_speaker_check.isChecked()


# ────────────────────────────────────────────────────────────────
# Preview Panel — preview teks hasil transkrip
# ────────────────────────────────────────────────────────────────
class PreviewPanel(QWidget):
    """Panel preview TXT bersih + tombol Copy & Save As."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText("Hasil transkrip akan muncul di sini...")
        layout.addWidget(self.text_edit)

        btn_row = QHBoxLayout()
        self.btn_copy = QPushButton("📋 Copy")
        self.btn_copy.clicked.connect(self._copy_text)
        btn_row.addWidget(self.btn_copy)

        self.btn_save = QPushButton("💾 Save As…")
        btn_row.addWidget(self.btn_save)

        btn_row.addStretch()
        layout.addLayout(btn_row)

    def set_text(self, text: str) -> None:
        """Set teks preview."""
        self.text_edit.setPlainText(text)

    def get_text(self) -> str:
        """Ambil teks preview."""
        return self.text_edit.toPlainText()

    def _copy_text(self) -> None:
        from PySide6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.text_edit.toPlainText())


# ────────────────────────────────────────────────────────────────
# Progress Panel — progress bar + stage info
# ────────────────────────────────────────────────────────────────
class ProgressPanel(QGroupBox):
    """Panel progress bar + info stage + elapsed time."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Progress", parent)
        layout = QVBoxLayout(self)

        # Stage + elapsed time row
        info_row = QHBoxLayout()
        self.stage_label = QLabel("Siap")
        info_row.addWidget(self.stage_label)
        info_row.addStretch()
        self.elapsed_label = QLabel("")
        self.elapsed_label.setStyleSheet("color: #888; font-size: 11px;")
        info_row.addWidget(self.elapsed_label)
        layout.addLayout(info_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        layout.addWidget(self.progress_bar)

        # Detail label for sub-stage info
        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet("color: #999; font-size: 10px;")
        layout.addWidget(self.detail_label)

    def update_progress(self, stage: str, progress: float) -> None:
        self.stage_label.setText(stage)
        self.progress_bar.setValue(int(progress * 100))

    def set_elapsed(self, text: str) -> None:
        """Update elapsed time display."""
        self.elapsed_label.setText(text)

    def set_detail(self, text: str) -> None:
        """Update detail/sub-stage text."""
        self.detail_label.setText(text)

    def reset(self) -> None:
        self.stage_label.setText("Siap")
        self.progress_bar.setValue(0)
        self.elapsed_label.setText("")
        self.detail_label.setText("")


# ────────────────────────────────────────────────────────────────
# Log Panel — log output
# ────────────────────────────────────────────────────────────────
class LogPanel(QWidget):
    """Panel log output dengan timestamp, level colors, dan auto-scroll."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; font-size: 11px;"
        )
        layout.addWidget(self.log_text)

        # Bottom buttons
        btn_row = QHBoxLayout()
        btn_clear = QPushButton("🗑️ Clear Log")
        btn_clear.setFixedWidth(100)
        btn_clear.clicked.connect(lambda: self.log_text.clear())
        btn_row.addWidget(btn_clear)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def append_log(self, message: str, level: str = "INFO") -> None:
        """Append log message with timestamp and color coding."""
        from datetime import datetime

        ts = datetime.now().strftime("%H:%M:%S")
        colors = {
            "DEBUG": "#888888",
            "INFO": "#cccccc",
            "WARNING": "#f0ad4e",
            "ERROR": "#d9534f",
            "CRITICAL": "#d9534f",
            "SUCCESS": "#5cb85c",
        }
        color = colors.get(level, "#cccccc")
        level_short = level[:4].ljust(4)
        html = (
            f'<span style="color:#666">[{ts}]</span> '
            f'<span style="color:{color}">[{level_short}]</span> '
            f'<span style="color:{color}">{message}</span>'
        )
        self.log_text.append(html)

        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


# ────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────
def _format_size(size_bytes: int) -> str:
    """Format ukuran file ke human readable."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
