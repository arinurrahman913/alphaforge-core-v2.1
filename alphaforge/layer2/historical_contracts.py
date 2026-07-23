"""Historical tracking contracts — Layer 2 Fase B, stage 6 (post-pipeline)
12_HISTORICAL_TRACKING_JOURNAL.md + Data Contracts §8.

Penyimpanan (v2.0) dan evaluasi (v2.1) sengaja dipisah — cuma evaluasinya
yang boleh menyusul, bukan penyimpanannya (Prinsip #6). HistoricalEntry
menyimpan SNAPSHOT UTUH AggregatorOutput, bukan ringkasan — meringkas hari
ini mengandaikan kita sudah tahu apa yang penting untuk dievaluasi nanti,
padahal itu justru yang belum diketahui.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HistoricalEntry:
    """Satu snapshot AggregatorOutput di waktu tertentu — Data Contracts §8."""
    entry_id: str
    analyzed_at: str  # ISO datetime
    aggregator_output: object  # AggregatorOutput (snapshot utuh)
    method_versions: dict[str, str]  # disalin ke level entri, bukan cuma di dalam snapshot
    outcome: dict | None = None  # sengaja None di v2.0 — bentuknya belum diputuskan (v2.1, lihat spec)

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)


@dataclass
class HistoricalTimeline:
    """Timeline entries untuk satu ticker."""
    ticker: str
    total_entries: int = 0
    first_entry_date: str | None = None
    last_entry_date: str | None = None
    entries: list[HistoricalEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)
