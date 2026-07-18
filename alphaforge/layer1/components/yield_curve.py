"""02_LAYER1_SPECS/05_YIELD_CURVE.md — kind=direct, komponen leaf."""
from __future__ import annotations

from ..contracts import ComponentReading
from ..sources import fred
from ._util import ev, missing, source, th

NAME = "yield_curve"

# raw_score: normal=100 (no recession-risk signal), flat=50, inverted=0
# (inversi 10Y-2Y adalah salah satu leading indicator resesi paling
# dipakai luas — lihat catatan di 02_LAYER1_SPECS/05_YIELD_CURVE.md).
RAW_SCORE = {"normal": 100.0, "flat": 50.0, "inverted": 0.0}


def compute() -> ComponentReading:
    try:
        date, spread = fred.latest_observation("T10Y2Y")
    except Exception as exc:
        return missing(NAME, "direct", f"FRED T10Y2Y gagal ditarik: {exc}")

    if spread < 0:
        shape = "inverted"
    elif spread < 0.25:
        shape = "flat"
    else:
        shape = "normal"

    narrative = f"Spread 10Y-2Y {spread:+.2f}pp per {date} — kurva {shape}."
    rule = "spread < 0 → inverted; 0 ≤ spread < 0.25pp → flat; spread ≥ 0.25pp → normal"

    return ComponentReading(
        name=NAME,
        value={"spread_10y_2y": spread, "shape": shape, "as_of": date},
        status="ok",
        kind="direct",
        sources=[source("FRED")],
        narrative=narrative,
        narrative_version="1.0.0",
        evidence=[ev("spread_10y_2y", spread, date, "FRED T10Y2Y")],
        rule=rule,
        thresholds=[
            th("inverted jika spread di bawah ini", "<", 0.0),
            th("flat jika spread di bawah ini", "<", 0.25),
        ],
        raw_score=RAW_SCORE[shape],
    )
