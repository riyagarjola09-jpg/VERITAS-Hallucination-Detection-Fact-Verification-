"""
Claim Extraction
----------------
Splits a raw LLM response into sentences, filters out non-factual
(subjective / conversational) sentences, and classifies the remaining
"claims" by type so downstream stages can prioritize risk appropriately.

In production this stage would use a fine-tuned claim-decomposition
model (e.g. an instruction-tuned LLM prompted to output atomic
propositions) plus a coreference resolver. This rule-based version is a
transparent, dependency-free stand-in that is good enough to demonstrate
the pipeline end-to-end.
"""

import re

SUBJECTIVE_MARKERS = [
    "i think", "i believe", "in my opinion", "i feel", "arguably",
    "personally", "it seems", "probably", "perhaps", "i guess",
]

CAUSAL_MARKERS = ["because", "causes", "leads to", "results in", "due to", "therefore"]

RISK_WEIGHTS = {
    "Numerical": 0.95,
    "Temporal": 0.85,
    "Named-Entity": 0.7,
    "Causal": 0.6,
    "Definitional": 0.5,
}


def _split_sentences(text):
    text = text.strip()
    # Naive sentence splitter: breaks on . ! ? followed by whitespace + capital/digit,
    # while trying not to split on common abbreviations (Mr., U.S., etc.)
    text = re.sub(r'\b(Mr|Mrs|Ms|Dr|vs|etc|e\.g|i\.e)\.', r'\1<DOT>', text)
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', text)
    return [p.replace('<DOT>', '.').strip() for p in parts if p.strip()]


def _is_factual(sentence):
    s = sentence.lower()
    if s.endswith('?'):
        return False
    if any(marker in s for marker in SUBJECTIVE_MARKERS):
        return False
    if len(sentence.split()) < 4:
        return False
    return True


def _classify_type(sentence):
    s = sentence.lower()
    if re.search(r'\b(1[5-9]\d{2}|20\d{2})\b', sentence):
        return "Temporal"
    if re.search(r'\d', sentence):
        return "Numerical"
    if any(m in s for m in CAUSAL_MARKERS):
        return "Causal"
    if re.search(r'\b[A-Z][a-zA-Z]{2,}(\s[A-Z][a-zA-Z]{2,})*\b', sentence):
        return "Named-Entity"
    return "Definitional"


def extract_claims(response_text):
    """Returns a risk-sorted list of atomic claim dicts extracted from response_text."""
    sentences = _split_sentences(response_text)
    claims = []
    for idx, sentence in enumerate(sentences):
        if not _is_factual(sentence):
            continue
        ctype = _classify_type(sentence)
        claims.append({
            "claim_id": f"c{idx + 1}",
            "text": sentence,
            "type": ctype,
            "risk_score": RISK_WEIGHTS.get(ctype, 0.5),
        })
    claims.sort(key=lambda c: -c["risk_score"])
    return claims
