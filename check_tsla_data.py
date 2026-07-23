#!/usr/bin/env python3
import sys
sys.path.insert(0, ".")
from alphaforge.layer2.contracts import ScreeningCandidate
from alphaforge.layer2.evidence import build_evidence_for_ticker
from alphaforge.layer2.knowledge import build_knowledge_for_ticker

candidate = ScreeningCandidate("TSLA", "NASDAQ", True)
evidence = build_evidence_for_ticker(candidate)
knowledge = build_knowledge_for_ticker(evidence, candidate)

print("TSLA Fundamental Data:")
print(f"  Last price: ${evidence.price_market.last_price}")
print(f"  Market cap: ${evidence.price_market.market_cap:,.0f}")
print(f"  PE ratio: {evidence.fundamental.pe_ratio:.1f}x")
print(f"  Revenue: ${evidence.fundamental.revenue:,.0f}")
print(f"  Net income: ${evidence.fundamental.net_income:,.0f}")
print(f"  Free cash flow: ${evidence.fundamental.free_cash_flow:,.0f}")
print(f"  D/E ratio: {evidence.fundamental.debt_to_equity:.2f}")
print(f"\nValuation:")
print(f"  P/S: {knowledge.valuation.ps_ratio:.2f}x")
print(f"  P/B: {knowledge.valuation.pb_ratio:.2f}x")
print(f"\nOwnership:")
print(f"  Institutional: {evidence.institutional_ownership.percentage:.2f}%")
print(f"  Form 4 filings (30d): {knowledge.ownership.insider_filing_activity_30d}")
