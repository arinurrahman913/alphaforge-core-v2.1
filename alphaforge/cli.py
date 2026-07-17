"""CLI: python -m alphaforge.cli <layer1|screening> [opsi]"""
from __future__ import annotations

import argparse
import json
import sys

from .layer1 import build_market_context_package
from .layer2 import run_screening, run_evidence, run_knowledge, run_peer_comparison, run_confidence, run_risk_assessment, run_reasoning_pipeline, run_aggregator


def _write(data: str, out: str | None) -> None:
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(data)
        print(f"Ditulis ke {out}", file=sys.stderr)
    else:
        print(data)


def main() -> None:
    parser = argparse.ArgumentParser(prog="alphaforge")
    sub = parser.add_subparsers(dest="command", required=True)

    layer1_parser = sub.add_parser("layer1", help="Hitung Market Context Package")
    layer1_parser.add_argument("--out", type=str, default=None, help="Tulis JSON ke file (default: stdout)")
    layer1_parser.add_argument("--with-screening", action="store_true",
                                help="Jalankan Screening dulu supaya market_breadth bisa dihitung (lambat)")
    layer1_parser.add_argument("--screening-limit", type=int, default=None,
                                help="Batasi jumlah ticker yang di-screening (buat testing)")

    screening_parser = sub.add_parser("screening", help="Jalankan Screening (Layer 2, tahap 1)")
    screening_parser.add_argument("--out", type=str, default=None, help="Tulis JSON ke file (default: stdout)")
    screening_parser.add_argument("--limit", type=int, default=None,
                                   help="Batasi jumlah ticker yang di-screening (buat testing)")

    evidence_parser = sub.add_parser("evidence", help="Jalankan Evidence (Layer 2, tahap 2) — butuh Screening dulu")
    evidence_parser.add_argument("--screening-out", type=str, required=True,
                                help="Path ke screening.json hasil Screening")
    evidence_parser.add_argument("--out", type=str, default=None, help="Tulis JSON ke file (default: stdout)")
    evidence_parser.add_argument("--limit", type=int, default=None,
                                help="Batasi jumlah ticker yang di-evidence (buat testing)")

    knowledge_parser = sub.add_parser("knowledge", help="Jalankan Knowledge (Layer 2, tahap 3) — butuh Evidence dulu")
    knowledge_parser.add_argument("--evidence-out", type=str, required=True,
                                 help="Path ke evidence.json hasil Evidence")
    knowledge_parser.add_argument("--screening-out", type=str, default=None,
                                 help="Path ke screening.json (optional, untuk supplementary flags)")
    knowledge_parser.add_argument("--out", type=str, default=None, help="Tulis JSON ke file (default: stdout)")
    knowledge_parser.add_argument("--limit", type=int, default=None,
                                 help="Batasi jumlah ticker yang di-knowledge (buat testing)")

    peer_parser = sub.add_parser("peer", help="Jalankan Peer Comparison (Layer 2, Fase B) — butuh Knowledge dulu")
    peer_parser.add_argument("--knowledge-out", type=str, required=True,
                            help="Path ke knowledge.json hasil Knowledge (Fase A complete)")
    peer_parser.add_argument("--out", type=str, default=None, help="Tulis JSON ke file (default: stdout)")
    peer_parser.add_argument("--limit", type=int, default=None,
                            help="Batasi jumlah ticker yang di-peer (buat testing)")

    confidence_parser = sub.add_parser("confidence", help="Jalankan Confidence Scoring (Layer 2, Fase B, tahap 2) — butuh Knowledge + Peer dulu")
    confidence_parser.add_argument("--knowledge-out", type=str, required=True,
                                  help="Path ke knowledge.json hasil Knowledge")
    confidence_parser.add_argument("--peer-out", type=str, default=None,
                                  help="Path ke peer_results.json (optional, untuk peer group scoring)")
    confidence_parser.add_argument("--out", type=str, default=None, help="Tulis JSON ke file (default: stdout)")
    confidence_parser.add_argument("--limit", type=int, default=None,
                                  help="Batasi jumlah ticker (buat testing)")

    risk_parser = sub.add_parser("risk", help="Jalankan Risk Assessment (Layer 2, Fase B, tahap 3) — butuh Knowledge dulu")
    risk_parser.add_argument("--knowledge-out", type=str, required=True,
                            help="Path ke knowledge.json hasil Knowledge")
    risk_parser.add_argument("--out", type=str, default=None, help="Tulis JSON ke file (default: stdout)")
    risk_parser.add_argument("--limit", type=int, default=None,
                            help="Batasi jumlah ticker (buat testing)")

    reasoning_parser = sub.add_parser("reasoning", help="Jalankan Reasoning Pipeline (Layer 2, Fase B, tahap 4) — butuh Knowledge+Confidence+Risk dulu")
    reasoning_parser.add_argument("--knowledge-out", type=str, required=True,
                                 help="Path ke knowledge.json hasil Knowledge")
    reasoning_parser.add_argument("--confidence-out", type=str, default=None,
                                 help="Path ke confidence_scores.json (optional)")
    reasoning_parser.add_argument("--risk-out", type=str, default=None,
                                 help="Path ke risk_assessments.json (optional)")
    reasoning_parser.add_argument("--out", type=str, default=None, help="Tulis JSON ke file (default: stdout)")
    reasoning_parser.add_argument("--limit", type=int, default=None,
                                 help="Batasi jumlah ticker (buat testing)")

    aggregator_parser = sub.add_parser("aggregator", help="Jalankan Aggregator (Layer 2, Fase B, tahap 5/final) — butuh semua stages")
    aggregator_parser.add_argument("--knowledge-out", type=str, required=True,
                                  help="Path ke knowledge.json")
    aggregator_parser.add_argument("--peer-out", type=str, default=None,
                                  help="Path ke peer_results.json (optional)")
    aggregator_parser.add_argument("--confidence-out", type=str, default=None,
                                  help="Path ke confidence_scores.json (optional)")
    aggregator_parser.add_argument("--risk-out", type=str, default=None,
                                  help="Path ke risk_assessments.json (optional)")
    aggregator_parser.add_argument("--reasoning-out", type=str, default=None,
                                  help="Path ke reasoning_outputs.json (optional)")
    aggregator_parser.add_argument("--out", type=str, default=None, help="Tulis JSON ke file (default: stdout)")
    aggregator_parser.add_argument("--limit", type=int, default=None,
                                  help="Batasi jumlah ticker (buat testing)")

    args = parser.parse_args()

    if args.command == "layer1":
        price_cache = None
        if args.with_screening:
            print("Menjalankan Screening dulu untuk mengisi cache market_breadth...", file=sys.stderr)
            _, price_cache = run_screening(limit=args.screening_limit)
            print(f"Screening selesai: {len(price_cache)} ticker di cache harga.", file=sys.stderr)
        package = build_market_context_package(price_cache=price_cache)
        _write(json.dumps(package.to_dict(), indent=2, ensure_ascii=False), args.out)

    elif args.command == "screening":
        result, _ = run_screening(limit=args.limit)
        print(
            f"Universe mentah: {result.universe_raw} · setelah filter tipe: "
            f"{result.universe_after_cheap_filter} · di-scan: {result.universe_scanned} · "
            f"lolos: {len(result.passed)} · hard exclude: {len(result.hard_excluded)}",
            file=sys.stderr,
        )
        _write(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), args.out)

    elif args.command == "evidence":
        with open(args.screening_out, "r", encoding="utf-8") as f:
            screening_dict = json.load(f)

        # Reconstruct ScreeningResult dari dict
        from .layer2.contracts import ScreeningCandidate, ScreeningResult
        screening_result = ScreeningResult(
            universe_raw=screening_dict["universe_raw"],
            universe_after_cheap_filter=screening_dict["universe_after_cheap_filter"],
            universe_scanned=screening_dict["universe_scanned"],
            passed=[ScreeningCandidate(**c) for c in screening_dict["passed"]],
            hard_excluded=[ScreeningCandidate(**c) for c in screening_dict["hard_excluded"]],
            generated_at=screening_dict["generated_at"]
        )

        # Apply limit jika ada
        if args.limit:
            screening_result.passed = screening_result.passed[:args.limit]

        packages = run_evidence(screening_result)
        result_dict = {
            "screening_universe": screening_result.universe_raw,
            "screening_passed": len(screening_result.passed),
            "evidence_generated": len(packages),
            "generated_at": packages[0].generated_at if packages else None,
            "packages": [p.to_dict() for p in packages],
        }
        _write(json.dumps(result_dict, indent=2, ensure_ascii=False), args.out)

    elif args.command == "knowledge":
        with open(args.evidence_out, "r", encoding="utf-8") as f:
            evidence_dict = json.load(f)

        # Reconstruct Evidence packages properly
        from .layer2.contracts import (
            EvidencePackage, PriceBar, SourceMetadata,
            PriceMarketData, FundamentalData, InstitutionalOwnership,
            NewsCollection, SecFilings, QuarterlyFundamental
        )
        evidence_packages = []
        for pkg_dict in evidence_dict.get("packages", []):
            # Reconstruct nested objects
            pm_dict = pkg_dict["price_market"]
            price_bars = [
                PriceBar(**bar) for bar in pm_dict.get("price_history", [])
            ]
            price_market = PriceMarketData(
                metadata=SourceMetadata(**pm_dict["metadata"]),
                last_price=pm_dict.get("last_price"),
                open=pm_dict.get("open"),
                high=pm_dict.get("high"),
                low=pm_dict.get("low"),
                close=pm_dict.get("close"),
                volume=pm_dict.get("volume"),
                market_cap=pm_dict.get("market_cap"),
                shares_outstanding=pm_dict.get("shares_outstanding"),
                beta=pm_dict.get("beta"),
                high_52w=pm_dict.get("high_52w"),
                low_52w=pm_dict.get("low_52w"),
                price_history=price_bars
            )

            fund_dict = pkg_dict["fundamental"]
            fundamental = FundamentalData(
                metadata=SourceMetadata(**fund_dict["metadata"]),
                revenue=fund_dict.get("revenue"),
                net_income=fund_dict.get("net_income"),
                eps=fund_dict.get("eps"),
                pe_ratio=fund_dict.get("pe_ratio"),
                debt_to_equity=fund_dict.get("debt_to_equity"),
                current_ratio=fund_dict.get("current_ratio"),
                quick_ratio=fund_dict.get("quick_ratio"),
                roe=fund_dict.get("roe"),
                roa=fund_dict.get("roa"),
                operating_margin=fund_dict.get("operating_margin"),
                gross_margin=fund_dict.get("gross_margin"),
                free_cash_flow=fund_dict.get("free_cash_flow"),
                dividend_yield=fund_dict.get("dividend_yield"),
                payout_ratio=fund_dict.get("payout_ratio"),
                book_value_per_share=fund_dict.get("book_value_per_share"),
                asset_turnover=fund_dict.get("asset_turnover"),
                inventory_turnover=fund_dict.get("inventory_turnover"),
                interest_coverage=fund_dict.get("interest_coverage"),
                quarterly_data=[
                    QuarterlyFundamental(**q) for q in fund_dict.get("quarterly_data") or []
                ]
            )

            inst_dict = pkg_dict["institutional_ownership"]
            institutional_ownership = InstitutionalOwnership(
                metadata=SourceMetadata(**inst_dict["metadata"]),
                percentage=inst_dict.get("percentage")
            )

            news_dict = pkg_dict["news"]
            news = NewsCollection(
                news=[],
                metadata=SourceMetadata(**news_dict.get("metadata")) if news_dict.get("metadata") else None
            )

            sec_dict = pkg_dict["sec_filings"]
            sec_filings = SecFilings(
                filings=[],
                metadata=SourceMetadata(**sec_dict.get("metadata")) if sec_dict.get("metadata") else None
            )

            pkg = EvidencePackage(
                ticker=pkg_dict["ticker"],
                exchange=pkg_dict["exchange"],
                price_market=price_market,
                fundamental=fundamental,
                institutional_ownership=institutional_ownership,
                news=news,
                sec_filings=sec_filings,
                generated_at=pkg_dict["generated_at"]
            )
            evidence_packages.append(pkg)

        # Load screening candidates jika ada
        screening_candidates = []
        if args.screening_out:
            with open(args.screening_out, "r", encoding="utf-8") as f:
                screening_dict = json.load(f)
            from .layer2.contracts import ScreeningCandidate
            screening_candidates = [ScreeningCandidate(**c) for c in screening_dict.get("passed", [])]

        # Apply limit
        if args.limit:
            evidence_packages = evidence_packages[:args.limit]

        profiles = run_knowledge(evidence_packages, screening_candidates)
        result_dict = {
            "evidence_count": len(evidence_packages),
            "knowledge_generated": len(profiles),
            "generated_at": profiles[0].metadata.evidence_date if profiles else None,
            "profiles": [p.to_dict() for p in profiles],
        }
        _write(json.dumps(result_dict, indent=2, ensure_ascii=False), args.out)

    elif args.command == "peer":
        with open(args.knowledge_out, "r", encoding="utf-8") as f:
            knowledge_dict = json.load(f)

        # Reconstruct KnowledgeProfile objects properly
        from .layer2.knowledge_contracts import (
            KnowledgeProfile, KnowledgeMetadata, FinancialHealth, Ownership,
            RevenueTrend, MarginTrend, BalanceSheet, CashFlowTrend, CapExInfo,
            CompetitiveStructure, CompetitiveMomentum, HistoricalTrend, Valuation, Governance
        )

        profiles = []
        for profile_dict in knowledge_dict.get("profiles", []):
            # Reconstruct nested financial health objects
            fh_dict = profile_dict["financial_health"]
            financial_health = FinancialHealth(
                revenue_trend=RevenueTrend(**fh_dict["revenue_trend"]),
                gross_margin_trend=MarginTrend(**fh_dict["gross_margin_trend"]),
                operating_margin_trend=MarginTrend(**fh_dict["operating_margin_trend"]),
                net_margin_trend=MarginTrend(**fh_dict["net_margin_trend"]),
                balance_sheet=BalanceSheet(**fh_dict["balance_sheet"]),
                cash_flow_trend=CashFlowTrend(**fh_dict["cash_flow_trend"]),
                capex_info=CapExInfo(**fh_dict["capex_info"])
            )

            # Reconstruct competitive structures
            cs_dict = profile_dict["competitive_structure"]
            competitive_structure = CompetitiveStructure(**cs_dict)

            cm_dict = profile_dict["competitive_momentum"]
            competitive_momentum = CompetitiveMomentum(**cm_dict)

            # Reconstruct historical trend
            ht_dict = profile_dict["historical_trend"]
            historical_trend = HistoricalTrend(**ht_dict)

            # Reconstruct ownership
            own_dict = profile_dict["ownership"]
            ownership = Ownership(**own_dict)

            # Reconstruct valuation
            val_dict = profile_dict["valuation"]
            valuation = Valuation(**val_dict)

            # Reconstruct governance
            gov_dict = profile_dict["governance"]
            governance = Governance(**gov_dict)

            # Reconstruct metadata
            meta_dict = profile_dict["metadata"]
            metadata = KnowledgeMetadata(**meta_dict)

            # Create full KnowledgeProfile
            profile = KnowledgeProfile(
                ticker=profile_dict["ticker"],
                exchange=profile_dict["exchange"],
                sector=profile_dict.get("sector"),
                size_category=profile_dict.get("size_category"),
                screening_flags=profile_dict.get("screening_flags", []),
                financial_health=financial_health,
                competitive_structure=competitive_structure,
                competitive_momentum=competitive_momentum,
                historical_trend=historical_trend,
                ownership=ownership,
                valuation=valuation,
                governance=governance,
                metadata=metadata
            )
            profiles.append(profile)

        # Apply limit if specified
        if args.limit:
            profiles = profiles[:args.limit]

        # Run peer comparison
        comparisons = run_peer_comparison(profiles)

        # Output results
        result_dict = {
            "knowledge_count": len(profiles),
            "peer_comparisons_generated": len(comparisons),
            "generated_at": comparisons[0].generated_at if comparisons else None,
            "comparisons": [c.to_dict() for c in comparisons],
        }
        _write(json.dumps(result_dict, indent=2, ensure_ascii=False), args.out)

    elif args.command == "confidence":
        with open(args.knowledge_out, "r", encoding="utf-8") as f:
            knowledge_dict = json.load(f)

        # Reconstruct KnowledgeProfile objects (same as peer command)
        from .layer2.knowledge_contracts import (
            KnowledgeProfile, KnowledgeMetadata, FinancialHealth, Ownership,
            RevenueTrend, MarginTrend, BalanceSheet, CashFlowTrend, CapExInfo,
            CompetitiveStructure, CompetitiveMomentum, HistoricalTrend, Valuation, Governance
        )

        profiles = []
        for profile_dict in knowledge_dict.get("profiles", []):
            fh_dict = profile_dict["financial_health"]
            financial_health = FinancialHealth(
                revenue_trend=RevenueTrend(**fh_dict["revenue_trend"]),
                gross_margin_trend=MarginTrend(**fh_dict["gross_margin_trend"]),
                operating_margin_trend=MarginTrend(**fh_dict["operating_margin_trend"]),
                net_margin_trend=MarginTrend(**fh_dict["net_margin_trend"]),
                balance_sheet=BalanceSheet(**fh_dict["balance_sheet"]),
                cash_flow_trend=CashFlowTrend(**fh_dict["cash_flow_trend"]),
                capex_info=CapExInfo(**fh_dict["capex_info"])
            )

            cs_dict = profile_dict["competitive_structure"]
            competitive_structure = CompetitiveStructure(**cs_dict)

            cm_dict = profile_dict["competitive_momentum"]
            competitive_momentum = CompetitiveMomentum(**cm_dict)

            ht_dict = profile_dict["historical_trend"]
            historical_trend = HistoricalTrend(**ht_dict)

            own_dict = profile_dict["ownership"]
            ownership = Ownership(**own_dict)

            val_dict = profile_dict["valuation"]
            valuation = Valuation(**val_dict)

            gov_dict = profile_dict["governance"]
            governance = Governance(**gov_dict)

            meta_dict = profile_dict["metadata"]
            metadata = KnowledgeMetadata(**meta_dict)

            profile = KnowledgeProfile(
                ticker=profile_dict["ticker"],
                exchange=profile_dict["exchange"],
                sector=profile_dict.get("sector"),
                size_category=profile_dict.get("size_category"),
                screening_flags=profile_dict.get("screening_flags", []),
                financial_health=financial_health,
                competitive_structure=competitive_structure,
                competitive_momentum=competitive_momentum,
                historical_trend=historical_trend,
                ownership=ownership,
                valuation=valuation,
                governance=governance,
                metadata=metadata
            )
            profiles.append(profile)

        # Load peer comparisons if provided
        comparisons = None
        if args.peer_out:
            with open(args.peer_out, "r", encoding="utf-8") as f:
                peer_dict = json.load(f)
            from .layer2.peer_contracts import (
                PeerComparisonResult, PeerGroupInfo, PeerMetricComparison
            )
            comparisons = []
            for comp_dict in peer_dict.get("comparisons", []):
                pg_dict = comp_dict["peer_group"]
                peer_group = PeerGroupInfo(**pg_dict)

                # Reconstruct metric comparisons
                metric_comparisons = {}
                for metric_key in [
                    "pe_ratio_comparison", "ps_ratio_comparison", "pb_ratio_comparison",
                    "fcf_yield_comparison", "gross_margin_comparison", "operating_margin_comparison",
                    "net_margin_comparison", "revenue_growth_comparison", "roe_comparison",
                    "roa_comparison", "debt_to_equity_comparison"
                ]:
                    metric_dict = comp_dict.get(metric_key)
                    if metric_dict:
                        metric_comparisons[metric_key] = PeerMetricComparison(**metric_dict)
                    else:
                        metric_comparisons[metric_key] = None

                comparison = PeerComparisonResult(
                    ticker=comp_dict["ticker"],
                    exchange=comp_dict["exchange"],
                    peer_group=peer_group,
                    generated_at=comp_dict["generated_at"],
                    peer_group_basis=comp_dict.get("peer_group_basis", "screening_universe"),
                    **metric_comparisons
                )
                comparisons.append(comparison)

        # Apply limit
        if args.limit:
            profiles = profiles[:args.limit]
            if comparisons:
                comparisons = comparisons[:args.limit]

        # Run confidence scoring
        scores = run_confidence(profiles, comparisons)

        # Output results
        result_dict = {
            "knowledge_count": len(profiles),
            "confidence_scores_generated": len(scores),
            "generated_at": scores[0].assessed_at if scores else None,
            "scores": [s.to_dict() for s in scores],
        }
        _write(json.dumps(result_dict, indent=2, ensure_ascii=False), args.out)

    elif args.command == "risk":
        with open(args.knowledge_out, "r", encoding="utf-8") as f:
            knowledge_dict = json.load(f)

        # Reconstruct KnowledgeProfile objects (same as confidence command)
        from .layer2.knowledge_contracts import (
            KnowledgeProfile, KnowledgeMetadata, FinancialHealth, Ownership,
            RevenueTrend, MarginTrend, BalanceSheet, CashFlowTrend, CapExInfo,
            CompetitiveStructure, CompetitiveMomentum, HistoricalTrend, Valuation, Governance
        )

        profiles = []
        for profile_dict in knowledge_dict.get("profiles", []):
            fh_dict = profile_dict["financial_health"]
            financial_health = FinancialHealth(
                revenue_trend=RevenueTrend(**fh_dict["revenue_trend"]),
                gross_margin_trend=MarginTrend(**fh_dict["gross_margin_trend"]),
                operating_margin_trend=MarginTrend(**fh_dict["operating_margin_trend"]),
                net_margin_trend=MarginTrend(**fh_dict["net_margin_trend"]),
                balance_sheet=BalanceSheet(**fh_dict["balance_sheet"]),
                cash_flow_trend=CashFlowTrend(**fh_dict["cash_flow_trend"]),
                capex_info=CapExInfo(**fh_dict["capex_info"])
            )

            cs_dict = profile_dict["competitive_structure"]
            competitive_structure = CompetitiveStructure(**cs_dict)

            cm_dict = profile_dict["competitive_momentum"]
            competitive_momentum = CompetitiveMomentum(**cm_dict)

            ht_dict = profile_dict["historical_trend"]
            historical_trend = HistoricalTrend(**ht_dict)

            own_dict = profile_dict["ownership"]
            ownership = Ownership(**own_dict)

            val_dict = profile_dict["valuation"]
            valuation = Valuation(**val_dict)

            gov_dict = profile_dict["governance"]
            governance = Governance(**gov_dict)

            meta_dict = profile_dict["metadata"]
            metadata = KnowledgeMetadata(**meta_dict)

            profile = KnowledgeProfile(
                ticker=profile_dict["ticker"],
                exchange=profile_dict["exchange"],
                sector=profile_dict.get("sector"),
                size_category=profile_dict.get("size_category"),
                screening_flags=profile_dict.get("screening_flags", []),
                financial_health=financial_health,
                competitive_structure=competitive_structure,
                competitive_momentum=competitive_momentum,
                historical_trend=historical_trend,
                ownership=ownership,
                valuation=valuation,
                governance=governance,
                metadata=metadata
            )
            profiles.append(profile)

        # Apply limit
        if args.limit:
            profiles = profiles[:args.limit]

        # Run risk assessment
        assessments = run_risk_assessment(profiles)

        # Output results
        result_dict = {
            "knowledge_count": len(profiles),
            "risk_assessments_generated": len(assessments),
            "generated_at": assessments[0].assessed_at if assessments else None,
            "assessments": [a.to_dict() for a in assessments],
        }
        _write(json.dumps(result_dict, indent=2, ensure_ascii=False), args.out)

    elif args.command == "reasoning":
        with open(args.knowledge_out, "r", encoding="utf-8") as f:
            knowledge_dict = json.load(f)

        # Reconstruct KnowledgeProfile objects
        from .layer2.knowledge_contracts import (
            KnowledgeProfile, KnowledgeMetadata, FinancialHealth, Ownership,
            RevenueTrend, MarginTrend, BalanceSheet, CashFlowTrend, CapExInfo,
            CompetitiveStructure, CompetitiveMomentum, HistoricalTrend, Valuation, Governance
        )

        profiles = []
        for profile_dict in knowledge_dict.get("profiles", []):
            fh_dict = profile_dict["financial_health"]
            financial_health = FinancialHealth(
                revenue_trend=RevenueTrend(**fh_dict["revenue_trend"]),
                gross_margin_trend=MarginTrend(**fh_dict["gross_margin_trend"]),
                operating_margin_trend=MarginTrend(**fh_dict["operating_margin_trend"]),
                net_margin_trend=MarginTrend(**fh_dict["net_margin_trend"]),
                balance_sheet=BalanceSheet(**fh_dict["balance_sheet"]),
                cash_flow_trend=CashFlowTrend(**fh_dict["cash_flow_trend"]),
                capex_info=CapExInfo(**fh_dict["capex_info"])
            )

            cs_dict = profile_dict["competitive_structure"]
            competitive_structure = CompetitiveStructure(**cs_dict)

            cm_dict = profile_dict["competitive_momentum"]
            competitive_momentum = CompetitiveMomentum(**cm_dict)

            ht_dict = profile_dict["historical_trend"]
            historical_trend = HistoricalTrend(**ht_dict)

            own_dict = profile_dict["ownership"]
            ownership = Ownership(**own_dict)

            val_dict = profile_dict["valuation"]
            valuation = Valuation(**val_dict)

            gov_dict = profile_dict["governance"]
            governance = Governance(**gov_dict)

            meta_dict = profile_dict["metadata"]
            metadata = KnowledgeMetadata(**meta_dict)

            profile = KnowledgeProfile(
                ticker=profile_dict["ticker"],
                exchange=profile_dict["exchange"],
                sector=profile_dict.get("sector"),
                size_category=profile_dict.get("size_category"),
                screening_flags=profile_dict.get("screening_flags", []),
                financial_health=financial_health,
                competitive_structure=competitive_structure,
                competitive_momentum=competitive_momentum,
                historical_trend=historical_trend,
                ownership=ownership,
                valuation=valuation,
                governance=governance,
                metadata=metadata
            )
            profiles.append(profile)

        # Load confidence scores if provided
        confidence_map = {}
        if args.confidence_out:
            with open(args.confidence_out, "r", encoding="utf-8") as f:
                confidence_dict = json.load(f)
            from .layer2.confidence_contracts import ConfidenceScore, DataQualityScore
            for score_dict in confidence_dict.get("scores", []):
                quality_scores = [
                    DataQualityScore(**qs) for qs in score_dict.get("quality_scores", [])
                ]
                score_dict_copy = score_dict.copy()
                score_dict_copy["quality_scores"] = quality_scores
                confidence = ConfidenceScore(**score_dict_copy)
                confidence_map[confidence.ticker] = confidence

        # Load risk assessments if provided
        risk_map = {}
        if args.risk_out:
            with open(args.risk_out, "r", encoding="utf-8") as f:
                risk_dict = json.load(f)
            from .layer2.risk_contracts import RiskAssessment, RedFlag
            for assess_dict in risk_dict.get("assessments", []):
                red_flags = [
                    RedFlag(**rf) for rf in assess_dict.get("red_flags", [])
                ]
                assess_dict_copy = assess_dict.copy()
                assess_dict_copy["red_flags"] = red_flags
                risk = RiskAssessment(**assess_dict_copy)
                risk_map[risk.ticker] = risk

        # Apply limit
        if args.limit:
            profiles = profiles[:args.limit]

        # Run reasoning pipeline for each profile
        reasonings = []
        for profile in profiles:
            confidence = confidence_map.get(profile.ticker)
            risk = risk_map.get(profile.ticker)
            reasoning = run_reasoning_pipeline(profile, confidence, risk)
            reasonings.append(reasoning)

        # Output results
        result_dict = {
            "knowledge_count": len(profiles),
            "reasoning_outputs_generated": len(reasonings),
            "generated_at": reasonings[0].aggregated_at if reasonings else None,
            "reasoning_outputs": [r.to_dict() for r in reasonings],
        }
        _write(json.dumps(result_dict, indent=2, ensure_ascii=False), args.out)

    elif args.command == "aggregator":
        with open(args.knowledge_out, "r", encoding="utf-8") as f:
            knowledge_dict = json.load(f)

        # Reconstruct KnowledgeProfile objects (simplified - reuse pattern)
        from .layer2.knowledge_contracts import (
            KnowledgeProfile, KnowledgeMetadata, FinancialHealth, Ownership,
            RevenueTrend, MarginTrend, BalanceSheet, CashFlowTrend, CapExInfo,
            CompetitiveStructure, CompetitiveMomentum, HistoricalTrend, Valuation, Governance
        )

        profiles = []
        for profile_dict in knowledge_dict.get("profiles", []):
            fh_dict = profile_dict["financial_health"]
            financial_health = FinancialHealth(
                revenue_trend=RevenueTrend(**fh_dict["revenue_trend"]),
                gross_margin_trend=MarginTrend(**fh_dict["gross_margin_trend"]),
                operating_margin_trend=MarginTrend(**fh_dict["operating_margin_trend"]),
                net_margin_trend=MarginTrend(**fh_dict["net_margin_trend"]),
                balance_sheet=BalanceSheet(**fh_dict["balance_sheet"]),
                cash_flow_trend=CashFlowTrend(**fh_dict["cash_flow_trend"]),
                capex_info=CapExInfo(**fh_dict["capex_info"])
            )
            cs_dict = profile_dict["competitive_structure"]
            competitive_structure = CompetitiveStructure(**cs_dict)
            cm_dict = profile_dict["competitive_momentum"]
            competitive_momentum = CompetitiveMomentum(**cm_dict)
            ht_dict = profile_dict["historical_trend"]
            historical_trend = HistoricalTrend(**ht_dict)
            own_dict = profile_dict["ownership"]
            ownership = Ownership(**own_dict)
            val_dict = profile_dict["valuation"]
            valuation = Valuation(**val_dict)
            gov_dict = profile_dict["governance"]
            governance = Governance(**gov_dict)
            meta_dict = profile_dict["metadata"]
            metadata = KnowledgeMetadata(**meta_dict)

            profile = KnowledgeProfile(
                ticker=profile_dict["ticker"],
                exchange=profile_dict["exchange"],
                sector=profile_dict.get("sector"),
                size_category=profile_dict.get("size_category"),
                screening_flags=profile_dict.get("screening_flags", []),
                financial_health=financial_health,
                competitive_structure=competitive_structure,
                competitive_momentum=competitive_momentum,
                historical_trend=historical_trend,
                ownership=ownership,
                valuation=valuation,
                governance=governance,
                metadata=metadata
            )
            profiles.append(profile)

        # Load optional outputs (peer, confidence, risk, reasoning)
        peers, confidences, risks, reasonings = None, None, None, None

        if args.peer_out:
            with open(args.peer_out, "r", encoding="utf-8") as f:
                peer_dict = json.load(f)
            from .layer2.peer_contracts import PeerComparisonResult, PeerGroupInfo, PeerMetricComparison
            peers = []
            for comp_dict in peer_dict.get("comparisons", []):
                pg_dict = comp_dict["peer_group"]
                peer_group = PeerGroupInfo(**pg_dict)
                metric_comparisons = {}
                for metric_key in [
                    "pe_ratio_comparison", "ps_ratio_comparison", "pb_ratio_comparison",
                    "fcf_yield_comparison", "gross_margin_comparison", "operating_margin_comparison",
                    "net_margin_comparison", "revenue_growth_comparison", "roe_comparison",
                    "roa_comparison", "debt_to_equity_comparison"
                ]:
                    metric_dict = comp_dict.get(metric_key)
                    metric_comparisons[metric_key] = PeerMetricComparison(**metric_dict) if metric_dict else None

                peers.append(PeerComparisonResult(
                    ticker=comp_dict["ticker"],
                    exchange=comp_dict["exchange"],
                    peer_group=peer_group,
                    generated_at=comp_dict["generated_at"],
                    peer_group_basis=comp_dict.get("peer_group_basis", "screening_universe"),
                    **metric_comparisons
                ))

        if args.confidence_out:
            with open(args.confidence_out, "r", encoding="utf-8") as f:
                conf_dict = json.load(f)
            from .layer2.confidence_contracts import ConfidenceScore, DataQualityScore
            confidences = []
            for score_dict in conf_dict.get("scores", []):
                quality_scores = [DataQualityScore(**qs) for qs in score_dict.get("quality_scores", [])]
                score_dict_copy = score_dict.copy()
                score_dict_copy["quality_scores"] = quality_scores
                confidences.append(ConfidenceScore(**score_dict_copy))

        if args.risk_out:
            with open(args.risk_out, "r", encoding="utf-8") as f:
                risk_dict = json.load(f)
            from .layer2.risk_contracts import RiskAssessment, RedFlag
            risks = []
            for assess_dict in risk_dict.get("assessments", []):
                red_flags = [RedFlag(**rf) for rf in assess_dict.get("red_flags", [])]
                assess_dict_copy = assess_dict.copy()
                assess_dict_copy["red_flags"] = red_flags
                risks.append(RiskAssessment(**assess_dict_copy))

        if args.reasoning_out:
            with open(args.reasoning_out, "r", encoding="utf-8") as f:
                reason_dict = json.load(f)
            from .layer2.reasoning_contracts import AggregatedReasoning, ReasoningOutput
            reasonings = []
            for out_dict in reason_dict.get("reasoning_outputs", []):
                # Reconstruct ReasoningOutput objects (simplified)
                for key in ["quality_output", "speculative_output", "multibagger_output"]:
                    if out_dict.get(key):
                        out_dict[key] = ReasoningOutput(**out_dict[key])
                reasonings.append(AggregatedReasoning(**out_dict))

        # Apply limit
        if args.limit:
            profiles = profiles[:args.limit]

        # Run aggregator
        recommendations = run_aggregator(profiles, peers, confidences, risks, reasonings)

        # Output results
        result_dict = {
            "profiles_count": len(profiles),
            "recommendations_generated": len(recommendations),
            "generated_at": recommendations[0].recommended_at if recommendations else None,
            "recommendations": [r.to_dict() for r in recommendations],
        }
        _write(json.dumps(result_dict, indent=2, ensure_ascii=False), args.out)


if __name__ == "__main__":
    main()
