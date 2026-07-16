"""02_LAYER1_SPECS/11_COMMODITY_SIGNALS.md — kind=direct, komponen leaf."""
from __future__ import annotations

from ..contracts import ComponentReading
from ..sources import yahoo
from ._util import missing, source

NAME = "commodity_signals"


def compute() -> ComponentReading:
    try:
        gold = yahoo.last_close("GC=F")
        gold_chg = yahoo.pct_change("GC=F", days=30, period="6mo")
        wti = yahoo.last_close("CL=F")
        wti_chg = yahoo.pct_change("CL=F", days=30, period="6mo")
    except Exception as exc:
        return missing(NAME, "direct", f"Yahoo futures gagal ditarik: {exc}")

    narrative = (
        f"Emas {gold:,.0f} ({gold_chg:+.1f}% 30h), WTI {wti:,.2f} ({wti_chg:+.1f}% 30h)."
    )

    return ComponentReading(
        name=NAME,
        value={
            "gold": gold,
            "gold_change_30d_pct": gold_chg,
            "wti": wti,
            "wti_change_30d_pct": wti_chg,
        },
        status="ok",
        kind="direct",
        sources=[source("Yahoo Finance")],
        narrative=narrative,
        narrative_version="1.0.0",
    )
