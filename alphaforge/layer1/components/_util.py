from __future__ import annotations

from typing import Any

from ..contracts import ComponentReading, Evidence, Source, Threshold, now_iso


def missing(name: str, kind, note: str, method_version: str | None = None, inputs=None) -> ComponentReading:
    return ComponentReading(
        name=name,
        value=None,
        status="missing",
        kind=kind,
        method_version=method_version,
        inputs=inputs or [],
        sources=[],
        note=note,
    )


def source(provider: str) -> Source:
    return Source(provider=provider, fetched_at=now_iso())


def ev(field: str, value: Any, as_of: str, source_label: str) -> Evidence:
    """Shorthand buat satu titik Evidence — dipakai berkali-kali per komponen."""
    return Evidence(field=field, value=value, as_of=as_of, source=source_label)


def th(label: str, operator: str, value: float) -> Threshold:
    """Shorthand buat satu Threshold."""
    return Threshold(label=label, operator=operator, value=value)
