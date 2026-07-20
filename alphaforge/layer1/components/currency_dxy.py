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
        # 21 hari bursa ≈ 30 hari kalender (~1 bulan) — dulu days=30 (30 hari
        # bursa = ~42 hari kalender) padahal field-nya dinamai "30d", jadi
        # menyesatkan. 21 menyelaraskan field dengan makna ~1 bulan (sama
        # dengan konvensi sector_rotation).
        chg_30d = yahoo.pct_change("DX-Y.NYB", days=21, period="6mo")
    except Exception as exc:
        return missing(NAME, "direct", f"Yahoo DX-Y.NYB gagal ditarik: {exc}")

    direction = "menguat" if chg_30d > 0 else "melemah"
    narrative = f"DXY {current:.2f}, {direction} {abs(chg_30d):.1f}% dalam ~1 bulan (21 hari bursa)."
    rule = "score turun saat DXY menguat (headwind EM/komoditas/growth stock): >+2% ~1bln → 25, 0..+2% → 45, -2%..0% → 60, <-2% → 80"

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
            ev("change_30d_pct", chg_30d, as_of, "Yahoo Finance DX-Y.NYB (~1 bulan, 21 hari bursa)"),
        ],
        rule=rule,
        thresholds=[
            th("score=25 jika perubahan ~1bln di atas ini", ">", 2.0),
            th("score=45 jika perubahan ~1bln di atas ini", ">", 0.0),
            th("score=60 jika perubahan ~1bln di atas ini", ">", -2.0),
        ],
        raw_score=_score_for_change(chg_30d),
    )
