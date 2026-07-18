"""02_LAYER1_SPECS/08_MARKET_REGIME.md — kind=direct, komponen leaf."""
from __future__ import annotations

from ..contracts import ComponentReading
from ..sources import yahoo
from ._util import ev, missing, source, th

NAME = "market_regime"

RAW_SCORE = {"bull": 90.0, "sideways": 50.0, "bear": 10.0}


def compute() -> ComponentReading:
    try:
        df = yahoo.history("^GSPC", period="2y")
        close = df["Close"]
        current = float(close.iloc[-1])
        ma50 = float(close.rolling(50).mean().iloc[-1])
        ma200 = float(close.rolling(200).mean().iloc[-1])
        as_of = df.index[-1].strftime("%Y-%m-%d")
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
    rule = "price > MA50 > MA200 → bull; price < MA50 < MA200 → bear; selain itu → sideways"

    return ComponentReading(
        name=NAME,
        value={"regime": regime, "price": current, "ma50": ma50, "ma200": ma200,
               "distance_to_ma200_pct": dist_ma200_pct},
        status="ok",
        kind="direct",
        sources=[source("Yahoo Finance")],
        narrative=narrative,
        narrative_version="1.0.0",
        evidence=[
            ev("price", current, as_of, "Yahoo Finance ^GSPC"),
            ev("ma50", ma50, as_of, "Yahoo Finance ^GSPC (rolling 50d)"),
            ev("ma200", ma200, as_of, "Yahoo Finance ^GSPC (rolling 200d)"),
        ],
        rule=rule,
        thresholds=[],  # klasifikasi ini urutan MA, bukan angka ambang tunggal
        raw_score=RAW_SCORE[regime],
    )
