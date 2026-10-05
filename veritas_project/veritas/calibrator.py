"""
Confidence Calibration
----------------------
Maps a raw verifier score into a "calibrated" confidence value that
should be closer to empirical accuracy than the raw score alone.

In production this is fit offline with temperature scaling / conformal
prediction against a held-out set of human-labeled verification outcomes,
and refreshed continuously from the feedback loop (see
pipeline.VeritasPipeline / the paper's Section V, Step 5). This
prototype uses a simple, documented piecewise adjustment so the effect
of calibration is visible without requiring a labeled training set.
"""


def calibrate(raw_score, num_supporting, num_contradicting):
    score = raw_score

    # More independent agreeing sources -> nudge confidence up.
    if num_supporting >= 2:
        score = min(0.99, score + 0.05)
    if num_contradicting >= 2:
        score = min(0.99, score + 0.03)

    # Single-source verdicts are inherently less certain.
    if num_supporting == 1 and num_contradicting == 0:
        score = max(0.05, score - 0.05)

    return round(max(0.05, min(0.99, score)), 2)
