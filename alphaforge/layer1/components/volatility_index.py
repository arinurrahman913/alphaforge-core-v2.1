"""02_LAYER1_SPECS/07_VOLATILITY_INDEX.md — kind=direct, komponen leaf."""
from __future__ import annotations

from ..contracts import ComponentReading
from ..sources import yahoo
from ._util import missing, source

NAME = "volatility_index"


def compute() -> ComponentReading:
    try:
        df = yahoo.history("^VIX", period="5y")
        current = float(df["Close"].iloc[-1])
        avg_5y = float(df["Close"].mean())
    except Exception as exc:
        return missing(NAME, "direct", f"Yahoo ^VIX gagal ditarik: {exc}")

    if current < avg_5y * 0.85:
        level = "low"
    elif current > avg_5y * 1.25:
        level = "high"
    else:
        level = "normal"

    narrative = f"VIX {current:.1f}, {level} relatif terhadap rata-rata 5 tahun ({avg_5y:.1f})."

    return ComponentReading(
        name=NAME,
        value={"vix": current, "avg_5y": avg_5y, "level": level},
        status="ok",
        kind="direct",
        sources=[source("Yahoo Finance")],
        narrative=narrative,
        narrative_version="1.0.0",
    )
