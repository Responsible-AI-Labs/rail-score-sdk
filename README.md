# RAIL Score Python SDK

Official Python client library for the RAIL Score API — Evaluate AI-generated content across 8 dimensions of Responsible AI.

[![PyPI version](https://img.shields.io/pypi/v/rail-score-sdk.svg)](https://pypi.org/project/rail-score-sdk/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Sync & Async Clients** — Blocking `requests`-based and non-blocking `httpx`-based clients
- **Evaluation** — Score content across 8 RAIL dimensions in basic (fast) or deep (detailed) mode
- **Protected Content** — Evaluate against a quality threshold and regenerate improved content
- **Compliance** — Check against GDPR, CCPA, HIPAA, EU AI Act, India DPDP, India AI Governance
- **Policy Engine** — Configurable enforcement: `log_only`, `block`, `regenerate`, or `custom` callback
- **Multi-Turn Sessions** — Conversation-aware evaluation with adaptive quality gating
- **LLM Provider Wrappers** — Drop-in wrappers for OpenAI, Anthropic, and Google Gemini
- **Observability** — Langfuse v3 score integration and LiteLLM guardrail support
- **Type-Safe** — Full type hints and typed response models
- **Error Handling** — Granular exception hierarchy for every error scenario

## Installation

```bash
pip install rail-score-sdk
```

With optional LLM provider integrations:

```bash
# Individual providers
pip install "rail-score-sdk[openai]"
pip install "rail-score-sdk[anthropic]"
pip install "rail-score-sdk[google]"

# Observability
pip install "rail-score-sdk[langfuse]"
pip install "rail-score-sdk[litellm]"

# All integrations
pip install "rail-score-sdk[integrations]"
```

For development:
```bash
pip install "rail-score-sdk[dev]"
```

## Quick Start

### Sync Client

```python
from rail_score_sdk import RailScoreClient

client = RailScoreClient(api_key="your-api-key")

result = client.eval(
    content="AI should prioritize human welfare and be transparent.",
    mode="basic",
)

print(f"RAIL Score: {result.rail_score.score}/10")
print(f"Summary: {result.rail_score.summary}")

for dim, score in result.dimension_scores.items():
    print(f"  {dim}: {score.score}/10")
```

### Async Client

```python
import asyncio
from rail_score_sdk import AsyncRAILClient

async def main():
    async with AsyncRAILClient(api_key="your-api-key") as client:
        result = await client.eval(
            content="AI should prioritize human welfare and be transparent.",
            mode="basic",
        )
        print(f"RAIL Score: {result['rail_score']['score']}/10")

asyncio.run(main())
```

## API Reference

### Evaluate Content

Score content across all 8 RAIL dimensions. Supports **basic** (hybrid ML, fast) and **deep** (LLM-as-Judge, detailed) modes.

```python
# Basic mode — all dimensions
result = client.eval(
    content="Your content here",
    mode="basic",
    domain="general",       # general, healthcare, finance, legal, education, code
    usecase="general",      # general, chatbot, content_generation, summarization, translation, code_generation
)

# Deep mode — specific dimensions with explanations
result = client.eval(
    content="Your content here",
    mode="deep",
    dimensions=["safety", "reliability", "fairness"],
    include_explanations=True,
    include_issues=True,
    include_suggestions=True,
)

# Custom dimension weights (must sum to 100)
result = client.eval(
    content="Your content here",
    weights={
        "fairness": 10, "safety": 25, "reliability": 25,
        "transparency": 10, "privacy": 10, "accountability": 10,
        "inclusivity": 5, "user_impact": 5,
    },
)
```

### Safe Regenerate

Evaluate content and automatically regenerate until it meets your thresholds:

```python
# Server-side regeneration (RAIL_Safe_LLM mode)
result = client.safe_regenerate(
    content="Content to improve",
    mode="basic",
    max_regenerations=3,
    regeneration_model="RAIL_Safe_LLM",
    thresholds={"overall": {"score": 7.0}},
    domain="general",
)

print(result.best_content)
print(f"Final score: {result.final_score}")
print(f"Iterations: {result.iterations_used}")

# External mode (client-orchestrated loop)
result = client.safe_regenerate(
    content="Content to check",
    mode="basic",
    regeneration_model="external",
    thresholds={"overall": {"score": 7.0}},
)

if not result.thresholds_met and result.session_id:
    # Regenerate with your own model, then continue the session
    improved = my_llm_regenerate(result.best_content)
    result = client.safe_regenerate_continue(
        session_id=result.session_id,
        regenerated_content=improved,
    )
```

### Compliance Check

Evaluate against regulatory frameworks:

```python
# Single framework
result = client.compliance_check(
    content="Our AI processes user data...",
    framework="gdpr",
    context={
        "domain": "e-commerce",
        "data_types": ["browsing_history", "purchase_data"],
        "processing_purpose": "personalized_recommendations",
    },
)

print(f"Score: {result.compliance_score.score}/10 ({result.compliance_score.label})")
print(f"Passed: {result.requirements_passed}/{result.requirements_checked}")

# Multi-framework (up to 5)
result = client.compliance_check(
    content="...",
    frameworks=["gdpr", "ccpa"],
)
print(result.cross_framework_summary.average_score)

# Strict mode (8.5 threshold instead of 7.0)
result = client.compliance_check(content="...", framework="ccpa", strict_mode=True)
```

**Supported frameworks:** `gdpr`, `ccpa`, `hipaa`, `eu_ai_act`, `india_dpdp`, `india_ai_gov`

### Utility

```python
# Health check
health = client.health()
print(health.status)

# Version info
version = client.version()
print(f"{version.version} ({version.api_version})")
```

---

## Policy Engine

The `PolicyEngine` controls what happens when content scores below your threshold:

```python
import asyncio
from rail_score_sdk import AsyncRAILClient, PolicyEngine, Policy, RAILBlockedError

async def main():
    client = AsyncRAILClient(api_key="your-api-key")
    async with client:
        eval_response = await client.eval(content="Some content", mode="basic")

        # Log only (default) — always passes through
        engine = PolicyEngine(policy=Policy.LOG_ONLY, threshold=7.0)
        result = await engine.enforce("Some content", eval_response, client)
        print(f"Score: {result.score}, Passed: {result.threshold_met}")

        # Block — raises RAILBlockedError if below threshold
        engine = PolicyEngine(policy=Policy.BLOCK, threshold=7.0)
        try:
            result = await engine.enforce("Some content", eval_response, client)
        except RAILBlockedError as e:
            print(f"Blocked! Score: {e.score}, Threshold: {e.threshold}")

        # Regenerate — automatically calls /protected/regenerate
        engine = PolicyEngine(policy=Policy.REGENERATE, threshold=7.0)
        result = await engine.enforce("Some content", eval_response, client)
        if result.was_regenerated:
            print(f"Improved content: {result.content}")
            print(f"Original: {result.original_content}")

        # Custom — run your own async callback
        async def my_handler(content, eval_data, rail_client):
            # Your custom logic here (e.g., call a different LLM)
            return "My custom improved content"

        engine = PolicyEngine(
            policy=Policy.CUSTOM,
            threshold=7.0,
            custom_callback=my_handler,
        )
        result = await engine.enforce("Some content", eval_response, client)

asyncio.run(main())
```

---

## Multi-Turn Sessions

`RAILSession` tracks conversation history and applies RAIL evaluation to every turn with adaptive quality gating:

```python
import asyncio
from rail_score_sdk import RAILSession

async def main():
    async with RAILSession(
        api_key="your-api-key",
        threshold=7.0,
        policy="regenerate",      # auto-regenerate low-scoring responses
        mode="basic",
        domain="healthcare",
        deep_every_n=5,           # force deep eval every 5th turn
        context_window=3,         # include last 3 turns as context
    ) as session:

        # Evaluate each conversation turn
        result = await session.evaluate_turn(
            user_message="What medication should I take for a headache?",
            assistant_response="Take 500mg ibuprofen every 4-6 hours with food.",
        )
        print(f"Turn 1 — Score: {result.score}, Content: {result.content}")

        result = await session.evaluate_turn(
            user_message="What about if I have stomach issues?",
            assistant_response="Consider acetaminophen instead, and consult your doctor.",
        )
        print(f"Turn 2 — Score: {result.score}")

        # Pre-evaluate user input for safety (doesn't record a turn)
        input_check = await session.evaluate_input("How do I harm someone?")
        if not input_check.threshold_met:
            print(f"Unsafe input detected! Score: {input_check.score}")

        # Session-level metrics
        print(session.scores_summary())
        # {'total_turns': 2, 'average_score': 8.2, 'lowest_score': 7.8,
        #  'turns_below_threshold': 0, 'regenerations': 0}

asyncio.run(main())
```

---

## Middleware

`RAILMiddleware` wraps any async LLM generate function with RAIL evaluation and policy enforcement:

```python
import asyncio
from rail_score_sdk import RAILMiddleware

# Your LLM call — can be any provider
async def my_llm_generate(messages, **kwargs):
    # Call OpenAI, Anthropic, local model, etc.
    return "The LLM generated this response."

async def main():
    mw = RAILMiddleware(
        api_key="your-rail-api-key",
        generate_fn=my_llm_generate,
        threshold=7.0,
        policy="block",           # block low-scoring responses
        mode="basic",
        domain="general",
        eval_input=True,          # also safety-check the user's input
        input_threshold=5.0,      # separate threshold for input safety
    )

    result = await mw.run(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain quantum computing."},
        ]
    )

    print(f"Content: {result.content}")
    print(f"RAIL Score: {result.score}")
    print(f"Threshold met: {result.threshold_met}")

asyncio.run(main())
```

With pre/post hooks for logging:

```python
async def log_before(messages):
    print(f"Sending {len(messages)} messages to LLM...")
    return messages  # return modified messages or None to keep original

async def log_after(original_text, eval_result):
    print(f"Score: {eval_result.score}, Regenerated: {eval_result.was_regenerated}")

mw = RAILMiddleware(
    api_key="your-rail-api-key",
    generate_fn=my_llm_generate,
    threshold=7.0,
    pre_hook=log_before,
    post_hook=log_after,
)
```

---

## LLM Provider Wrappers

Drop-in wrappers that automatically evaluate every LLM response via RAIL Score.

### OpenAI

```bash
pip install "rail-score-sdk[openai]"
```

```python
import asyncio
from rail_score_sdk.integrations import RAILOpenAI

async def main():
    client = RAILOpenAI(
        openai_api_key="sk-...",
        rail_api_key="your-rail-api-key",
        rail_threshold=7.0,
        rail_policy="regenerate",  # auto-fix low-scoring responses
        rail_mode="basic",
    )

    response = await client.chat_completion(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Explain quantum computing."}],
        temperature=0.7,
    )

    print(f"Content: {response.content}")
    print(f"RAIL Score: {response.rail_score}/10")
    print(f"Confidence: {response.rail_confidence}")
    print(f"Threshold met: {response.threshold_met}")
    print(f"Was regenerated: {response.was_regenerated}")
    print(f"Model: {response.model}")
    print(f"Token usage: {response.usage}")

    # Access dimension scores
    for dim, data in response.rail_dimensions.items():
        score = data if isinstance(data, (int, float)) else data.get("score")
        print(f"  {dim}: {score}/10")

    # Skip RAIL evaluation for a specific call
    raw_response = await client.chat_completion(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello"}],
        rail_skip=True,
    )

asyncio.run(main())
```

### Anthropic

```bash
pip install "rail-score-sdk[anthropic]"
```

```python
import asyncio
from rail_score_sdk.integrations import RAILAnthropic

async def main():
    client = RAILAnthropic(
        anthropic_api_key="sk-ant-...",
        rail_api_key="your-rail-api-key",
        rail_threshold=7.0,
        rail_policy="block",
    )

    response = await client.message(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Explain quantum computing."}],
        system="You are a helpful physics tutor.",
    )

    print(f"Content: {response.content}")
    print(f"RAIL Score: {response.rail_score}/10")
    print(f"Threshold met: {response.threshold_met}")
    print(f"Token usage: {response.usage}")

asyncio.run(main())
```

### Google Gemini

```bash
pip install "rail-score-sdk[google]"
```

```python
import asyncio
from rail_score_sdk.integrations import RAILGemini

async def main():
    # Using Gemini API key
    client = RAILGemini(
        rail_api_key="your-rail-api-key",
        gemini_api_key="AIza...",
        rail_threshold=7.0,
        rail_policy="log_only",
    )

    response = await client.generate(
        model="gemini-2.5-flash",
        contents="Explain quantum computing in simple terms.",
    )

    print(f"Content: {response.content}")
    print(f"RAIL Score: {response.rail_score}/10")
    print(f"Threshold met: {response.threshold_met}")

    # Using Vertex AI
    vertex_client = RAILGemini(
        rail_api_key="your-rail-api-key",
        vertexai=True,
        project="my-gcp-project",
        location="us-central1",
        rail_threshold=7.0,
    )

asyncio.run(main())
```

---

## Observability Integrations

### Langfuse

Push RAIL scores as numeric scores into [Langfuse](https://langfuse.com) v3 traces:

```bash
pip install "rail-score-sdk[langfuse]"
```

```python
import asyncio
from rail_score_sdk.integrations import RAILLangfuse

async def main():
    rl = RAILLangfuse(
        rail_api_key="your-rail-api-key",
        langfuse_public_key="pk-lf-...",
        langfuse_secret_key="sk-lf-...",
        score_dimensions=True,     # push all 8 dimension scores
        score_prefix="rail_",      # scores named "rail_overall", "rail_fairness", etc.
    )

    # Evaluate content and push scores in one call
    result = await rl.evaluate_and_log(
        content="The LLM response to evaluate.",
        trace_id="trace-abc-123",
        observation_id="gen-xyz-456",   # optional
        mode="deep",
    )
    print(f"RAIL Score: {result.score}/10")

asyncio.run(main())
```

You can also log pre-computed results from a `RAILSession`:

```python
from rail_score_sdk import RAILSession
from rail_score_sdk.integrations import RAILLangfuse

rl = RAILLangfuse(rail_api_key="your-rail-api-key")

# After evaluating a turn in a session...
result = await session.evaluate_turn(
    user_message="...",
    assistant_response="...",
)

# Push the result to Langfuse
rl.log_eval_result(result, trace_id="trace-abc-123")
```

### LiteLLM Guardrail

Use RAIL Score as a [LiteLLM](https://litellm.ai) proxy guardrail:

```bash
pip install "rail-score-sdk[litellm]"
```

In your LiteLLM `config.yaml`:

```yaml
guardrails:
  - guardrail_name: "rail-score-guard"
    litellm_params:
      guardrail: rail_score_sdk.integrations.litellm_guardrail.RAILGuardrail
      mode: "post_call"
      api_key: os.environ/RAIL_API_KEY
      api_base: os.environ/RAIL_API_BASE
```

Or use it standalone:

```python
from rail_score_sdk.integrations import RAILGuardrail

guard = RAILGuardrail(
    api_key="your-rail-api-key",
    guardrail_name="rail-score",
    event_hook="post_call",       # "pre_call", "post_call", or "during_call"
    rail_threshold=7.0,
    rail_input_threshold=5.0,     # separate threshold for input safety (pre_call)
    rail_mode="basic",
)
```

---

## RAIL Dimensions

Content is evaluated across 8 dimensions on a 0–10 scale:

| Dimension | Description |
|-----------|-------------|
| **Fairness** | Equitable treatment across demographic groups. No bias or stereotyping. |
| **Safety** | Prevention of harmful, toxic, or unsafe content. |
| **Reliability** | Factual accuracy, internal consistency, appropriate calibration. |
| **Transparency** | Clear communication of limitations and reasoning process. |
| **Privacy** | Protection of personal information and data minimization. |
| **Accountability** | Traceable reasoning, stated assumptions, error signals. |
| **Inclusivity** | Inclusive language, accessibility, cultural awareness. |
| **User Impact** | Positive value delivered at the right detail level and tone. |

**Score labels:** Excellent (9–10), Good (7–8.9), Needs improvement (5–6.9), Poor (3–4.9), Critical (0–2.9)

## Authentication

```python
# API key or JWT token
client = RailScoreClient(api_key="rail_xxx...")

# Environment variable
import os
client = RailScoreClient(
    api_key=os.getenv("RAIL_API_KEY"),
    base_url=os.getenv("RAIL_BASE_URL", "https://api.responsibleailabs.ai"),
    timeout=int(os.getenv("RAIL_TIMEOUT", "30")),
)
```

## Error Handling

```python
from rail_score_sdk import (
    RailScoreError,
    AuthenticationError,
    InsufficientCreditsError,
    InsufficientTierError,
    ValidationError,
    ContentTooHarmfulError,
    RateLimitError,
    EvaluationFailedError,
    ServiceUnavailableError,
    RAILBlockedError,
)

try:
    result = client.eval(content="...")
except AuthenticationError:
    print("Check your API key")
except InsufficientCreditsError as e:
    print(f"Credits: {e.balance} available, {e.required} needed")
except InsufficientTierError:
    print("Upgrade your plan for this feature")
except ValidationError as e:
    print(f"Bad request: {e.message}")
except ContentTooHarmfulError:
    print("Content too harmful to regenerate (avg score < 3.0)")
except RateLimitError:
    print("Rate limited — try again later")
except EvaluationFailedError:
    print("Server error — safe to retry")
except ServiceUnavailableError:
    print("Service temporarily unavailable")
except RailScoreError as e:
    print(f"API error ({e.status_code}): {e.message}")

# For async/policy-based code
try:
    result = await engine.enforce(content, eval_response, client)
except RAILBlockedError as e:
    print(f"Content blocked — Score: {e.score}, Threshold: {e.threshold}")
```

## Examples

See the [examples](examples/) directory:

- **basic_usage.py** — Basic and deep evaluation
- **advanced_features.py** — Custom weights, dimension filtering, basic vs deep
- **compliance_check.py** — GDPR, CCPA, HIPAA, EU AI Act, multi-framework
- **regenerate_content.py** — Protected content evaluation and regeneration
- **error_handling.py** — Production error handling patterns
- **batch_processing.py** — Processing multiple items with retry

## Testing

```bash
pip install -r requirements-dev.txt

pytest
pytest --cov=rail_score_sdk --cov-report=html

black rail_score_sdk/
mypy rail_score_sdk/
```

## Migrating from `rail-score`

The `rail-score` package has been deprecated. To migrate:

```bash
pip uninstall rail-score
pip install rail-score-sdk
```

Update your imports:

```python
# Old (deprecated)
from rail_score import RailScore
client = RailScore(api_key="...")

# New
from rail_score_sdk import RailScoreClient
client = RailScoreClient(api_key="...")
```

## License

MIT License — see [LICENSE](LICENSE) for details.

## Links

- **Documentation**: https://responsibleailabs.ai/developer/quickstart
- **API Reference**: https://responsibleailabs.ai/developer/api-reference
- **PyPI**: https://pypi.org/project/rail-score-sdk/
- **GitHub**: https://github.com/Responsible-AI-Labs/rail-score-sdk
- **Issues**: https://github.com/Responsible-AI-Labs/rail-score-sdk/issues
- **Support**: research@responsibleailabs.ai
