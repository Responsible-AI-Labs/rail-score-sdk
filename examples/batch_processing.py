"""
Batch processing example for RAIL Score Python SDK v2.

Demonstrates processing multiple pieces of content with error handling
and progress tracking.
"""

import time
from typing import List, Dict, Any
from rail_score_sdk import (
    RailScoreClient,
    RailScoreError,
    RateLimitError,
    EvalResult,
)

# Initialize the client
client = RailScoreClient(api_key="your-api-key-here")

# Sample content for batch processing
content_samples = [
    {
        "id": "article_1",
        "domain": "healthcare",
        "content": (
            "AI is transforming healthcare by enabling early disease "
            "detection and personalized treatment plans."
        ),
    },
    {
        "id": "article_2",
        "domain": "finance",
        "content": (
            "Machine learning algorithms can detect fraudulent "
            "transactions with high accuracy while protecting "
            "customer privacy."
        ),
    },
    {
        "id": "article_3",
        "domain": "legal",
        "content": (
            "Legal AI systems must be transparent and explainable "
            "to ensure fair and unbiased judicial recommendations."
        ),
    },
    {
        "id": "article_4",
        "domain": "general",
        "content": (
            "AI-powered hiring tools should be regularly audited "
            "for bias to ensure equal opportunity for all candidates."
        ),
    },
    {
        "id": "article_5",
        "domain": "general",
        "content": (
            "Responsible journalism requires fact-checking and "
            "source verification, especially when covering "
            "AI-generated content."
        ),
    },
]


def batch_eval(
    items: List[Dict[str, Any]],
    mode: str = "basic",
    retry_limit: int = 3,
) -> List[Dict[str, Any]]:
    """Evaluate a batch of content items with retry logic."""
    results = []
    total = len(items)

    for i, item in enumerate(items, 1):
        print(f"  [{i}/{total}] Evaluating {item['id']}...", end=" ")

        for attempt in range(retry_limit):
            try:
                result = client.eval(
                    content=item["content"],
                    domain=item.get("domain", "general"),
                    mode=mode,
                )
                results.append(
                    {
                        "id": item["id"],
                        "score": result.rail_score.score,
                        "summary": result.rail_score.summary,
                        "dimensions": {
                            dim: s.score
                            for dim, s in result.dimension_scores.items()
                        },
                        "status": "success",
                    }
                )
                print(f"{result.rail_score.score}/10")
                break
            except RateLimitError:
                wait = 2 ** attempt
                print(f"rate limited, retrying in {wait}s...", end=" ")
                time.sleep(wait)
            except RailScoreError as e:
                results.append(
                    {
                        "id": item["id"],
                        "score": None,
                        "summary": None,
                        "dimensions": {},
                        "status": f"error: {e.message}",
                    }
                )
                print(f"error: {e.message}")
                break

    return results


print("=" * 70)
print("RAIL Score SDK — Batch Processing")
print("=" * 70)

# --- Basic mode batch ---
print("\nProcessing batch in basic mode:")
basic_results = batch_eval(content_samples, mode="basic")

# --- Summary statistics ---
scores = [r["score"] for r in basic_results if r["score"] is not None]
if scores:
    avg = sum(scores) / len(scores)
    print(f"\nBatch Summary:")
    print(f"  Total: {len(basic_results)}")
    print(f"  Succeeded: {len(scores)}")
    print(f"  Average score: {avg:.1f}/10")
    print(f"  Min: {min(scores)}/10 | Max: {max(scores)}/10")

# --- Per-dimension averages ---
print(f"\n  Per-Dimension Averages:")
dim_totals: Dict[str, List[float]] = {}
for r in basic_results:
    for dim, score in r["dimensions"].items():
        dim_totals.setdefault(dim, []).append(score)

for dim, vals in sorted(dim_totals.items()):
    print(f"    {dim}: {sum(vals) / len(vals):.1f}/10")

# --- Flag low scorers ---
print(f"\n  Items needing attention (score < 7.0):")
low = [r for r in basic_results if r["score"] is not None and r["score"] < 7.0]
if low:
    for r in low:
        print(f"    {r['id']}: {r['score']}/10")
else:
    print("    None — all items scored 7.0 or above.")

print("\n" + "=" * 70)
print("Batch Processing Complete!")
print("=" * 70)
