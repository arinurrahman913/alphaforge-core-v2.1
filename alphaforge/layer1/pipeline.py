"""Orkestrasi Layer 1 — DAG di 01_ARCHITECTURE/02_LAYER1_MARKET_CONTEXT.md §5:
11 komponen leaf paralel, lalu market_sentiment (satu-satunya composite)."""
from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor

from .components import (
    business_cycle_stage,
    commodity_signals,
    currency_dxy,
    liquidity_conditions,
    macro_calendar,
    market_breadth,
    market_regime,
    money_flow,
    sector_rotation,
    volatility_index,
    yield_curve,
)
from .components import market_sentiment as market_sentiment_mod
from .contracts import Confidence, ContextSummary, MarketContextPackage, now_iso

LEAF_COMPONENTS = {
    "business_cycle_stage": business_cycle_stage.compute,
    "sector_rotation": sector_rotation.compute,
    "money_flow": money_flow.compute,
    "liquidity_conditions": liquidity_conditions.compute,
    "yield_curve": yield_curve.compute,
    "market_regime": market_regime.compute,
    "macro_calendar": macro_calendar.compute,
    "currency_dxy": currency_dxy.compute,
    "commodity_signals": commodity_signals.compute,
    "volatility_index": volatility_index.compute,
    "market_breadth": market_breadth.compute,
}

CONTEXT_SUMMARY_METHOD_VERSION = "1.0.0"


def _build_context_summary(components: dict) -> ContextSummary:
    degraded = [name for name, r in components.items() if r.status in ("degraded", "missing")]
    n_ok = len(components) - len(degraded)

    parts = []
    yc = components["yield_curve"]
    if yc.status == "ok":
        parts.append(f"yield curve {yc.value['shape']}")
    bcs = components["business_cycle_stage"]
    if bcs.status == "ok":
        parts.append(f"siklus {bcs.value['stage']}")
    regime = components["market_regime"]
    if regime.status == "ok":
        parts.append(f"regime {regime.value['regime']}")
    sentiment = components["market_sentiment"]
    if sentiment.status in ("ok", "degraded") and sentiment.value:
        parts.append(f"sentimen {sentiment.value['label']}")

    narrative = (", ".join(parts).capitalize() + ".") if parts else "Konteks tidak bisa disusun — mayoritas komponen kosong."
    if degraded:
        narrative += f" {len(degraded)} dari {len(components)} komponen degraded/missing: {', '.join(degraded)}."

    if n_ok == len(components):
        band = "high"
    elif n_ok >= len(components) * 0.75:
        band = "medium"
    else:
        band = "low"

    return ContextSummary(
        method_version=CONTEXT_SUMMARY_METHOD_VERSION,
        narrative=narrative,
        confidence=Confidence(score=n_ok / len(components) * 100.0, band=band, limiters=degraded),
        components_degraded=degraded,
    )


def build_market_context_package(price_cache: dict | None = None, session_id: str | None = None) -> MarketContextPackage:
    session_id = session_id or f"session-{uuid.uuid4().hex[:12]}"

    components: dict = {}
    with ThreadPoolExecutor(max_workers=len(LEAF_COMPONENTS)) as pool:
        futures = {
            name: pool.submit(fn, price_cache) if name == "market_breadth" else pool.submit(fn)
            for name, fn in LEAF_COMPONENTS.items()
        }
        for name, fut in futures.items():
            components[name] = fut.result()

    components["market_sentiment"] = market_sentiment_mod.compute(
        vix_reading=components["volatility_index"],
        breadth_reading=components["market_breadth"],
    )

    context_summary = _build_context_summary(components)

    return MarketContextPackage(
        session_id=session_id,
        components=components,
        context_summary=context_summary,
        generated_at=now_iso(),
    )
