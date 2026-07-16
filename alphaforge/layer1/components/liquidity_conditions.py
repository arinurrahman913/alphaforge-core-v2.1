"""02_LAYER1_SPECS/04_LIQUIDITY_CONDITIONS.md — kind=direct (dua seri resmi
dibaca apa adanya, bukan digabung jadi indeks baru), komponen leaf."""
from __future__ import annotations

from ..contracts import ComponentReading
from ..sources import fred
from ._util import missing, source

NAME = "liquidity_conditions"


def compute() -> ComponentReading:
    try:
        walcl_obs = fred.series_observations("WALCL", limit=12)
        m2_obs = fred.series_observations("M2SL", limit=12)
    except Exception as exc:
        return missing(NAME, "direct", f"FRED WALCL/M2SL gagal ditarik: {exc}")

    walcl_date, walcl_now = walcl_obs[0]
    walcl_prior = walcl_obs[-1][1]
    walcl_chg = walcl_now - walcl_prior

    m2_date, m2_now = m2_obs[0]
    m2_prior_year = m2_obs[-1][1]
    m2_yoy = (m2_now - m2_prior_year) / m2_prior_year * 100.0

    tightening = walcl_chg < 0
    narrative = (
        f"Neraca Fed (WALCL) {'turun' if tightening else 'naik'} {abs(walcl_chg):,.0f} juta USD "
        f"dari {len(walcl_obs)} rilis lalu. M2 {m2_yoy:+.1f}% YoY per {m2_date}."
    )

    return ComponentReading(
        name=NAME,
        value={
            "fed_balance_sheet": walcl_now,
            "fed_balance_sheet_change": walcl_chg,
            "fed_balance_sheet_as_of": walcl_date,
            "m2_yoy_pct": m2_yoy,
            "m2_as_of": m2_date,
            "tightening": tightening,
        },
        status="ok",
        kind="direct",
        sources=[source("FRED")],
        narrative=narrative,
        narrative_version="1.0.0",
    )
