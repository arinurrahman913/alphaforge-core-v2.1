"""Historical tracking module — Layer 2 Fase B, stage 6: snapshot storage (v2.0).

12_HISTORICAL_TRACKING_JOURNAL.md: penyimpanan snapshot AggregatorOutput
sejak v2.0 (murah, mulai hari ini); EVALUASI terhadap outcome nyata sengaja
DITUNDA ke v2.1 karena bentuknya ("Return absolut? Relatif index? Horizon
berapa lama, beda per modul?") masih eksplisit "belum diputuskan" di spec
sendiri. Versi sebelumnya sempat implementasi evaluasi (record_outcome,
compare_recommendations, confidence_trend) lebih awal dari keputusan spec-nya
sendiri — dihapus di sini, bukan diadaptasi, karena field yang dipakainya
(recommendation/conviction tunggal) sudah tidak ada lagi (D-04), dan
menebak bentuk outcome sendiri akan mengulang kesalahan yang sama (membuat
keputusan produk yang seharusnya didiskusikan, bukan diasumsikan).

Entries disimpan sebagai dict polos setelah dibuat (bukan direkonstruksi balik
jadi dataclass bersarang saat load) — snapshot AggregatorOutput bersarang
dalam sampai ModuleOutput/Flag/dst, round-trip dataclass penuh tidak
diperlukan karena entry lama tidak pernah dimodifikasi, cuma ditambah &
dibaca ulang sebagai JSON.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from .historical_contracts import HistoricalTimeline
from ..json_safe import dumps_safe

if TYPE_CHECKING:
    from .aggregator_contracts import AggregatorOutput


def create_historical_entry(output: AggregatorOutput) -> dict:
    """Bungkus satu AggregatorOutput jadi HistoricalEntry dict siap simpan."""
    return {
        "entry_id": str(uuid.uuid4()),
        "analyzed_at": output.generated_at,
        "aggregator_output": asdict(output),
        "method_versions": dict(output.method_versions),
        "outcome": None,
    }


def _entry_date(entry: dict) -> str:
    return entry["analyzed_at"]


def load_historical_timeline(timeline_file: str) -> dict[str, HistoricalTimeline]:
    """Load historical timeline dari file. Entries dibiarkan sebagai dict
    (lihat docstring modul) — cuma total/first/last date yang dibaca ulang
    ke field dataclass HistoricalTimeline."""
    if not Path(timeline_file).exists():
        return {}

    with open(timeline_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    timelines = {}
    for ticker, timeline_dict in data.items():
        timeline = HistoricalTimeline(
            ticker=ticker,
            total_entries=timeline_dict.get("total_entries", 0),
            first_entry_date=timeline_dict.get("first_entry_date"),
            last_entry_date=timeline_dict.get("last_entry_date"),
            entries=list(timeline_dict.get("entries", [])),
        )
        timelines[ticker] = timeline

    return timelines


def update_timeline(
    timelines: dict[str, HistoricalTimeline],
    new_outputs: list[AggregatorOutput],
) -> dict[str, HistoricalTimeline]:
    """Update timelines dengan AggregatorOutput baru. Satu entry per HARI
    KALENDER (UTC) per ticker — re-run di hari yang sama menimpa entry hari
    itu, bukan menambah duplikat (lihat riwayat bug di commit 7caf44c)."""
    for output in new_outputs:
        if output.ticker not in timelines:
            timelines[output.ticker] = HistoricalTimeline(ticker=output.ticker)

        timeline = timelines[output.ticker]
        entry = create_historical_entry(output)

        same_day = (
            timeline.entries
            and datetime.fromisoformat(_entry_date(timeline.entries[-1])).date()
            == datetime.fromisoformat(_entry_date(entry)).date()
        )
        if same_day:
            timeline.entries[-1] = entry
        else:
            timeline.entries.append(entry)
            timeline.total_entries += 1

        timeline.last_entry_date = _entry_date(entry)
        if not timeline.first_entry_date:
            timeline.first_entry_date = _entry_date(entry)

    return timelines


def save_historical_timeline(timelines: dict[str, HistoricalTimeline], output_file: str) -> None:
    data = {ticker: timeline.to_dict() for ticker, timeline in timelines.items()}
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(dumps_safe(data, indent=2, ensure_ascii=False))


def get_entry_history(timeline: HistoricalTimeline, days_back: int | None = None) -> list[dict]:
    """Get entry history untuk satu ticker, urut kronologis."""
    entries = list(timeline.entries)
    if days_back:
        from datetime import timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
        entries = [e for e in entries if datetime.fromisoformat(_entry_date(e)) >= cutoff]
    return sorted(entries, key=_entry_date)
