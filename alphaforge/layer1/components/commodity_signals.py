"""02_LAYER1_SPECS/11_COMMODITY_SIGNALS.md — kind=direct, komponen leaf."""
from __future__ import annotations

from ..contracts import ComponentReading
from ..sources import yahoo
from ._util import ev, missing, source, th

NAME = "commodity_signals"

# raw_score: sinyal paling lemah/ambigu di antara 12 komponen (naik bisa
# berarti inflasi/late-cycle yang bearish buat saham, atau reflation yang
# bullish — spec sendiri memposisikan ini sebagai konteks sektor, bukan
# sinyal arah yang kuat), jadi score cuma bergerak tipis di sekitar netral
# 55, tidak pernah lebih ekstrem dari ±10 poin.
BASELINE = 55.0
MAX_SWING = 10.0


def compute() -> ComponentReading:
    try:
        gold_df = yahoo.history("GC=F", period="6mo")
        gold = float(gold_df["Close"].iloc[-1])
        gold_as_of = gold_df.index[-1].strftime("%Y-%m-%d")
        gold_chg = yahoo.pct_change("GC=F", days=21, period="6mo")

        wti_df = yahoo.history("CL=F", period="6mo")
        wti = float(wti_df["Close"].iloc[-1])
        wti_as_of = wti_df.index[-1].strftime("%Y-%m-%d")
        wti_chg = yahoo.pct_change("CL=F", days=21, period="6mo")
    except Exception as exc:
        return missing(NAME, "direct", f"Yahoo futures gagal ditarik: {exc}")

    # 21 hari bursa ≈ 30 hari kalender (~1 bulan) — selaras field "30d" &
    # currency_dxy (dulu days=30 = ~42 hari kalender, menyesatkan).
    narrative = (
        f"Emas {gold:,.0f} ({gold_chg:+.1f}% ~1bln), WTI {wti:,.2f} ({wti_chg:+.1f}% ~1bln)."
    )
    rule = (
        "score = 55 dikurangi rata-rata perubahan emas+WTI ~1 bulan (21 hari bursa) "
        "(dibatasi ±10 poin) — komoditas naik dibaca sedikit bearish (risiko inflasi/late-cycle)"
    )

    avg_chg = (gold_chg + wti_chg) / 2
    swing = max(-MAX_SWING, min(MAX_SWING, avg_chg))
    raw_score = BASELINE - swing

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
        evidence=[
            ev("gold", gold, gold_as_of, "Yahoo Finance GC=F"),
            ev("gold_change_30d_pct", gold_chg, gold_as_of, "Yahoo Finance GC=F (~1 bulan, 21 hari bursa)"),
            ev("wti", wti, wti_as_of, "Yahoo Finance CL=F"),
            ev("wti_change_30d_pct", wti_chg, wti_as_of, "Yahoo Finance CL=F (~1 bulan, 21 hari bursa)"),
        ],
        rule=rule,
        thresholds=[th("swing dibatasi ± poin dari baseline 55", "clamp", MAX_SWING)],
        raw_score=raw_score,
    )
