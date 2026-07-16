from __future__ import annotations

from ..contracts import ComponentReading, Source, now_iso


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
