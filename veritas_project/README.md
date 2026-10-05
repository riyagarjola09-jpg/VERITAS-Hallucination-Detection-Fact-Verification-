# VERITAS — Hallucination Detection & Fact Verification Prototype

A working, runnable prototype of a post-generation hallucination-detection
pipeline for LLM outputs: it decomposes a response into atomic factual
claims, retrieves independent evidence, cross-checks each claim, produces a
calibrated confidence score, and explains every claim that isn't fully
supported — all wrapped in a small web UI.

This is the reference implementation for the accompanying research paper
*"VERITAS: A Multi-Stage Claim Extraction, Retrieval, and Verification
Framework for Detecting and Explaining Hallucinations in Large Language
Models."*

## Why this exists

LLMs generate the most statistically probable next token, not the most
factually correct one. RAG helps ground generation but never checks whether
the final answer actually agrees with what it retrieved. VERITAS treats
verification as its own dedicated stage — like a spell-checker or a
compiler's static analyzer — that runs *after* generation and works with
**any** LLM's output, without needing access to model weights.

## Architecture

```
LLM response
     |
     v
[1] Claim Extraction        -> splits response into atomic, checkable claims
     |
     v
[2] Claim Prioritization     -> ranks claims by risk (numeric/date/entity first)
     |
     v
[3] Evidence Retrieval       -> TF-IDF search over a local knowledge base
     |                           (swap for hybrid keyword+vector search in prod)
     v
[4] Verification Engine      -> entailment / contradiction / unverifiable
     |                           (swap for a fine-tuned NLI model in prod)
     v
[5] Confidence Calibration   -> raw score -> calibrated confidence
     |
     v
[6] Explanation Generation   -> evidence-grounded justification for any
     |                           claim that isn't fully Supported
     v
Annotated response + trust score
```

## Project layout

```
veritas_project/
├── app.py                  Flask server (API + demo UI)
├── demo.py                 Standalone CLI demo (no server needed)
├── requirements.txt
├── data/
│   └── knowledge_base.json  Local demo evidence corpus (20 documents)
├── veritas/
│   ├── claim_extractor.py   Stage 1-2
│   ├── retriever.py         Stage 3
│   ├── verifier.py          Stage 4
│   ├── calibrator.py        Stage 5
│   ├── explainer.py         Stage 6
│   └── pipeline.py          Wires all stages together
├── templates/index.html     Demo UI
└── static/{style.css,script.js}
```

## Running it

```bash
pip install -r requirements.txt

# Option A: command-line demo (fastest way to see it work)
python demo.py

# Option B: full web app
python app.py
# then open http://127.0.0.1:5000
```

Paste any AI-generated text into the left panel and click **Run
Verification**. Each claim comes back with a verdict (Supported /
Contradicted / Unverifiable), a calibrated confidence bar, and — for
anything that isn't fully supported — a short explanation citing the
conflicting or missing evidence.

## What's "real" vs. what's a stand-in

Everything here is a genuinely working, end-to-end pipeline — nothing is
mocked or hard-coded per example. That said, to keep the prototype
dependency-free and runnable offline with zero API keys, a few stages use
lightweight statistical/heuristic methods in place of the large learned
models a production system would use. Each module's docstring says exactly
what it stands in for. Swapping any one of them out does not require
touching the rest of the pipeline, because each stage has a small, stable
interface (claims in, claims + verdicts out):

| Stage | Prototype implementation | Production upgrade path |
|---|---|---|
| Claim extraction | Regex sentence splitter + rule-based classifier | Fine-tuned LLM prompted to output atomic propositions, + a coreference resolver |
| Evidence retrieval | TF-IDF + cosine similarity over a 20-document local JSON corpus | Hybrid keyword + dense-vector search (FAISS/Milvus) over curated knowledge bases, domain corpora, and live web search |
| Verification | Lexical-overlap + numeric/negation/entity-swap conflict heuristics | Transformer NLI model fine-tuned on fact-verification data (FEVER-style), wrapped with multi-hop decomposition |
| Calibration | Documented piecewise score adjustment | Temperature scaling / conformal prediction fit on held-out human-labeled verification outcomes, refreshed from the feedback loop |
| Explanation | Template-based snippet citation | Small LLM prompted specifically to summarize the discrepancy between claim and evidence |

## Extending this project

- **Bigger knowledge base:** replace `data/knowledge_base.json` with a real
  corpus (Wikipedia dump, internal docs, domain-specific sources) — the
  retriever code doesn't need to change.
- **Domain packs:** ship separate knowledge bases per domain (medical,
  legal, financial) and route claims to the right one based on `claim_type`
  / detected domain.
- **Live web evidence:** add a web-search call inside
  `EvidenceRetriever.retrieve()` alongside the local TF-IDF lookup.
- **Real NLI model:** replace the body of `verify_claim()` in
  `verifier.py` with a call to a fine-tuned entailment model; keep the same
  return shape (`verdict`, `raw_score`, `supporting`, `contradicting`).
- **Feedback loop:** log human corrections (a reviewer marking a flagged
  claim as actually correct) and use them to refit calibration and adjust
  per-source trust weights over time.

## Notes on scope

This prototype ships with a small, illustrative knowledge base so the demo
is self-contained and reproducible offline. It is meant to show the
architecture and prove the pipeline works end-to-end — not as a
production-scale fact database. See the paper's Limitations section for a
fuller discussion of privacy, bias, and reliability considerations before
deploying anything like this on real user traffic.
