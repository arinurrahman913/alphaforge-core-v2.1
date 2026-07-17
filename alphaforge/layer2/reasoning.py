"""Reasoning modules — Layer 2 Fase B, stage 4

3 independent reasoning lens dengan field access control.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from .reasoning_contracts import AggregatedReasoning, ReasoningOutput

if TYPE_CHECKING:
    from .confidence_contracts import ConfidenceScore
    from .knowledge_contracts import KnowledgeProfile
    from .risk_contracts import RiskAssessment


def run_quality_lens(
    profile: KnowledgeProfile,
    confidence: ConfidenceScore | None = None,
    risk: RiskAssessment | None = None,
) -> ReasoningOutput:
    """Quality Lens: Fundamental analysis.

    Access: sections 1,2,3a,4,6,7 (Identity, Financial Health, Competitive Structure, Historical, Valuation, Governance)
    Focus: margin trends, balance sheet health, valuation vs peers, governance quality
    """
    score = 0.0
    positive = []
    negative = []
    metrics = {}

    # Section 2: Financial Health
    fh = profile.financial_health
    if fh.net_margin_trend.q4 is not None and fh.net_margin_trend.q4 > 0.05:
        score += 15
        positive.append("Strong net margins (>5%)")
        metrics["net_margin_q4"] = fh.net_margin_trend.q4
    elif fh.net_margin_trend.q4 is not None and fh.net_margin_trend.q4 < 0:
        score -= 15
        negative.append("Negative net margin")
        metrics["net_margin_q4"] = fh.net_margin_trend.q4

    if fh.balance_sheet.current_ratio is not None and fh.balance_sheet.current_ratio > 1.5:
        score += 10
        positive.append("Strong current ratio (>1.5)")
        metrics["current_ratio"] = fh.balance_sheet.current_ratio
    elif fh.balance_sheet.current_ratio is not None and fh.balance_sheet.current_ratio < 1.0:
        score -= 10
        negative.append("Weak liquidity (current ratio <1)")
        metrics["current_ratio"] = fh.balance_sheet.current_ratio

    if fh.balance_sheet.debt_to_equity is not None and fh.balance_sheet.debt_to_equity < 1.0:
        score += 10
        positive.append("Conservative leverage (D/E <1)")
        metrics["debt_to_equity"] = fh.balance_sheet.debt_to_equity
    elif fh.balance_sheet.debt_to_equity is not None and fh.balance_sheet.debt_to_equity > 2.0:
        score -= 12
        negative.append("High leverage (D/E >2)")
        metrics["debt_to_equity"] = fh.balance_sheet.debt_to_equity

    # Section 4: Historical Trend
    ht = profile.historical_trend
    if ht.return_1y is not None and ht.return_1y > 10:
        score += 8
        positive.append("Positive 1Y return")
        metrics["return_1y"] = ht.return_1y
    elif ht.return_1y is not None and ht.return_1y < -20:
        score -= 8
        negative.append("Severe drawdown")
        metrics["return_1y"] = ht.return_1y

    # Section 6: Valuation
    val = profile.valuation
    if val.pe_ratio_trailing is not None:
        if val.pe_ratio_trailing < 20:
            score += 12
            positive.append("Attractive P/E (<20x)")
            metrics["pe_ratio"] = val.pe_ratio_trailing
        elif val.pe_ratio_trailing > 50:
            score -= 8
            negative.append("Expensive valuation (P/E >50x)")
            metrics["pe_ratio"] = val.pe_ratio_trailing

    if val.pb_ratio is not None and val.pb_ratio < 2.0:
        score += 8
        positive.append("Fair P/B ratio (<2x)")
        metrics["pb_ratio"] = val.pb_ratio

    # Section 7: Governance
    gov = profile.governance
    if len(gov.restatements or []) > 0:
        score -= 15
        negative.append(f"Financial restatements ({len(gov.restatements)})")
    elif len(gov.auditor_changes or []) > 0:
        score -= 8
        negative.append(f"Auditor changes ({len(gov.auditor_changes)})")

    # Confidence adjustment
    if confidence and confidence.overall_confidence < 40:
        score -= 10
        negative.append("Low data confidence")

    # Risk adjustment
    if risk and risk.high_severity_count > 0:
        score -= 15
        negative.append(f"High-risk flags ({risk.high_severity_count})")

    score = max(-50, min(100, score + 50))  # Normalize to 0-100

    stance = _score_to_stance(score)

    return ReasoningOutput(
        lens_name="quality",
        ticker=profile.ticker,
        exchange=profile.exchange,
        conviction_score=round(score, 1),
        stance=stance,
        score_breakdown={"fundamentals": (score - 50) / 50},
        positive_factors=positive,
        negative_factors=negative,
        key_metrics=metrics,
        reasoning_notes=f"Quality score {score:.0f}: " + (positive[0] if positive else "Mixed signals"),
        assessed_at=datetime.now(timezone.utc).isoformat(),
        fields_accessed=["identity", "financial_health", "competitive_structure", "historical_trend", "valuation", "governance"],
    )


def run_speculative_lens(
    profile: KnowledgeProfile,
    confidence: ConfidenceScore | None = None,
) -> ReasoningOutput:
    """Speculative Lens: Technical + sentiment.

    Access: sections 1,3a,4-volatility,5 (Identity, Competitive Structure, Volatility, Ownership)
    Focus: price momentum, volatility, insider activity, sentiment shifts
    """
    score = 0.0
    positive = []
    negative = []
    metrics = {}

    # Section 4: Volatility & momentum
    ht = profile.historical_trend
    if ht.volatility_daily is not None:
        if ht.volatility_daily > 4.0:
            score += 10
            positive.append("High volatility - trading opportunity")
            metrics["volatility_daily"] = ht.volatility_daily
        elif ht.volatility_daily < 1.0:
            score -= 5
            negative.append("Low volatility - boring")
            metrics["volatility_daily"] = ht.volatility_daily

    if ht.return_1y is not None and ht.return_1y > 30:
        score += 15
        positive.append("Strong momentum (>30% 1Y)")
        metrics["return_1y"] = ht.return_1y
    elif ht.return_1y is not None and ht.return_1y < -30:
        score -= 10
        negative.append("Negative momentum")
        metrics["return_1y"] = ht.return_1y

    # Section 5: Ownership - insider activity
    own = profile.ownership
    if own.institutional_pct is not None and own.institutional_pct > 0.70:
        score += 8
        positive.append("High institutional ownership")
        metrics["institutional_pct"] = own.institutional_pct
    elif own.institutional_pct is not None and own.institutional_pct < 0.10:
        score -= 5
        negative.append("Low institutional ownership")
        metrics["institutional_pct"] = own.institutional_pct

    if len(own.insider_transactions or []) > 0:
        score += 10
        positive.append("Recent insider activity")
        metrics["insider_transactions"] = len(own.insider_transactions)

    # Confidence adjustment
    if confidence and confidence.price_data_confidence < 40:
        score -= 15
        negative.append("Insufficient price data for technical analysis")

    score = max(-50, min(100, score + 50))  # Normalize to 0-100

    stance = _score_to_stance(score)

    return ReasoningOutput(
        lens_name="speculative",
        ticker=profile.ticker,
        exchange=profile.exchange,
        conviction_score=round(score, 1),
        stance=stance,
        score_breakdown={"momentum": (score - 50) / 50},
        positive_factors=positive,
        negative_factors=negative,
        key_metrics=metrics,
        reasoning_notes=f"Speculative score {score:.0f}: " + (positive[0] if positive else "Neutral momentum"),
        assessed_at=datetime.now(timezone.utc).isoformat(),
        fields_accessed=["identity", "competitive_structure", "historical_trend", "ownership"],
    )


def run_multibagger_lens(
    profile: KnowledgeProfile,
    confidence: ConfidenceScore | None = None,
) -> ReasoningOutput:
    """Multibagger Lens: Growth + momentum.

    Access: sections 1,3a,3b,4,6 (Identity, Competitive Structure, Momentum, Historical, Valuation)
    Focus: revenue growth, segment acceleration, TAM, high-growth characteristics
    """
    score = 0.0
    positive = []
    negative = []
    metrics = {}

    # Section 3a: Competitive Structure
    cs = profile.competitive_structure
    if cs.total_revenue_ttm is not None and cs.total_revenue_ttm > 100e6:
        if cs.tam_estimate and "large" in str(cs.tam_estimate).lower():
            score += 12
            positive.append("Large TAM - multibagger potential")
            metrics["tam_estimate"] = cs.tam_estimate

    # Section 3b: Momentum
    cm = profile.competitive_momentum
    if cm.segment_growth and "high" in str(cm.segment_growth).lower():
        score += 15
        positive.append("High segment growth")
        metrics["segment_growth"] = cm.segment_growth
    elif cm.acceleration_signal and "positive" in str(cm.acceleration_signal).lower():
        score += 10
        positive.append("Positive acceleration signal")
        metrics["acceleration_signal"] = cm.acceleration_signal

    # Section 4: Historical returns
    ht = profile.historical_trend
    if ht.return_1y is not None and ht.return_1y > 50:
        score += 12
        positive.append("Explosive 1Y return (>50%)")
        metrics["return_1y"] = ht.return_1y
    elif ht.return_1y is not None and ht.return_1y > 20:
        score += 8
        positive.append("Strong 1Y return (>20%)")
        metrics["return_1y"] = ht.return_1y

    # Section 6: Valuation - growth justification
    val = profile.valuation
    if val.pe_ratio_trailing is not None:
        if val.pe_ratio_trailing > 50 and ht.return_1y and ht.return_1y > 30:
            score += 8
            positive.append("High growth justifies premium valuation")
            metrics["pe_ratio"] = val.pe_ratio_trailing
        elif val.pe_ratio_trailing > 100:
            score -= 10
            negative.append("Extreme valuation - limited upside")
            metrics["pe_ratio"] = val.pe_ratio_trailing

    # Confidence adjustment
    if confidence and confidence.overall_confidence < 40:
        score -= 12
        negative.append("Insufficient data for growth thesis")

    score = max(-50, min(100, score + 50))  # Normalize to 0-100

    stance = _score_to_stance(score)

    return ReasoningOutput(
        lens_name="multibagger",
        ticker=profile.ticker,
        exchange=profile.exchange,
        conviction_score=round(score, 1),
        stance=stance,
        score_breakdown={"growth": (score - 50) / 50},
        positive_factors=positive,
        negative_factors=negative,
        key_metrics=metrics,
        reasoning_notes=f"Multibagger score {score:.0f}: " + (positive[0] if positive else "Modest growth profile"),
        assessed_at=datetime.now(timezone.utc).isoformat(),
        fields_accessed=["identity", "competitive_structure", "competitive_momentum", "historical_trend", "valuation"],
    )


def aggregate_reasoning(
    quality: ReasoningOutput,
    speculative: ReasoningOutput,
    multibagger: ReasoningOutput,
    risk_adjustment: float = 0.0,
) -> AggregatedReasoning:
    """Aggregate 3 lens menjadi final recommendation.

    Args:
        quality: Quality lens output
        speculative: Speculative lens output
        multibagger: Multibagger lens output
        risk_adjustment: Confidence adjustment dari risk module

    Returns:
        AggregatedReasoning dengan final stance
    """
    # Weighted average of 3 lens
    final_score = (
        quality.conviction_score * 0.40 +
        speculative.conviction_score * 0.30 +
        multibagger.conviction_score * 0.30
    )

    # Risk adjustment
    final_score = max(0, min(100, final_score + (risk_adjustment * 50)))

    # Map to stance
    final_stance = _score_to_stance(final_score)

    # Check lens agreement
    stances = [quality.stance, speculative.stance, multibagger.stance]
    agreement = sum(1 for s in stances if s == final_stance) / 3 * 100

    # Divergence level
    if agreement >= 80:
        divergence = "low"
    elif agreement >= 50:
        divergence = "medium"
    else:
        divergence = "high"

    # Build recommendation string
    reason_parts = []
    if quality.stance in ["strong_buy", "buy"]:
        reason_parts.append("Quality bullish")
    elif quality.stance in ["strong_sell", "sell"]:
        reason_parts.append("Quality bearish")

    if multibagger.stance in ["strong_buy", "buy"]:
        reason_parts.append("Multibagger growth")
    elif multibagger.stance in ["strong_sell", "sell"]:
        reason_parts.append("Multibagger caution")

    recommendation = f"{final_stance.replace('_', ' ').title()} ({'+ ' + ', '.join(reason_parts) if reason_parts else 'Mixed signals'})"

    return AggregatedReasoning(
        ticker=quality.ticker,
        exchange=quality.exchange,
        quality_output=quality,
        speculative_output=speculative,
        multibagger_output=multibagger,
        final_score=round(final_score, 1),
        final_stance=final_stance,
        lens_agreement=round(agreement, 0),
        divergence_level=divergence,
        recommendation=recommendation,
        risk_adjusted_score=round(final_score, 1),
        aggregated_at=datetime.now(timezone.utc).isoformat(),
    )


def _score_to_stance(score: float) -> str:
    """Convert numeric score to stance."""
    if score >= 75:
        return "strong_buy"
    elif score >= 60:
        return "buy"
    elif score >= 40:
        return "hold"
    elif score >= 25:
        return "sell"
    else:
        return "strong_sell"


def run_reasoning_pipeline(
    profile: KnowledgeProfile,
    confidence: ConfidenceScore | None = None,
    risk: RiskAssessment | None = None,
) -> AggregatedReasoning:
    """Run all 3 reasoning lenses dan aggregate hasil.

    Args:
        profile: KnowledgeProfile
        confidence: ConfidenceScore (optional)
        risk: RiskAssessment (optional)

    Returns:
        AggregatedReasoning dengan 3 lens outputs + final recommendation
    """
    quality = run_quality_lens(profile, confidence, risk)
    speculative = run_speculative_lens(profile, confidence)
    multibagger = run_multibagger_lens(profile, confidence)

    risk_adj = risk.recommended_risk_adjustment if risk else 0.0
    aggregated = aggregate_reasoning(quality, speculative, multibagger, risk_adj)

    return aggregated
