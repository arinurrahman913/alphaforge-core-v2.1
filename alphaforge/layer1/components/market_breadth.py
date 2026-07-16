"""02_LAYER1_SPECS/06_MARKET_BREADTH.md — kind=derived, komponen leaf.

Universe = hasil Screening sendiri (D-05), bukan S&P 500 — lihat spec.
Screening/cache harga belum diimplementasikan di repo ini, jadi komponen
ini sengaja `status=missing` daripada memicu ribuan panggilan Yahoo sendiri
(larangan eksplisit di spec: "bukan memicu ribuan call sendiri").

Begitu `03_LAYER2_SPECS/01_SCREENING.md` + cache harga (`04_DATA_SOURCES/
05_RATE_LIMIT_CACHING_STRATEGY.md`) ada, panggil `compute(price_cache=...)`
dengan cache itu.
"""
from __future__ import annotations

from ..contracts import ComponentReading
from ._util import missing

NAME = "market_breadth"
METHOD_VERSION = "1.0.0"


def compute(price_cache: dict | None = None) -> ComponentReading:
    if price_cache is None:
        return missing(
            NAME,
            "derived",
            "Cache harga universe Screening belum terisi — Screening belum diimplementasikan.",
            method_version=METHOD_VERSION,
        )

    advances = 0
    declines = 0
    above_ma200 = 0
    total = 0
    for ticker, df in price_cache.items():
        if df is None or len(df) < 200:
            continue
        close = df["Close"]
        total += 1
        if float(close.iloc[-1]) > float(close.iloc[-2]):
            advances += 1
        else:
            declines += 1
        if float(close.iloc[-1]) > float(close.rolling(200).mean().iloc[-1]):
            above_ma200 += 1

    if total == 0:
        return missing(NAME, "derived", "Cache harga tidak punya histori cukup (>=200 hari).",
                        method_version=METHOD_VERSION)

    pct_above_ma200 = above_ma200 / total * 100.0
    narrative = (
        f"{advances}/{total} saham naik sesi terakhir. {pct_above_ma200:.1f}% di atas MA200. "
        f"Universe: hasil Screening sendiri ({total} ticker), tidak sebanding dengan breadth S&P 500."
    )

    return ComponentReading(
        name=NAME,
        value={
            "advances": advances,
            "declines": declines,
            "pct_above_ma200": pct_above_ma200,
            "universe_size": total,
        },
        status="ok",
        kind="derived",
        method_version=METHOD_VERSION,
        note="Universe = hasil Screening sendiri (D-05), bukan konstituen S&P 500 — tidak sebanding "
             "dengan breadth publik manapun.",
        narrative=narrative,
        narrative_version="1.0.0",
    )
