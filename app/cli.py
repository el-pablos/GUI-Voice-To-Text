"""CLI entry point untuk batch transkrip lewat terminal."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from app.core.pipeline import run_batch, run_pipeline

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="transkrip",
        description="Transkrip wawancara/sidang dari audio/video ke teks — CLI mode.",
    )
    parser.add_argument("input", nargs="+", help="File atau folder audio/video yang mau ditranskrip.")
    parser.add_argument("-o", "--output-dir", default="output", help="Folder output (default: output/).")
    parser.add_argument("-f", "--format", nargs="+", default=["txt"], help="Format export: txt md srt vtt json docx.")
    parser.add_argument("-l", "--language", default="id", help="Kode bahasa (default: id).")
    parser.add_argument("-m", "--model", default="base", help="Model size: tiny/base/small/medium/large-v3.")
    parser.add_argument("--no-cache", action="store_true", help="Skip Redis cache.")
    parser.add_argument("--remove-filler", action="store_true", help="Hapus filler words (eee, anu).")
    parser.add_argument("--diarization", choices=["none", "heuristic"], default="none", help="Mode speaker label.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Tampilkan log verbose.")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    print("🎙️ Transkrip Wawancara — CLI Mode")
    print(f"   Bahasa: {args.language} | Model: {args.model} | Format: {', '.join(args.format)}")
    print()

    all_results = []

    for input_path in args.input:
        p = Path(input_path)

        if p.is_dir():
            # Batch mode
            print(f"📁 Batch folder: {p}")
            results = run_batch(
                input_dir=p,
                output_dir=args.output_dir,
                formats=args.format,
                language=args.language,
                model_size=args.model,
                use_cache=not args.no_cache,
                remove_filler=args.remove_filler,
                diarization_mode=args.diarization,
            )
            all_results.extend(results)
        elif p.is_file():
            print(f"🎵 File: {p.name}")
            try:
                result = run_pipeline(
                    input_path=p,
                    output_dir=args.output_dir,
                    formats=args.format,
                    language=args.language,
                    model_size=args.model,
                    use_cache=not args.no_cache,
                    remove_filler=args.remove_filler,
                    diarization_mode=args.diarization,
                )
                all_results.append(result)
                print(f"   ✅ Selesai ({result['segments_count']} segmen, {result['duration']:.1f}s)")
                for f in result["exported_files"]:
                    print(f"   📄 {f}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                all_results.append({"input": str(p), "error": str(e)})
        else:
            print(f"   ⚠️ '{input_path}' bukan file atau folder valid")

    # Summary
    success = sum(1 for r in all_results if "error" not in r)
    print(f"\n📊 Selesai: {success}/{len(all_results)} berhasil")


if __name__ == "__main__":
    main()
