"""02_LAYER1_SPECS/03_MONEY_FLOW.md — kind=derived, komponen leaf.

Proksi: volume abnormal + arah harga di sector ETF (bukan data flow
institusional presisi seperti EPFR/Lipper, yang berbayar).
"""
from __future__ import annotations

from ..contracts import ComponentReading
from ..sources import yahoo
from ._util import missing, source

NAME = "money_flow"
METHOD_VERSION = "1.0.0"

SECTOR_ETFS = ["XLK", "XLE", "XLF", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]


def compute() -> ComponentReading:
    try:
        flows = {}
        for etf in SECTOR_ETFS:
            df = yahoo.history(etf, period="2mo")
            vol = df["Volume"]
            avg_vol_20d = float(vol.iloc[-21:-1].mean())
            last_vol = float(vol.iloc[-1])
            price_chg = (float(df["Close"].iloc[-1]) - float(df["Close"].iloc[-2])) / float(df["Close"].iloc[-2]) * 100.0
            vol_ratio = last_vol / avg_vol_20d if avg_vol_20d else 0.0
            if vol_ratio > 1.3 and price_chg > 0:
                direction = "inflow"
            elif vol_ratio > 1.3 and price_chg < 0:
                direction = "outflow"
            else:
                direction = "neutral"
            flows[etf] = {"volume_ratio_vs_20d": vol_ratio, "price_change_pct": price_chg, "direction": direction}
    except Exception as exc:
        return missing(NAME, "derived", f"Yahoo sector ETF gagal ditarik: {exc}", method_version=METHOD_VERSION)

    inflows = [k for k, v in flows.items() if v["direction"] == "inflow"]
    outflows = [k for k, v in flows.items() if v["direction"] == "outflow"]
    narrative = (
        f"Inflow terdeteksi di: {', '.join(inflows) if inflows else 'tidak ada'}. "
        f"Outflow di: {', '.join(outflows) if outflows else 'tidak ada'} "
        f"(volume >30% di atas rata-rata 20 hari + arah harga)."
    )

    return ComponentReading(
        name=NAME,
        value={"sectors": flows, "inflows": inflows, "outflows": outflows},
        status="ok",
        kind="derived",
        method_version=METHOD_VERSION,
        sources=[source("Yahoo Finance")],
        narrative=narrative,
        narrative_version="1.0.0",
    )
