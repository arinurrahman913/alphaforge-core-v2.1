"""CLI: python -m alphaforge.cli <layer1|screening> [opsi]"""
from __future__ import annotations

import argparse
import json
import sys

from .layer1 import build_market_context_package
from .layer2 import run_screening, run_evidence, run_knowledge


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

    knowledge_parser = sub.add_parser("knowledge", help="Jalankan Knowledge (Layer 2, tahap 3) — butuh Evidence dulu")
    knowledge_parser.add_argument("--evidence-out", type=str, required=True,
                                 help="Path ke evidence.json hasil Evidence")
    knowledge_parser.add_argument("--screening-out", type=str, default=None,
                                 help="Path ke screening.json (optional, untuk supplementary flags)")
    knowledge_parser.add_argument("--out", type=str, default=None, help="Tulis JSON ke file (default: stdout)")
    knowledge_parser.add_argument("--limit", type=int, default=None,
                                 help="Batasi jumlah ticker yang di-knowledge (buat testing)")

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

    elif args.command == "knowledge":
        with open(args.evidence_out, "r", encoding="utf-8") as f:
            evidence_dict = json.load(f)

        # Reconstruct Evidence packages
        from .layer2.contracts import EvidencePackage
        evidence_packages = []
        for pkg_dict in evidence_dict.get("packages", []):
            # Simplified reconstruction (would need more fields in production)
            pkg = EvidencePackage(
                ticker=pkg_dict["ticker"],
                exchange=pkg_dict["exchange"],
                price_market=type('obj', (object,), pkg_dict["price_market"])(),
                fundamental=type('obj', (object,), pkg_dict["fundamental"])(),
                institutional_ownership=type('obj', (object,), pkg_dict["institutional_ownership"])(),
                news=type('obj', (object,), pkg_dict["news"])(),
                sec_filings=type('obj', (object,), pkg_dict["sec_filings"])(),
                generated_at=pkg_dict["generated_at"]
            )
            evidence_packages.append(pkg)

        # Load screening candidates jika ada
        screening_candidates = []
        if args.screening_out:
            with open(args.screening_out, "r", encoding="utf-8") as f:
                screening_dict = json.load(f)
            from .layer2.contracts import ScreeningCandidate
            screening_candidates = [ScreeningCandidate(**c) for c in screening_dict.get("passed", [])]

        # Apply limit
        if args.limit:
            evidence_packages = evidence_packages[:args.limit]

        profiles = run_knowledge(evidence_packages, screening_candidates)
        result_dict = {
            "evidence_count": len(evidence_packages),
            "knowledge_generated": len(profiles),
            "generated_at": profiles[0].metadata.evidence_date if profiles else None,
            "profiles": [p.to_dict() for p in profiles],
        }
        _write(json.dumps(result_dict, indent=2, ensure_ascii=False), args.out)


if __name__ == "__main__":
    main()
