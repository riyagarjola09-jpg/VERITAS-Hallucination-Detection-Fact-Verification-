"""
Explanation Generation
----------------------
Produces a short, evidence-grounded justification for any claim that is
not fully Supported, so a human reviewer does not have to re-research
the topic from scratch.
"""


def explain(claim, result):
    verdict = result["verdict"]

    if verdict == "Supported":
        return None

    if verdict == "Contradicted":
        ev = result["contradicting"][0]
        snippet = ev["text"][:170].rstrip()
        return (
            f"Evidence from \u201c{ev['title']}\u201d appears to conflict with this "
            f"claim: \u201c{snippet}{'...' if len(ev['text']) > 170 else ''}\u201d"
        )

    return (
        "No sufficiently relevant evidence was found in the connected knowledge "
        "base to confirm or refute this claim. Treat it as unverified rather "
        "than assume it is correct."
    )
