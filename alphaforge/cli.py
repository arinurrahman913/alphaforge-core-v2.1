"""CLI: python -m alphaforge.cli <layer1|screening> [opsi]"""
from __future__ import annotations

import argparse
import json
import sys

from .layer1 import build_market_context_package
from .layer2 import run_screening, run_evidence


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

    evidence_parser = sub.add_parser("evidence", help="Jalankan Evidence (Layer 2, tahap 2) — butuh Screening dulu")
    evidence_parser.add_argument("--screening-out", type=str, required=True,
                                help="Path ke screening.json hasil Screening")
    evidence_parser.add_argument("--out", type=str, default=None, help="Tulis JSON ke file (default: stdout)")
    evidence_parser.add_argument("--limit", type=int, default=None,
                                help="Batasi jumlah ticker yang di-evidence (buat testing)")

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

    elif args.command == "evidence":
        with open(args.screening_out, "r", encoding="utf-8") as f:
            screening_dict = json.load(f)

        # Reconstruct ScreeningResult dari dict
        from .layer2.contracts import ScreeningCandidate, ScreeningResult
        screening_result = ScreeningResult(
            universe_raw=screening_dict["universe_raw"],
            universe_after_cheap_filter=screening_dict["universe_after_cheap_filter"],
            universe_scanned=screening_dict["universe_scanned"],
            passed=[ScreeningCandidate(**c) for c in screening_dict["passed"]],
            hard_excluded=[ScreeningCandidate(**c) for c in screening_dict["hard_excluded"]],
            generated_at=screening_dict["generated_at"]
        )

        # Apply limit jika ada
        if args.limit:
            screening_result.passed = screening_result.passed[:args.limit]

        packages = run_evidence(screening_result)
        result_dict = {
            "screening_universe": screening_result.universe_raw,
            "screening_passed": len(screening_result.passed),
            "evidence_generated": len(packages),
            "generated_at": packages[0].generated_at if packages else None,
            "packages": [p.to_dict() for p in packages],
        }
        _write(json.dumps(result_dict, indent=2, ensure_ascii=False), args.out)


if __name__ == "__main__":
    main()
