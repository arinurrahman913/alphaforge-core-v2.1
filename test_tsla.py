import sys
sys.path.insert(0, ".")
from alphaforge.layer2.contracts import ScreeningCandidate
from alphaforge.layer2.evidence import build_evidence_for_ticker
from alphaforge.layer2.knowledge import build_knowledge_for_ticker
from alphaforge.layer2.reasoning import run_reasoning_pipeline

candidate = ScreeningCandidate("TSLA", "NASDAQ", True)
evidence = build_evidence_for_ticker(candidate)
knowledge = build_knowledge_for_ticker(evidence, candidate)

reasoning = run_reasoning_pipeline(knowledge, None, None, None, None)

print(f"TSLA Reasoning (dengan increased insider weight):\n")
print(f"Quality:")
print(f"  Stance: {reasoning.quality_compound.stance}")
print(f"  Score: {reasoning.quality_compound.confidence.score}")
print(f"  Positive: {reasoning.quality_compound.positive_factors[:3]}")

print(f"\nMultibagger:")
print(f"  Stance: {reasoning.multibagger.stance}")
print(f"  Score: {reasoning.multibagger.confidence.score}")
print(f"  Positive: {reasoning.multibagger.positive_factors[:3]}")

print(f"\nMetrics:")
print(f"  Quality: {reasoning.quality_compound.key_metrics}")
print(f"  Multibagger: {reasoning.multibagger.key_metrics}")
