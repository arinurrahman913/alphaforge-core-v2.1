"""02_LAYER1_SPECS/01_BUSINESS_CYCLE_STAGE.md — kind=derived, komponen leaf.

Catatan jujur soal sumber: spec menyebut PMI sebagai salah satu indikator,
tapi ISM Manufacturing PMI tidak tersedia gratis di FRED (berlisensi, seri
lama `NAPM` sudah ditarik). Sebagai gantinya dipakai Industrial Production
YoY (`INDPRO`) sebagai proksi arah aktivitas manufaktur — didokumentasikan
di sini, bukan disamarkan seolah PMI resmi.
"""
from __future__ import annotations

from ..contracts import ComponentReading
from ..sources import fred
from ._util import missing, source

NAME = "business_cycle_stage"
METHOD_VERSION = "1.0.0"


def compute() -> ComponentReading:
    try:
        gdp_date, gdp_qoq = fred.latest_observation("A191RL1Q225SBEA")  # real GDP QoQ SAAR %
        unrate_obs = fred.series_observations("UNRATE", limit=7)
        indpro_obs = fred.series_observations("INDPRO", limit=13)
    except Exception as exc:
        return missing(NAME, "derived", f"FRED gagal ditarik: {exc}", method_version=METHOD_VERSION)

    unrate_date, unrate_now = unrate_obs[0]
    unrate_6mo_ago = unrate_obs[-1][1]
    unrate_rising = unrate_now > unrate_6mo_ago + 0.2

    indpro_date, indpro_now = indpro_obs[0]
    indpro_yoy = (indpro_now - indpro_obs[-1][1]) / indpro_obs[-1][1] * 100.0

    expansive = indpro_yoy > 0
    if gdp_qoq < 0 and unrate_rising:
        stage = "recession"
    elif gdp_qoq > 2.5 and expansive and not unrate_rising:
        stage = "early-cycle"
    elif not expansive and unrate_rising:
        stage = "late-cycle"
    else:
        stage = "mid-cycle"

    narrative = (
        f"GDP QoQ {gdp_qoq:+.1f}% ({gdp_date}), Industrial Production {indpro_yoy:+.1f}% YoY "
        f"(proksi PMI, {indpro_date}), pengangguran {unrate_now:.1f}% "
        f"({'naik' if unrate_rising else 'stabil/turun'} vs 6 bulan lalu) → {stage}."
    )

    return ComponentReading(
        name=NAME,
        value={
            "stage": stage,
            "gdp_qoq_pct": gdp_qoq,
            "indpro_yoy_pct": indpro_yoy,
            "unemployment_rate": unrate_now,
            "unemployment_rising": unrate_rising,
        },
        status="ok",
        kind="derived",
        method_version=METHOD_VERSION,
        sources=[source("FRED")],
        note="PMI diganti Industrial Production YoY (INDPRO) — ISM PMI tidak gratis di FRED.",
        narrative=narrative,
        narrative_version="1.0.0",
    )
