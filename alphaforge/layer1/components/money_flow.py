"""02_LAYER1_SPECS/03_MONEY_FLOW.md — kind=derived, komponen leaf.

Proksi: volume abnormal + arah harga di sector ETF (bukan data flow
institusional presisi seperti EPFR/Lipper, yang berbayar).
"""
from __future__ import annotations

from ..contracts import ComponentReading
from ..sources import yahoo
from ._util import ev, missing, source, th

NAME = "money_flow"
METHOD_VERSION = "1.0.0"

SECTOR_ETFS = ["XLK", "XLE", "XLF", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
VOL_RATIO_THRESHOLD = 1.3


def compute() -> ComponentReading:
    try:
        flows = {}
        as_of = None
        for etf in SECTOR_ETFS:
            df = yahoo.history(etf, period="2mo")
            as_of = df.index[-1].strftime("%Y-%m-%d")
            vol = df["Volume"]
            avg_vol_20d = float(vol.iloc[-21:-1].mean())
            last_vol = float(vol.iloc[-1])
            price_chg = (float(df["Close"].iloc[-1]) - float(df["Close"].iloc[-2])) / float(df["Close"].iloc[-2]) * 100.0
            vol_ratio = last_vol / avg_vol_20d if avg_vol_20d else 0.0
            if vol_ratio > VOL_RATIO_THRESHOLD and price_chg > 0:
                direction = "inflow"
            elif vol_ratio > VOL_RATIO_THRESHOLD and price_chg < 0:
                direction = "outflow"
            else:
                direction = "neutral"
            flows[etf] = {"volume_ratio_vs_20d": vol_ratio, "price_change_pct": price_chg, "direction": direction}
    except Exception as exc:
        return missing(NAME, "derived", f"Yahoo sector ETF gagal ditarik: {exc}", method_version=METHOD_VERSION)

    inflows = [k for k, v in flows.items() if v["direction"] == "inflow"]
    outflows = [k for k, v in flows.items() if v["direction"] == "outflow"]
    narrative = (
        f"Proksi volume+harga (bukan data flow institusional). Inflow terdeteksi di: "
        f"{', '.join(inflows) if inflows else 'tidak ada'}. "
        f"Outflow di: {', '.join(outflows) if outflows else 'tidak ada'} "
        f"(volume >30% di atas rata-rata 20 hari + arah harga, universe {len(SECTOR_ETFS)} sector ETF)."
    )
    rule = f"volume_ratio > {VOL_RATIO_THRESHOLD} & price naik → inflow; volume_ratio > {VOL_RATIO_THRESHOLD} & price turun → outflow; selain itu → neutral"
    raw_score = max(0.0, min(100.0, 50.0 + (len(inflows) - len(outflows)) / len(SECTOR_ETFS) * 50.0))

    return ComponentReading(
        name=NAME,
        value={"sectors": flows, "inflows": inflows, "outflows": outflows},
        status="ok",
        kind="derived",
        method_version=METHOD_VERSION,
        sources=[source("Yahoo Finance")],
        narrative=narrative,
        narrative_version="1.0.0",
        evidence=[
            ev("universe_size", len(SECTOR_ETFS), as_of, "Yahoo Finance sector ETF"),
            ev("inflows", inflows, as_of, "Yahoo Finance sector ETF volume+price"),
            ev("outflows", outflows, as_of, "Yahoo Finance sector ETF volume+price"),
        ],
        rule=rule,
        thresholds=[th("volume ratio vs rata-rata 20d di atas ini dianggap abnormal", ">", VOL_RATIO_THRESHOLD)],
        raw_score=raw_score,
    )
