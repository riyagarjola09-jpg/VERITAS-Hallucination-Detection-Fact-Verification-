"""
Quick CLI demo of the VERITAS hallucination-detection pipeline.
Run: python demo.py
"""

from veritas.pipeline import VeritasPipeline

SAMPLE_LLM_RESPONSE = """
The capital of Australia is Sydney, which is also its largest city.
Water boils at 100 degrees Celsius at standard atmospheric pressure.
The Great Wall of China can be seen from space with the naked eye, which is a well known fact.
Python was created by Guido van Rossum and first released in 1991.
The first iPhone was released by Apple in 2005.
Studies show that listening to jazz music increases IQ by 15 points permanently.
Mount Everest stands at 8,849 meters above sea level.
"""

VERDICT_ICON = {"Supported": "[OK]", "Contradicted": "[X]", "Unverifiable": "[?]"}


def main():
    pipeline = VeritasPipeline()
    report = pipeline.run(SAMPLE_LLM_RESPONSE)

    print("=" * 78)
    print("VERITAS VERIFICATION REPORT")
    print("=" * 78)
    for claim in report["claims"]:
        icon = VERDICT_ICON[claim["verdict"]]
        print(f"\n{icon} [{claim['verdict']:>13}]  confidence={claim['confidence']:.0%}  "
              f"type={claim['type']}")
        print(f"    Claim: {claim['text']}")
        if claim["explanation"]:
            print(f"    Why:   {claim['explanation']}")
        if claim["evidence"]:
            top = claim["evidence"][0]
            print(f"    Source: {top['title']} (similarity={top['similarity']})")

    print("\n" + "=" * 78)
    print(f"OVERALL RESPONSE TRUST SCORE: {report['overall_trust_score']:.0%}  "
          f"({report['claim_count']} claims checked)")
    print("=" * 78)


if __name__ == "__main__":
    main()
