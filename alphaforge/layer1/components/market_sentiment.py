"""02_LAYER1_SPECS/12_MARKET_SENTIMENT.md — kind=derived, satu-satunya
composite Layer 1 (butuh VIX + Market Breadth, wajib dihitung terakhir).

Catatan jujur: AAII Investor Sentiment Survey dan CBOE Put/Call Ratio belum
diintegrasikan di repo ini (keduanya tidak punya API resmi gratis — lihat
04_DATA_SOURCES/01_PROVIDERS_OVERVIEW.md §2b; mengintegrasikannya butuh
scraping yang belum diverifikasi amannya). Sampai itu ada, komponen ini
dihitung cuma dari VIX + Market Breadth (2 dari 4 input spec), dan SELALU
`status=degraded` (tidak pernah `ok`) sampai AAII+put/call terpasang —
supaya tidak diam-diam terlihat lengkap.
"""
from __future__ import annotations

from ..contracts import ComponentReading

NAME = "market_sentiment"
METHOD_VERSION = "1.0.0"

MISSING_INPUTS_ALWAYS = ["aaii_survey", "put_call_ratio"]  # belum diintegrasikan


def compute(vix_reading: ComponentReading, breadth_reading: ComponentReading) -> ComponentReading:
    missing_inputs = list(MISSING_INPUTS_ALWAYS)
    available = []

    if vix_reading.status == "ok":
        available.append(("vix", vix_reading.value["level"]))
    else:
        missing_inputs.append("vix")

    if breadth_reading.status == "ok":
        available.append(("market_breadth", breadth_reading.value["pct_above_ma200"]))
    else:
        missing_inputs.append("market_breadth")

    if not available:
        return ComponentReading(
            name=NAME,
            value=None,
            status="missing",
            kind="derived",
            method_version=METHOD_VERSION,
            inputs=["volatility_index", "market_breadth"],
            note=f"Tidak ada input tersedia — hilang: {', '.join(missing_inputs)}.",
        )

    # skala kasar 0 (extreme fear) - 100 (extreme greed) dari input yang tersedia
    scores = []
    for name, val in available:
        if name == "vix":
            scores.append({"low": 75, "normal": 50, "high": 20}[val])
        elif name == "market_breadth":
            scores.append(min(100, max(0, val)))
    score = sum(scores) / len(scores)

    if score >= 65:
        label = "greed"
    elif score <= 35:
        label = "fear"
    else:
        label = "neutral"

    narrative = (
        f"Skor sentimen kasar {score:.0f}/100 ({label}), dihitung dari {len(available)} dari 4 input spec "
        f"({', '.join(n for n, _ in available)}). Hilang: {', '.join(missing_inputs)}."
    )

    return ComponentReading(
        name=NAME,
        value={"score_0_100": score, "label": label, "inputs_used": [n for n, _ in available]},
        status="degraded",
        kind="derived",
        method_version=METHOD_VERSION,
        inputs=["volatility_index", "market_breadth"],
        note=f"AAII survey & put/call ratio belum diintegrasikan (lihat docstring modul). "
             f"Hilang: {', '.join(missing_inputs)}.",
        narrative=narrative,
        narrative_version="1.0.0",
    )
