"""
Live API test script for Python SDK v2.2.

Tests all SDK methods against the running API.
Set RAIL_API_KEY and optionally RAIL_BASE_URL environment variables.
"""

import os
import sys
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent))

from rail_score_sdk import (
    RailScoreClient,
    RailScoreError,
    AuthenticationError,
    ValidationError,
    ContentTooHarmfulError,
    SessionExpiredError,
)


def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_health_check(client):
    print_section("Testing Health Check")
    try:
        health = client.health()
        print(f"  Health Status: {health.status}")
        print(f"  Service: {health.service}")
        return True
    except Exception as e:
        print(f"  Health check failed: {e}")
        return False


def test_eval_basic(client):
    print_section("Testing Eval (Basic Mode)")
    try:
        result = client.eval(
            content=(
                "AI should prioritize human welfare, be transparent, "
                "and ensure fairness for all stakeholders."
            ),
            mode="basic",
        )

        print(f"  Score: {result.rail_score.score}/10")
        print(f"  Confidence: {result.rail_score.confidence}")
        print(f"  Summary: {result.rail_score.summary}")
        print(f"  Cached: {result.from_cache}")

        print("\n  Dimension Scores:")
        for dim, score in result.dimension_scores.items():
            print(f"    {dim}: {score.score}/10 (confidence: {score.confidence})")

        return True
    except Exception as e:
        print(f"  Eval basic failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_eval_deep(client):
    print_section("Testing Eval (Deep Mode)")
    try:
        result = client.eval(
            content=(
                "Women are generally worse at math than men. "
                "This is why STEM fields are dominated by males."
            ),
            mode="deep",
            include_suggestions=True,
        )

        print(f"  Score: {result.rail_score.score}/10")
        print(f"  Summary: {result.rail_score.summary}")

        for dim, score in result.dimension_scores.items():
            line = f"    {dim}: {score.score}/10"
            if score.explanation:
                line += f" — {score.explanation[:80]}..."
            print(line)

        if result.issues:
            print(f"\n  Issues ({len(result.issues)}):")
            for issue in result.issues[:5]:
                print(f"    [{issue.dimension}] {issue.description}")

        if result.improvement_suggestions:
            print(f"\n  Suggestions:")
            for s in result.improvement_suggestions[:3]:
                print(f"    - {s[:80]}...")

        return True
    except Exception as e:
        print(f"  Eval deep failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_eval_dimensions(client):
    print_section("Testing Eval (Specific Dimensions)")
    try:
        result = client.eval(
            content="Take 500mg of ibuprofen every 4 hours for pain relief.",
            mode="deep",
            dimensions=["safety", "reliability"],
            domain="healthcare",
        )

        print(f"  Score: {result.rail_score.score}/10")
        print(f"  Dimensions returned: {list(result.dimension_scores.keys())}")
        return True
    except Exception as e:
        print(f"  Eval dimensions failed: {e}")
        return False


def test_eval_weights(client):
    print_section("Testing Eval (Custom Weights)")
    try:
        result = client.eval(
            content="AI systems must prioritize fairness and safety above all.",
            weights={
                "fairness": 25, "safety": 25, "reliability": 15,
                "transparency": 10, "privacy": 10, "accountability": 5,
                "inclusivity": 5, "user_impact": 5,
            },
        )

        print(f"  Score: {result.rail_score.score}/10")
        return True
    except Exception as e:
        print(f"  Eval weights failed: {e}")
        return False


def test_safe_regenerate(client):
    print_section("Testing Safe-Regenerate (RAIL_Safe_LLM)")
    try:
        result = client.safe_regenerate(
            content=(
                "Our AI system collects user data. We use it for stuff. "
                "It's fast and works well."
            ),
            mode="basic",
            max_regenerations=1,
            regeneration_model="RAIL_Safe_LLM",
            thresholds={"overall": {"score": 8.0, "confidence": 0.5}},
        )

        print(f"  Status: {result.status}")
        print(f"  Credits consumed: {result.credits_consumed}")
        if result.best_content:
            print(f"  Best content: {result.best_content[:100]}...")
        if result.best_scores:
            rail = result.best_scores.get("rail_score", {})
            print(f"  Best score: {rail.get('score', 'N/A')}/10")
        return True
    except ContentTooHarmfulError as e:
        print(f"  Content flagged as critical: {e.message}")
        return True  # Expected for harmful content
    except Exception as e:
        print(f"  Safe-regenerate failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_safe_regenerate_external(client):
    print_section("Testing Safe-Regenerate (External Mode)")
    try:
        result = client.safe_regenerate(
            content="Our AI system collects user data. We use it for stuff.",
            mode="basic",
            max_regenerations=1,
            regeneration_model="external",
        )

        print(f"  Status: {result.status}")
        if result.session_id:
            print(f"  Session ID: {result.session_id}")
        if result.iterations_remaining is not None:
            print(f"  Iterations remaining: {result.iterations_remaining}")
        if result.rail_prompt:
            print(f"  Rail prompt system: {result.rail_prompt.system_prompt[:80]}...")
        return True
    except Exception as e:
        print(f"  Safe-regenerate external failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_compliance_single(client):
    print_section("Testing Compliance (Single Framework)")
    try:
        result = client.compliance_check(
            content=(
                "We collect user browsing history and purchase data "
                "for personalized recommendations without explicit consent."
            ),
            framework="gdpr",
            context={
                "domain": "e-commerce",
            },
        )

        cs = result.compliance_score
        print(f"  Score: {cs.score}/10 ({cs.label})")
        print(f"  Passed: {result.requirements_passed}/{result.requirements_checked}")
        print(f"  Issues: {len(result.issues)}")
        return True
    except Exception as e:
        print(f"  Compliance single failed: {e}")
        return False


def test_compliance_multi(client):
    print_section("Testing Compliance (Multi-Framework)")
    try:
        result = client.compliance_check(
            content=(
                "We use cookies to track user behavior and sell profiles "
                "to advertisers. Users can opt out via a footer link."
            ),
            frameworks=["gdpr", "ccpa"],
        )

        s = result.cross_framework_summary
        print(f"  Frameworks: {s.frameworks_evaluated}")
        print(f"  Average: {s.average_score}/10")
        print(f"  Weakest: {s.weakest_framework} ({s.weakest_score}/10)")
        return True
    except Exception as e:
        print(f"  Compliance multi failed: {e}")
        return False


def test_error_handling(client):
    print_section("Testing Error Handling")

    # Test validation error (content too short)
    try:
        client.eval(content="Short")
        print("  Should have raised ValidationError")
        return False
    except ValidationError as e:
        print(f"  ValidationError caught: {e.message}")
    except Exception as e:
        print(f"  Unexpected error: {type(e).__name__}: {e}")

    return True


def main():
    print("=" * 70)
    print("  RAIL Score Python SDK v2.2 — Live API Test Suite")
    print("=" * 70)

    api_key = os.getenv("RAIL_API_KEY", "test-api-key")
    base_url = os.getenv("RAIL_BASE_URL", "https://api.responsibleailabs.ai")

    print(f"\n  API Key: {api_key[:8]}...")
    print(f"  Base URL: {base_url}")

    client = RailScoreClient(api_key=api_key, base_url=base_url, timeout=120)
    print(f"  Client initialized")

    tests = [
        ("health", test_health_check),

        ("eval_basic", test_eval_basic),
        ("eval_deep", test_eval_deep),
        ("eval_dimensions", test_eval_dimensions),
        ("eval_weights", test_eval_weights),

        ("safe_regenerate", test_safe_regenerate),
        ("safe_regenerate_external", test_safe_regenerate_external),

        ("compliance_single", test_compliance_single),
        ("compliance_multi", test_compliance_multi),

        ("error_handling", test_error_handling),
    ]

    results = {}
    for name, fn in tests:
        results[name] = fn(client)

    # Summary
    print_section("Test Summary")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {status}  {name}")

    print(f"\n  Total: {total} | Passed: {passed} | Failed: {failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n  Interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n  Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
