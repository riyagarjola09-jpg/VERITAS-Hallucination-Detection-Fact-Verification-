"""
VERITAS Pipeline
----------------
Wires together claim extraction, evidence retrieval, verification,
calibration, and explanation generation into a single callable pipeline,
matching the architecture described in the accompanying research paper.
"""

from .claim_extractor import extract_claims
from .retriever import EvidenceRetriever
from .verifier import verify_claim
from .calibrator import calibrate
from .explainer import explain

_VERDICT_WEIGHT = {"Supported": 1.0, "Unverifiable": 0.5, "Contradicted": 0.0}


class VeritasPipeline:
    def __init__(self, kb_path=None):
        self.retriever = EvidenceRetriever(kb_path)

    def run(self, response_text):
        claims = extract_claims(response_text)
        results = []

        for claim in claims:
            evidence = self.retriever.retrieve(claim["text"])
            verification = verify_claim(claim, evidence)
            confidence = calibrate(
                verification["raw_score"],
                len(verification["supporting"]),
                len(verification["contradicting"]),
            )
            explanation = explain(claim, verification)

            results.append({
                "claim_id": claim["claim_id"],
                "text": claim["text"],
                "type": claim["type"],
                "verdict": verification["verdict"],
                "confidence": confidence,
                "explanation": explanation,
                "evidence": verification["supporting"] + verification["contradicting"],
            })

        return {
            "claims": results,
            "overall_trust_score": self._aggregate(results),
            "claim_count": len(results),
        }

    @staticmethod
    def _aggregate(results):
        if not results:
            return 1.0
        total = sum(_VERDICT_WEIGHT[r["verdict"]] * r["confidence"] for r in results)
        return round(total / len(results), 2)
