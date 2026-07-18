"""02_LAYER1_SPECS/10_CURRENCY_DXY.md — kind=direct, komponen leaf."""
from __future__ import annotations

from ..contracts import ComponentReading
from ..sources import yahoo
from ._util import ev, missing, source, th

NAME = "currency_dxy"

# raw_score: dolar menguat = headwind buat emerging market, komoditas, dan
# growth stock (kanal likuiditas dolar) — jadi score turun saat DXY naik.
BANDS = [(2.0, 25.0), (0.0, 45.0), (-2.0, 60.0)]
LOWEST_SCORE = 80.0


def _score_for_change(chg_30d: float) -> float:
    for threshold, score in BANDS:
        if chg_30d > threshold:
            return score
    return LOWEST_SCORE


def compute() -> ComponentReading:
    try:
        df = yahoo.history("DX-Y.NYB", period="6mo")
        current = float(df["Close"].iloc[-1])
        as_of = df.index[-1].strftime("%Y-%m-%d")
        chg_30d = yahoo.pct_change("DX-Y.NYB", days=30, period="6mo")
    except Exception as exc:
        return missing(NAME, "direct", f"Yahoo DX-Y.NYB gagal ditarik: {exc}")

    direction = "menguat" if chg_30d > 0 else "melemah"
    # yahoo.pct_change(days=30) mundur 30 baris data harian (hari bursa), bukan
    # 30 hari kalender (~42 hari kalender karena weekend/libur) — narasi
    # sebelumnya bilang "30 hari" begitu saja, menyiratkan presisi kalender
    # yang sebenarnya tidak ada.
    narrative = f"DXY {current:.2f}, {direction} {abs(chg_30d):.1f}% dalam 30 hari bursa."
    rule = "score turun saat DXY menguat (headwind EM/komoditas/growth stock): >+2% 30h bursa → 25, 0..+2% → 45, -2%..0% → 60, <-2% → 80"

    return ComponentReading(
        name=NAME,
        value={"dxy": current, "change_30d_pct": chg_30d},
        status="ok",
        kind="direct",
        sources=[source("Yahoo Finance")],
        narrative=narrative,
        narrative_version="1.0.0",
        evidence=[
            ev("dxy", current, as_of, "Yahoo Finance DX-Y.NYB"),
            ev("change_30d_pct", chg_30d, as_of, "Yahoo Finance DX-Y.NYB (30 hari bursa)"),
        ],
        rule=rule,
        thresholds=[
            th("score=25 jika perubahan 30h bursa di atas ini", ">", 2.0),
            th("score=45 jika perubahan 30h bursa di atas ini", ">", 0.0),
            th("score=60 jika perubahan 30h bursa di atas ini", ">", -2.0),
        ],
        raw_score=_score_for_change(chg_30d),
    )
