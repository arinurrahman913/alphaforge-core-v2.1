"""02_LAYER1_SPECS/08_MARKET_REGIME.md — kind=direct, komponen leaf."""
from __future__ import annotations

from ..contracts import ComponentReading
from ..sources import yahoo
from ._util import missing, source

NAME = "market_regime"


def compute() -> ComponentReading:
    try:
        df = yahoo.history("^GSPC", period="2y")
        close = df["Close"]
        current = float(close.iloc[-1])
        ma50 = float(close.rolling(50).mean().iloc[-1])
        ma200 = float(close.rolling(200).mean().iloc[-1])
    except Exception as exc:
        return missing(NAME, "direct", f"Yahoo ^GSPC gagal ditarik: {exc}")

    if current > ma50 > ma200:
        regime = "bull"
    elif current < ma50 < ma200:
        regime = "bear"
    else:
        regime = "sideways"

    dist_ma200_pct = (current - ma200) / ma200 * 100.0
    narrative = f"S&P 500 {current:,.0f}, {regime}. Jarak ke MA200: {dist_ma200_pct:+.1f}%."

    return ComponentReading(
        name=NAME,
        value={"regime": regime, "price": current, "ma50": ma50, "ma200": ma200,
               "distance_to_ma200_pct": dist_ma200_pct},
        status="ok",
        kind="direct",
        sources=[source("Yahoo Finance")],
        narrative=narrative,
        narrative_version="1.0.0",
    )
