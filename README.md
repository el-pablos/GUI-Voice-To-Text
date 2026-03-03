# 🎙️ Transkrip Wawancara — Voice to Text

[![CI](https://github.com/el-pablos/transkrip-wawancara-exe/actions/workflows/ci.yml/badge.svg)](https://github.com/el-pablos/transkrip-wawancara-exe/actions/workflows/ci.yml)
[![Release](https://github.com/el-pablos/transkrip-wawancara-exe/actions/workflows/release.yml/badge.svg)](https://github.com/el-pablos/transkrip-wawancara-exe/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Windows 10/11](https://img.shields.io/badge/platform-Windows%2010%2F11-0078d4.svg)]()

> **Tool desktop Windows buat transkrip wawancara, sidang skripsi, atau rapat dari file audio/video jadi teks, subtitle, dan dokumen — offline-first, caching Redis, auto release `.exe` portable.**

---

## 📋 Untuk Siapa?

- **Mahasiswa** yang butuh transkrip hasil sidang skripsi / wawancara penelitian
- **Peneliti** yang perlu konversi rekaman FGD / wawancara mendalam
- **Dosen / penguji** yang ingin review hasil sidang
- **Siapa saja** yang butuh konversi audio/video → teks dengan cepat dan _offline_

---

## ✨ Fitur Utama

| Fitur | Keterangan |
|-------|-----------|
| 🎵 **Multi-format input** | WAV, MP3, M4A, AAC, OGG, FLAC, WMA, MP4, MKV, MOV, AVI, WEBM |
| 📄 **Multi-format output** | TXT, Markdown, SRT, VTT, JSON, DOCX |
| 🧠 **Offline-first** | Pakai [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — tidak butuh internet |
| 🗣️ **Speaker label** | Heuristic diarization (pemisahan speaker otomatis berdasarkan jeda) |
| 🗄️ **Redis caching** | File yang sama tidak ditranskrip ulang (hemat waktu) |
| 🖥️ **GUI Desktop** | PySide6 UI — drag & drop, progress bar, konfigurasi visual |
| ⌨️ **CLI batch** | Proses banyak file sekaligus lewat terminal |
| 🧹 **Text cleanup** | Normalisasi spasi, hapus noise token, opsi hapus filler (eee, anu) |
| ⏱️ **Timestamp** | Per kalimat / per segmen |
| 📦 **Portable .exe** | Download 1 file, langsung jalankan — tanpa install Python |

---

## 🏗️ Arsitektur

```
transkrip-wawancara/
├── app/
│   ├── main.py                    # Entry point UI (PySide6)
│   ├── cli.py                     # Entry point CLI (argparse)
│   ├── core/
│   │   ├── hashing.py             # SHA256 hash file + cache key
│   │   ├── ffmpeg.py              # FFmpeg detect, probe, convert
│   │   ├── cache.py               # Redis cache (env-based, fallback aman)
│   │   ├── pipeline.py            # Orchestrator: convert → cache → transcribe → export
│   │   ├── engines/
│   │   │   ├── base.py            # Interface BaseEngine + TranscriptResult
│   │   │   ├── faster_whisper.py  # Default: faster-whisper (CTranslate2)
│   │   │   └── vosk_engine.py     # Fallback: Vosk (ringan)
│   │   ├── exporters/
│   │   │   ├── txt.py, md.py, srt.py, vtt.py
│   │   │   ├── json_export.py, docx_export.py
│   │   └── postprocess/
│   │       ├── cleanup.py         # Normalisasi teks, hapus noise/filler
│   │       └── segmentation.py    # Merge segmen, heuristic diarization
│   └── ui/
│       ├── window.py              # MainWindow PySide6
│       ├── widgets.py             # FileDropZone, ConfigPanel, ProgressPanel
│       └── state.py               # AppState centralized
├── tests/                         # pytest — 96 tests, 100% passed
├── .github/workflows/
│   ├── ci.yml                     # Test + lint otomatis
│   └── release.yml                # Build .exe + auto release + tagging
├── pyproject.toml
├── .env.example
└── .gitignore
```

---

## 🔄 Diagram Alur (Pipeline)

```mermaid
flowchart TD
    A[👤 User pilih file audio/video] --> B[🔧 FFmpeg convert ke WAV 16kHz mono]
    B --> C[🔑 Hitung SHA256 hash file]
    C --> D{🗄️ Redis cache hit?}
    D -- Ya --> E[📋 Ambil transkrip dari cache]
    D -- Tidak --> F[🧠 STT Engine: faster-whisper]
    F --> G[🧹 Postprocess: cleanup + segmentasi]
    G --> H[💾 Simpan hasil ke Redis cache]
    E --> I[📄 Export: TXT / MD / SRT / VTT / JSON / DOCX]
    H --> I
    I --> J[✅ Selesai — buka folder output]
```

---

## 🚀 Cara Pakai

### Opsi 1: Download `.exe` (Paling Gampang)

1. Buka halaman [**Releases**](https://github.com/el-pablos/transkrip-wawancara-exe/releases)
2. Download `TranskripWawancara.exe`
3. Jalankan — selesai! _(butuh FFmpeg di PATH atau taruh di folder `tools/ffmpeg/`)_

### Opsi 2: Jalankan dari Source

```powershell
# Clone repo
git clone https://github.com/el-pablos/transkrip-wawancara-exe.git
cd transkrip-wawancara-exe

# Buat virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e ".[dev]"

# Jalankan UI
python -m app.main

# Atau CLI
python -m app.cli rekaman.mp3 -f txt md srt -l id -m base
```

### CLI Usage

```powershell
# Transkrip 1 file
python -m app.cli "rekaman sidang.mp3" -o output/ -f txt md srt -l id

# Batch folder
python -m app.cli folder_rekaman/ -f txt json -m small

# Dengan opsi lengkap
python -m app.cli file.wav -f txt md srt vtt json docx \
    -l id -m medium --remove-filler --diarization heuristic -v
```

---

## ⚙️ Konfigurasi

### Environment Variables

Copy `.env.example` → `.env` lalu isi:

| Variable | Deskripsi | Default |
|----------|-----------|---------|
| `REDIS_HOST` | Host Redis (kosong = tanpa cache) | _(kosong)_ |
| `REDIS_PORT` | Port Redis | `6379` |
| `REDIS_USER` | Username Redis (opsional) | _(kosong)_ |
| `REDIS_PASSWORD` | Password Redis | _(kosong)_ |
| `REDIS_DB` | Nomor database Redis | `0` |
| `CACHE_TTL_SECONDS` | TTL cache dalam detik | `2592000` (30 hari) |
| `FFMPEG_PATH` | Path ke ffmpeg.exe (opsional) | auto-detect |
| `FFPROBE_PATH` | Path ke ffprobe.exe (opsional) | auto-detect |

> ⚠️ **Jangan commit `.env` ke repo!** File ini sudah ada di `.gitignore`.

### FFmpeg

Tool ini butuh FFmpeg untuk konversi format. Opsi:

1. **Install ke PATH**: Download dari [ffmpeg.org](https://ffmpeg.org/download.html), tambahkan ke PATH
2. **Portable**: Taruh `ffmpeg.exe` dan `ffprobe.exe` di folder `tools/ffmpeg/`
3. **Environment variable**: Set `FFMPEG_PATH` di `.env`

---

## 🧪 Testing

```powershell
# Run semua test
python -m pytest -q

# Dengan coverage
python -m pytest --cov=app --cov-report=term-missing

# Hanya module tertentu
python -m pytest tests/test_hashing.py -v
```

**Status: 96 tests passed, 2 skipped (butuh ffmpeg + fixture besar)**

---

## 🔧 Development

### Tech Stack

| Komponen | Teknologi |
|----------|-----------|
| Bahasa | Python 3.11+ |
| GUI | PySide6 (Qt6) |
| STT Engine | faster-whisper (CTranslate2) |
| Caching | Redis (via `redis-py`) |
| Konversi Media | FFmpeg |
| Export DOCX | python-docx |
| Testing | pytest + pytest-cov |
| Lint | ruff |
| Packaging | PyInstaller |
| CI/CD | GitHub Actions |

### Model Whisper

| Model | Ukuran | Kecepatan | Akurasi |
|-------|--------|-----------|---------|
| `tiny` | ~75 MB | ⚡⚡⚡ | ⭐⭐ |
| `base` | ~150 MB | ⚡⚡ | ⭐⭐⭐ |
| `small` | ~500 MB | ⚡ | ⭐⭐⭐⭐ |
| `medium` | ~1.5 GB | 🐢 | ⭐⭐⭐⭐⭐ |
| `large-v3` | ~3 GB | 🐌 | ⭐⭐⭐⭐⭐+ |

> **Rekomendasi**: `base` untuk sidang biasa, `small`/`medium` untuk akurasi tinggi.

---

## 🤝 Kontributor

| | Nama | GitHub |
|---|------|--------|
| 🧑‍💻 | el-pablos | [@el-pablos](https://github.com/el-pablos) |

---

## 📄 Lisensi

MIT License — bebas dipakai, dimodifikasi, dan didistribusikan.

---

<p align="center">
  <sub>Dibuat dengan ☕ untuk mahasiswa Indonesia yang butuh transkrip sidang skripsi.</sub>
</p>
