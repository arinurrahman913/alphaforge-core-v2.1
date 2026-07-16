"""CLI: python -m alphaforge.cli layer1 [--out path.json]"""
from __future__ import annotations

import argparse
import json
import sys

from .layer1 import build_market_context_package


def main() -> None:
    parser = argparse.ArgumentParser(prog="alphaforge")
    sub = parser.add_subparsers(dest="command", required=True)

    layer1_parser = sub.add_parser("layer1", help="Hitung Market Context Package")
    layer1_parser.add_argument("--out", type=str, default=None, help="Tulis JSON ke file (default: stdout)")

    args = parser.parse_args()

    if args.command == "layer1":
        package = build_market_context_package()
        data = json.dumps(package.to_dict(), indent=2, ensure_ascii=False)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(data)
            print(f"Ditulis ke {args.out}", file=sys.stderr)
        else:
            print(data)


if __name__ == "__main__":
    main()
