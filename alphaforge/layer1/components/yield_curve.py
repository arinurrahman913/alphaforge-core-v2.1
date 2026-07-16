"""02_LAYER1_SPECS/05_YIELD_CURVE.md — kind=direct, komponen leaf."""
from __future__ import annotations

from ..contracts import ComponentReading
from ..sources import fred
from ._util import missing, source

NAME = "yield_curve"


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

    return ComponentReading(
        name=NAME,
        value={"spread_10y_2y": spread, "shape": shape, "as_of": date},
        status="ok",
        kind="direct",
        sources=[source("FRED")],
        narrative=narrative,
        narrative_version="1.0.0",
    )
