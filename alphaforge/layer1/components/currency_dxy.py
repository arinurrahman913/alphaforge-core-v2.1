"""02_LAYER1_SPECS/10_CURRENCY_DXY.md — kind=direct, komponen leaf."""
from __future__ import annotations

from ..contracts import ComponentReading
from ..sources import yahoo
from ._util import missing, source

NAME = "currency_dxy"


def compute() -> ComponentReading:
    try:
        current = yahoo.last_close("DX-Y.NYB")
        chg_30d = yahoo.pct_change("DX-Y.NYB", days=30, period="6mo")
    except Exception as exc:
        return missing(NAME, "direct", f"Yahoo DX-Y.NYB gagal ditarik: {exc}")

    direction = "menguat" if chg_30d > 0 else "melemah"
    narrative = f"DXY {current:.2f}, {direction} {abs(chg_30d):.1f}% dalam 30 hari."

    return ComponentReading(
        name=NAME,
        value={"dxy": current, "change_30d_pct": chg_30d},
        status="ok",
        kind="direct",
        sources=[source("Yahoo Finance")],
        narrative=narrative,
        narrative_version="1.0.0",
    )
