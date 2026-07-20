"""02_LAYER1_SPECS/11_COMMODITY_SIGNALS.md — kind=direct, komponen leaf."""
from __future__ import annotations

from ..contracts import ComponentReading
from ..sources import yahoo
from ._util import ev, missing, percentile_rank, source, th

NAME = "commodity_signals"
METHOD_VERSION = "2.0.0"
CHANGE_WINDOW_DAYS = 21  # ~1 bulan kalender (hari bursa)
LOOKBACK_PERIOD = "3y"

# raw_score: sinyal paling lemah/ambigu di antara 12 komponen (naik bisa
# berarti inflasi/late-cycle yang bearish buat saham, atau reflation yang
# bullish — spec sendiri memposisikan ini sebagai konteks sektor, bukan
# sinyal arah yang kuat), jadi score cuma bergerak tipis di sekitar netral
# 55, tidak pernah lebih ekstrem dari ±10 poin.
#
# Pasca-audit (2026-07): swing tetap dibatasi ±10 (desain sengaja, lihat
# catatan di atas) TAPI sekarang diskalakan dari PERCENTILE gabungan emas+WTI
# terhadap distribusi perubahan ~1 bulan 3 tahun terakhir — bukan dari %
# perubahan mentah yang clamp-nya berarti beda antar rezim volatilitas
# komoditas (mis. ±10% wajar di era volatile, ekstrem di era tenang).
BASELINE = 55.0
MAX_SWING = 10.0


def compute() -> ComponentReading:
    try:
        gold_df = yahoo.history("GC=F", period=LOOKBACK_PERIOD)
        gold_close = gold_df["Close"]
        gold = float(gold_close.iloc[-1])
        gold_as_of = gold_df.index[-1].strftime("%Y-%m-%d")
        gold_chg_series = gold_close.pct_change(CHANGE_WINDOW_DAYS) * 100.0
        gold_chg = float(gold_chg_series.iloc[-1])
        gold_history = gold_chg_series.dropna().tolist()

        wti_df = yahoo.history("CL=F", period=LOOKBACK_PERIOD)
        wti_close = wti_df["Close"]
        wti = float(wti_close.iloc[-1])
        wti_as_of = wti_df.index[-1].strftime("%Y-%m-%d")
        wti_chg_series = wti_close.pct_change(CHANGE_WINDOW_DAYS) * 100.0
        wti_chg = float(wti_chg_series.iloc[-1])
        wti_history = wti_chg_series.dropna().tolist()
    except Exception as exc:
        return missing(NAME, "direct", f"Yahoo futures gagal ditarik: {exc}", method_version=METHOD_VERSION)

    if not gold_history or not wti_history:
        return missing(NAME, "direct", "Histori GC=F/CL=F tidak cukup untuk hitung percentile.", method_version=METHOD_VERSION)

    gold_pct = percentile_rank(gold_history, gold_chg)
    wti_pct = percentile_rank(wti_history, wti_chg)
    avg_percentile = (gold_pct + wti_pct) / 2.0  # 0=paling lemah historis, 1=paling kuat

    narrative = (
        f"Emas {gold:,.0f} ({gold_chg:+.1f}% ~1bln, persentil-{round(gold_pct * 100)}), "
        f"WTI {wti:,.2f} ({wti_chg:+.1f}% ~1bln, persentil-{round(wti_pct * 100)})."
    )
    rule = (
        f"score = {BASELINE:.0f} - (percentile_gabungan-0.5)×2×{MAX_SWING:.0f} — percentile dari ranking "
        f"perubahan ~1bln emas & WTI vs distribusi {LOOKBACK_PERIOD} masing-masing, dirata-rata. "
        f"Swing dibatasi ±{MAX_SWING:.0f} poin (sengaja sempit — sinyal ambigu: naik bisa inflasi/late-cycle "
        f"bearish ATAU reflation bullish)."
    )

    swing = (avg_percentile - 0.5) * 2.0 * MAX_SWING
    raw_score = BASELINE - swing

    return ComponentReading(
        name=NAME,
        value={
            "gold": gold,
            "gold_change_30d_pct": gold_chg,
            "wti": wti,
            "wti_change_30d_pct": wti_chg,
            "percentile_3y": avg_percentile,
        },
        status="ok",
        kind="direct",
        method_version=METHOD_VERSION,
        sources=[source("Yahoo Finance")],
        narrative=narrative,
        narrative_version="2.0.0",
        evidence=[
            ev("gold", gold, gold_as_of, "Yahoo Finance GC=F"),
            ev("gold_change_30d_pct", gold_chg, gold_as_of, "Yahoo Finance GC=F (~1 bulan, 21 hari bursa)"),
            ev("wti", wti, wti_as_of, "Yahoo Finance CL=F"),
            ev("wti_change_30d_pct", wti_chg, wti_as_of, "Yahoo Finance CL=F (~1 bulan, 21 hari bursa)"),
            ev("percentile_3y", round(avg_percentile, 3), gold_as_of, f"Yahoo Finance GC=F+CL=F (persentil vs {LOOKBACK_PERIOD})"),
        ],
        rule=rule,
        thresholds=[th("swing dibatasi ± poin dari baseline 55", "clamp", MAX_SWING)],
        raw_score=raw_score,
    )
