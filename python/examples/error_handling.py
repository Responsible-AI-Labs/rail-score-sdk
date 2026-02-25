"""
Error handling example for RAIL Score Python SDK v2.

Demonstrates how to properly handle the different types of errors
that may occur when using the RAIL Score API.
"""

import time
from rail_score_sdk import (
    RailScoreClient,
    RailScoreError,
    AuthenticationError,
    InsufficientCreditsError,
    InsufficientTierError,
    ValidationError,
    ContentTooHarmfulError,
    RateLimitError,
    EvaluationFailedError,
    ServiceUnavailableError,
)

# Initialize the client
client = RailScoreClient(api_key="your-api-key-here")

print("=" * 70)
print("RAIL Score SDK — Error Handling Examples")
print("=" * 70)


# --- Example 1: Authentication Error ---
print("\nExample 1: Handling Authentication Errors")
print("-" * 70)

try:
    bad_client = RailScoreClient(api_key="invalid_key_12345")
    bad_client.eval(content="Test content for evaluation purposes.")
except AuthenticationError as e:
    print(f"  Authentication failed: {e.message}")
    print(f"  Status code: {e.status_code}")
    print("  Fix: Check your API key at https://responsibleailabs.ai/dashboard")


# --- Example 2: Validation Error ---
print("\n\nExample 2: Handling Validation Errors")
print("-" * 70)

try:
    # Content too short (min 10 chars)
    client.eval(content="Short")
except ValidationError as e:
    print(f"  Validation error: {e.message}")

try:
    # Invalid mode
    client.eval(content="This is a valid length content.", mode="invalid_mode")
except ValidationError as e:
    print(f"  Validation error: {e.message}")


# --- Example 3: Insufficient Credits ---
print("\n\nExample 3: Handling Insufficient Credits")
print("-" * 70)

try:
    client.eval(
        content="Some content to evaluate for responsible AI scoring.",
        mode="deep",
    )
except InsufficientCreditsError as e:
    print(f"  Insufficient credits: {e.message}")
    if e.balance is not None:
        print(f"  Current balance: {e.balance}")
        print(f"  Required: {e.required}")
    print("  Fix: Top up at https://responsibleailabs.ai/dashboard")


# --- Example 4: Tier Insufficient ---
print("\n\nExample 4: Handling Tier Restrictions")
print("-" * 70)

try:
    client.compliance_check(
        content="Content for compliance evaluation.",
        framework="eu_ai_act",
    )
except InsufficientTierError as e:
    print(f"  Tier insufficient: {e.message}")
    print("  Fix: Upgrade your plan for access to this framework.")


# --- Example 5: Content Too Harmful ---
print("\n\nExample 5: Handling Content Too Harmful")
print("-" * 70)

try:
    client.protected_regenerate(
        content="Some severely problematic content here for testing.",
        issues_to_fix={
            "safety": {"score": 1.0, "explanation": "Harmful content", "issues": []},
            "fairness": {"score": 1.0, "explanation": "Discriminatory", "issues": []},
        },
    )
except ContentTooHarmfulError as e:
    print(f"  Content too harmful to regenerate: {e.message}")
    print("  The API refuses to regenerate content with avg score < 3.0.")


# --- Example 6: Rate Limiting with Retry ---
print("\n\nExample 6: Handling Rate Limits")
print("-" * 70)


def eval_with_retry(content: str, max_retries: int = 3) -> None:
    for attempt in range(max_retries):
        try:
            result = client.eval(content=content, mode="basic")
            print(f"  Score: {result.rail_score.score}/10")
            return
        except RateLimitError as e:
            wait = 2 ** attempt
            print(f"  Rate limited (attempt {attempt + 1}). Waiting {wait}s...")
            time.sleep(wait)
        except EvaluationFailedError as e:
            # Server error — safe to retry
            wait = 2 ** attempt
            print(f"  Server error (attempt {attempt + 1}). Retrying in {wait}s...")
            time.sleep(wait)
    print("  Max retries reached.")


eval_with_retry("AI should be fair and transparent in all its decisions.")


# --- Example 7: Generic Error Handling ---
print("\n\nExample 7: Generic Error Handling Pattern")
print("-" * 70)


def safe_eval(content: str) -> None:
    try:
        result = client.eval(content=content, mode="basic")
        print(f"  Score: {result.rail_score.score}/10 — {result.rail_score.summary}")
    except AuthenticationError:
        print("  Error: Invalid credentials. Check your API key.")
    except InsufficientCreditsError as e:
        print(f"  Error: Out of credits. Balance: {e.balance}")
    except ValidationError as e:
        print(f"  Error: Bad request — {e.message}")
    except RateLimitError:
        print("  Error: Rate limited. Try again later.")
    except ServiceUnavailableError:
        print("  Error: Service temporarily unavailable.")
    except RailScoreError as e:
        print(f"  Error ({e.status_code}): {e.message}")


safe_eval("Responsible AI requires transparency and accountability.")

print("\n" + "=" * 70)
print("Error Handling Examples Complete!")
print("=" * 70)
