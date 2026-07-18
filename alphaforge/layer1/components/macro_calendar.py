"""02_LAYER1_SPECS/09_MACRO_CALENDAR.md — kind=direct, komponen leaf.

Pakai FRED release calendar (endpoint /fred/release/dates), bukan scraping
Investing.com/Forex Factory — lihat 04_DATA_SOURCES/01_PROVIDERS_OVERVIEW.md §2b.

Catatan jujur: FRED release-dates endpoint cuma kasih TANGGAL rilis, bukan
nilai previous/consensus/actual (itu butuh feed forecast berbayar seperti
Trading Economics). Field itu sengaja tidak ditampilkan seolah ada,
daripada diisi placeholder yang menyesatkan.
"""
from __future__ import annotations

from datetime import date, timedelta

import requests

from ..contracts import ComponentReading
from ._util import ev, missing, source, th
from ..sources.fred import api_key

NAME = "macro_calendar"

# release_id resmi FRED: 10 = Consumer Price Index, 50 = Employment Situation
# Keduanya market-moving releases paling diawasi, jadi severity="high" tetap
# (bukan dihitung, karena hanya 2 seri yang di-track — tidak ada seri
# severity rendah untuk dibandingkan).
RELEASES = {10: "CPI", 50: "Employment Situation"}
HORIZON_DAYS = 30
SEVERITY = "high"


def _upcoming_dates(release_id: int, label: str) -> list[dict]:
    today = date.today()
    resp = requests.get(
        "https://api.stlouisfed.org/fred/release/dates",
        params={
            "release_id": release_id,
            "api_key": api_key(),
            "file_type": "json",
            "realtime_start": today.isoformat(),
            "realtime_end": (today + timedelta(days=HORIZON_DAYS)).isoformat(),
            "include_release_dates_with_no_data": "true",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return [{"label": label, "date": d["date"], "severity": SEVERITY} for d in resp.json().get("release_dates", [])]


def compute() -> ComponentReading:
    try:
        events: list[dict] = []
        for rid, label in RELEASES.items():
            events.extend(_upcoming_dates(rid, label))
    except Exception as exc:
        return missing(NAME, "direct", f"FRED release calendar gagal ditarik: {exc}")

    events.sort(key=lambda e: e["date"])
    today = date.today()
    if events:
        days_to_next = (date.fromisoformat(events[0]["date"]) - today).days
        narrative = (
            f"{events[0]['label']} rilis {events[0]['date']} ({days_to_next} hari lagi). "
            f"{len(events)} peristiwa dalam {HORIZON_DAYS} hari."
        )
    else:
        days_to_next = None
        narrative = f"Tidak ada rilis CPI/Employment terjadwal dalam {HORIZON_DAYS} hari."

    rule = "risk window sempit menurunkan score: rilis high-severity ≤3 hari → 40, ≤7 hari → 65, selain itu → 85"
    if days_to_next is None:
        raw_score = 85.0
    elif days_to_next <= 3:
        raw_score = 40.0
    elif days_to_next <= 7:
        raw_score = 65.0
    else:
        raw_score = 85.0

    return ComponentReading(
        name=NAME,
        value={"events": events, "horizon_days": HORIZON_DAYS},
        status="ok",
        kind="direct",
        sources=[source("FRED release calendar")],
        narrative=narrative,
        narrative_version="1.0.0",
        evidence=[
            ev("next_event", events[0]["label"] if events else None, today.isoformat(), "FRED release calendar"),
            ev("days_to_next", days_to_next, today.isoformat(), "FRED release calendar"),
        ],
        rule=rule,
        thresholds=[
            th("risk window ketat jika hari-ke-rilis di bawah ini", "<=", 3),
            th("risk window sedang jika hari-ke-rilis di bawah ini", "<=", 7),
        ],
        raw_score=raw_score,
    )
