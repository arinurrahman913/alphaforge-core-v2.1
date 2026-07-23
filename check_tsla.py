import sys
sys.path.insert(0, ".")
from alphaforge.layer2.contracts import ScreeningCandidate
from alphaforge.layer2.evidence import build_evidence_for_ticker
from alphaforge.layer2.knowledge import build_knowledge_for_ticker

candidate = ScreeningCandidate("TSLA", "NASDAQ", True)
evidence = build_evidence_for_ticker(candidate)
knowledge = build_knowledge_for_ticker(evidence, candidate)

print("TSLA Fundamental Data:")
print(f"  Last price: \")
print(f"  Market cap: \")
print(f"  PE ratio: {evidence.fundamental.pe_ratio:.1f}x")
print(f"  Revenue: \")
print(f"  Net income: \")
print(f"  Free cash flow: \")
print(f"  D/E ratio: {evidence.fundamental.debt_to_equity:.2f}")
print(f"\nValuation:")
print(f"  P/S: {knowledge.valuation.ps_ratio:.2f}x")
print(f"  P/B: {knowledge.valuation.pb_ratio:.2f}x")
print(f"\nOwnership:")
print(f"  Institutional: {evidence.institutional_ownership.percentage:.2f}%")
print(f"  Form 4 filings (30d): {knowledge.ownership.insider_filing_activity_30d}")
