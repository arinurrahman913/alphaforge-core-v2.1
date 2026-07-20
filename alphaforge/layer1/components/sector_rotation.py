"""02_LAYER1_SPECS/02_SECTOR_ROTATION.md — kind=direct, komponen leaf."""
from __future__ import annotations

from ..contracts import ComponentReading
from ..sources import yahoo
from ._util import ev, missing, source, th

NAME = "sector_rotation"

SECTOR_ETFS = ["XLK", "XLE", "XLF", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
BENCHMARK = "SPY"

# Klasifikasi kasar cyclical vs defensive buat raw_score — XLE/XLB/XLC
# sengaja netral (energi & materials lebih dipengaruhi commodity cycle,
# communication services campuran growth+defensive).
CYCLICAL = {"XLK", "XLY", "XLF", "XLI"}
DEFENSIVE = {"XLP", "XLU", "XLV", "XLRE"}
RAW_SCORE_CYCLICAL_LEADS = 70.0
RAW_SCORE_DEFENSIVE_LEADS = 40.0
RAW_SCORE_NEUTRAL = 55.0


def compute() -> ComponentReading:
    try:
        # Semua fetch pakai period="1y" yang sama supaya berbagi satu entry
        # cache per ticker (dulu 6mo & 1y = dua key = dua unduhan per ETF;
        # money_flow juga kini pakai 1y → ikut reuse cache yang sama).
        bench_df = yahoo.history(BENCHMARK, period="1y")
        as_of = bench_df.index[-1].strftime("%Y-%m-%d")
        bench_1m = yahoo.pct_change(BENCHMARK, days=21, period="1y")
        bench_3m = yahoo.pct_change(BENCHMARK, days=63, period="1y")
        relative = {}
        for etf in SECTOR_ETFS:
            r1m = yahoo.pct_change(etf, days=21, period="1y")
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
    rule = "leader = ETF sektor dengan relative_1m_pct tertinggi vs SPY; laggard = terendah"

    if leader in CYCLICAL:
        raw_score = RAW_SCORE_CYCLICAL_LEADS
    elif leader in DEFENSIVE:
        raw_score = RAW_SCORE_DEFENSIVE_LEADS
    else:
        raw_score = RAW_SCORE_NEUTRAL

    return ComponentReading(
        name=NAME,
        value={"benchmark": BENCHMARK, "sectors": relative, "leader": leader, "laggard": laggard},
        status="ok",
        kind="direct",
        sources=[source("Yahoo Finance")],
        narrative=narrative,
        narrative_version="1.0.0",
        evidence=[
            ev("leader", leader, as_of, "Yahoo Finance sector ETF (relative 1m vs SPY)"),
            ev("leader_relative_1m_pct", relative[leader]["relative_1m_pct"], as_of, "Yahoo Finance"),
            ev("laggard", laggard, as_of, "Yahoo Finance sector ETF (relative 1m vs SPY)"),
        ],
        rule=rule,
        thresholds=[
            th(f"cyclical leads → score {RAW_SCORE_CYCLICAL_LEADS:.0f} (XLK/XLY/XLF/XLI)", "in", 0),
            th(f"defensive leads → score {RAW_SCORE_DEFENSIVE_LEADS:.0f} (XLP/XLU/XLV/XLRE)", "in", 0),
        ],
        raw_score=raw_score,
    )
