"""02_LAYER1_SPECS/07_VOLATILITY_INDEX.md — kind=direct, komponen leaf."""
from __future__ import annotations

from ..contracts import ComponentReading
from ..sources import yahoo
from ._util import ev, missing, source, th

NAME = "volatility_index"

# raw_score: low=80 (calm, favorable for risk assets, tapi tidak 100 karena
# VIX yang terlalu rendah kadang mendahului lonjakan volatilitas), normal=55,
# high=15 (fear, headwind kuat buat risk assets).
RAW_SCORE = {"low": 80.0, "normal": 55.0, "high": 15.0}


def compute() -> ComponentReading:
    try:
        df = yahoo.history("^VIX", period="5y")
        current = float(df["Close"].iloc[-1])
        avg_5y = float(df["Close"].mean())
        as_of = df.index[-1].strftime("%Y-%m-%d")
    except Exception as exc:
        return missing(NAME, "direct", f"Yahoo ^VIX gagal ditarik: {exc}")

    if current < avg_5y * 0.85:
        level = "low"
    elif current > avg_5y * 1.25:
        level = "high"
    else:
        level = "normal"

    narrative = f"VIX {current:.1f}, {level} relatif terhadap rata-rata 5 tahun ({avg_5y:.1f})."
    rule = "VIX < 85% rata-rata 5th → low; VIX > 125% rata-rata 5th → high; selain itu → normal"

    return ComponentReading(
        name=NAME,
        value={"vix": current, "avg_5y": avg_5y, "level": level},
        status="ok",
        kind="direct",
        sources=[source("Yahoo Finance")],
        narrative=narrative,
        narrative_version="1.0.0",
        evidence=[
            ev("vix", current, as_of, "Yahoo Finance ^VIX"),
            ev("avg_5y", avg_5y, as_of, "Yahoo Finance ^VIX (rolling 5y mean)"),
        ],
        rule=rule,
        thresholds=[
            th("low jika VIX di bawah rata-rata 5y ×", "<", 0.85),
            th("high jika VIX di atas rata-rata 5y ×", ">", 1.25),
        ],
        raw_score=RAW_SCORE[level],
    )
