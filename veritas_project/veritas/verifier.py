"""
Multi-Hop-Style Verification
-----------------------------
Classifies a claim against retrieved evidence as Supported, Contradicted,
or Unverifiable.

In production this stage is a transformer NLI/entailment model
(fine-tuned on FEVER-style Supported/Refuted/NotEnoughInfo data) wrapped
with multi-hop decomposition for claims that need chained facts. This
prototype uses a transparent lexical-overlap + numeric/negation-conflict
heuristic so the whole pipeline runs with zero model downloads -- the
interface (verify_claim -> verdict, raw_score, evidence) is exactly what
a real NLI model would plug into, so swapping it in later requires no
changes to the rest of the pipeline. See README "Production upgrade path".
"""

import re

NEGATIONS = {"not", "no", "never", "cannot", "isn't", "wasn't", "doesn't", "don't", "n't"}
STOPWORDS = set("""a an the of to in on at for with and or is are was were be been
being this that these those it its as by from has have had""".split())


def _tokens(text):
    return set(w for w in re.findall(r"[a-zA-Z0-9]+", text.lower()) if w not in STOPWORDS)


def _numbers(text):
    return set(re.findall(r"\d+(?:\.\d+)?", text))


def _has_negation(text):
    words = set(re.findall(r"[a-zA-Z']+", text.lower()))
    return bool(words & NEGATIONS)


def _subject_after_is(text):
    """For patterns like '... is Sydney' -> returns 'Sydney'."""
    m = re.search(r"\bis\s+([A-Z][a-zA-Z]+)", text)
    return m.group(1) if m else None


def _subject_before_is(text):
    """For patterns like 'Canberra is ...' -> returns 'Canberra'."""
    m = re.search(r"([A-Z][a-zA-Z]+)\s+is\b", text)
    return m.group(1) if m else None


def _entity_swap_conflict(claim_text, evidence_text):
    """Catches the common hallucination pattern where a claim asserts
    'X is <wrong entity>' while the evidence asserts '<right entity> is X'."""
    claimed_entity = _subject_after_is(claim_text)
    evidence_entity = _subject_before_is(evidence_text)
    if not claimed_entity or not evidence_entity:
        return False
    return claimed_entity.lower() != evidence_entity.lower()


def verify_claim(claim, evidence_list):
    """Returns {verdict, raw_score, supporting, contradicting, reason}."""
    if not evidence_list:
        return {
            "verdict": "Unverifiable",
            "raw_score": 0.15,
            "supporting": [],
            "contradicting": [],
            "reason": "no_evidence_found",
        }

    claim_tokens = _tokens(claim["text"])
    claim_numbers = _numbers(claim["text"])
    claim_negated = _has_negation(claim["text"])

    # Score every evidence item by lexical overlap with the claim first, so
    # that conflict checks are only applied against evidence that is actually
    # *about* the same thing as the claim -- a weakly related passage should
    # never be able to veto a strongly matching one.
    scored = []
    for ev in evidence_list:
        ev_tokens = _tokens(ev["text"])
        overlap = len(claim_tokens & ev_tokens) / max(1, len(claim_tokens))
        scored.append({**ev, "overlap": round(overlap, 3)})
    scored.sort(key=lambda e: -e["overlap"])

    RELEVANCE_FLOOR = 0.35  # an evidence item must clear this to be considered at all
    relevant = [e for e in scored if e["overlap"] >= RELEVANCE_FLOOR]

    if not relevant:
        return {
            "verdict": "Unverifiable", "raw_score": 0.3,
            "supporting": [], "contradicting": [],
            "reason": "weak_or_ambiguous_match",
        }

    def _conflicts(ev):
        ev_numbers = _numbers(ev["text"])
        ev_negated = _has_negation(ev["text"])
        numeric_conflict = (
            bool(claim_numbers) and bool(ev_numbers)
            and not (claim_numbers & ev_numbers)
        )
        negation_conflict = claim_negated != ev_negated
        entity_conflict = _entity_swap_conflict(claim["text"], ev["text"])
        return numeric_conflict or negation_conflict or entity_conflict

    supporting = [e for e in relevant if not _conflicts(e)]
    contradicting = [e for e in relevant if _conflicts(e)]

    # The verdict follows the single MOST RELEVANT piece of evidence (highest
    # lexical overlap with the claim) so a strong, on-topic match can't be
    # overruled by a loosely related passage that merely mentions a different
    # number. Other evidence is still surfaced for transparency.
    top = relevant[0]

    if _conflicts(top):
        raw_score = 0.85 * top["trust_score"]
        return {
            "verdict": "Contradicted", "raw_score": raw_score,
            "supporting": supporting, "contradicting": contradicting,
            "reason": "conflicting_evidence",
        }

    raw_score = min(0.98, 0.5 + top["overlap"] * top["trust_score"])
    return {
        "verdict": "Supported", "raw_score": raw_score,
        "supporting": supporting, "contradicting": contradicting,
        "reason": "matching_evidence",
    }
