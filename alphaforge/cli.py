"""CLI: python -m alphaforge.cli <layer1|screening> [opsi]"""
from __future__ import annotations

import argparse
import json
import sys

from .layer1 import build_market_context_package
from .layer2 import run_screening


def _write(data: str, out: str | None) -> None:
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(data)
        print(f"Ditulis ke {out}", file=sys.stderr)
    else:
        print(data)


def main() -> None:
    parser = argparse.ArgumentParser(prog="alphaforge")
    sub = parser.add_subparsers(dest="command", required=True)

    layer1_parser = sub.add_parser("layer1", help="Hitung Market Context Package")
    layer1_parser.add_argument("--out", type=str, default=None, help="Tulis JSON ke file (default: stdout)")
    layer1_parser.add_argument("--with-screening", action="store_true",
                                help="Jalankan Screening dulu supaya market_breadth bisa dihitung (lambat)")
    layer1_parser.add_argument("--screening-limit", type=int, default=None,
                                help="Batasi jumlah ticker yang di-screening (buat testing)")

    screening_parser = sub.add_parser("screening", help="Jalankan Screening (Layer 2, tahap 1)")
    screening_parser.add_argument("--out", type=str, default=None, help="Tulis JSON ke file (default: stdout)")
    screening_parser.add_argument("--limit", type=int, default=None,
                                   help="Batasi jumlah ticker yang di-screening (buat testing)")

    args = parser.parse_args()

    if args.command == "layer1":
        price_cache = None
        if args.with_screening:
            print("Menjalankan Screening dulu untuk mengisi cache market_breadth...", file=sys.stderr)
            _, price_cache = run_screening(limit=args.screening_limit)
            print(f"Screening selesai: {len(price_cache)} ticker di cache harga.", file=sys.stderr)
        package = build_market_context_package(price_cache=price_cache)
        _write(json.dumps(package.to_dict(), indent=2, ensure_ascii=False), args.out)

    elif args.command == "screening":
        result, _ = run_screening(limit=args.limit)
        print(
            f"Universe mentah: {result.universe_raw} · setelah filter tipe: "
            f"{result.universe_after_cheap_filter} · di-scan: {result.universe_scanned} · "
            f"lolos: {len(result.passed)} · hard exclude: {len(result.hard_excluded)}",
            file=sys.stderr,
        )
        _write(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), args.out)


if __name__ == "__main__":
    main()
