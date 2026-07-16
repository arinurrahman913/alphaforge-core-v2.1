"""02_LAYER1_SPECS/02_SECTOR_ROTATION.md — kind=direct, komponen leaf."""
from __future__ import annotations

from ..contracts import ComponentReading
from ..sources import yahoo
from ._util import missing, source

NAME = "sector_rotation"

SECTOR_ETFS = ["XLK", "XLE", "XLF", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
BENCHMARK = "SPY"


def compute() -> ComponentReading:
    try:
        bench_1m = yahoo.pct_change(BENCHMARK, days=21, period="6mo")
        bench_3m = yahoo.pct_change(BENCHMARK, days=63, period="1y")
        relative = {}
        for etf in SECTOR_ETFS:
            r1m = yahoo.pct_change(etf, days=21, period="6mo")
            r3m = yahoo.pct_change(etf, days=63, period="1y")
            relative[etf] = {
                "return_1m_pct": r1m,
                "return_3m_pct": r3m,
                "relative_1m_pct": r1m - bench_1m,
                "relative_3m_pct": r3m - bench_3m,
            }
    except Exception as exc:
        return missing(NAME, "direct", f"Yahoo sector ETF gagal ditarik: {exc}")

    leader = max(relative, key=lambda k: relative[k]["relative_1m_pct"])
    laggard = min(relative, key=lambda k: relative[k]["relative_1m_pct"])

    narrative = (
        f"{leader} memimpin relatif terhadap {BENCHMARK} ({relative[leader]['relative_1m_pct']:+.1f}pp/1bln), "
        f"{laggard} tertinggal ({relative[laggard]['relative_1m_pct']:+.1f}pp/1bln)."
    )

    return ComponentReading(
        name=NAME,
        value={"benchmark": BENCHMARK, "sectors": relative, "leader": leader, "laggard": laggard},
        status="ok",
        kind="direct",
        sources=[source("Yahoo Finance")],
        narrative=narrative,
        narrative_version="1.0.0",
    )
