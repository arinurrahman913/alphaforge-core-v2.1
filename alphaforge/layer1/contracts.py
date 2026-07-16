"""Bentuk paket Layer 1, mengunci 01_ARCHITECTURE/04_DATA_CONTRACTS.md §3."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Literal

Status = Literal["ok", "degraded", "missing"]
Kind = Literal["direct", "derived"]


@dataclass
class Source:
    provider: str
    fetched_at: str


@dataclass
class ComponentReading:
    name: str
    value: Any
    status: Status
    kind: Kind
    method_version: str | None = None
    inputs: list[str] = field(default_factory=list)
    sources: list[Source] = field(default_factory=list)
    note: str | None = None
    narrative: str | None = None
    narrative_version: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class Confidence:
    score: float
    band: Literal["low", "medium", "high"]
    limiters: list[str] = field(default_factory=list)


@dataclass
class ContextSummary:
    method_version: str
    narrative: str
    confidence: Confidence
    components_degraded: list[str]
    kind: Kind = "derived"

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "method_version": self.method_version,
            "narrative": self.narrative,
            "confidence": asdict(self.confidence),
            "components_degraded": self.components_degraded,
        }


@dataclass
class MarketContextPackage:
    session_id: str
    components: dict[str, ComponentReading]
    context_summary: ContextSummary
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "generated_at": self.generated_at,
            "components": {k: v.to_dict() for k, v in self.components.items()},
            "context_summary": self.context_summary.to_dict(),
        }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
