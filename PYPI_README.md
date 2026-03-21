# RAIL Score Python SDK

Official Python client library for the [RAIL Score API](https://responsibleailabs.ai/developer/api-reference) — evaluate AI-generated content across **8 dimensions of Responsible AI**: fairness, safety, reliability, transparency, privacy, accountability, inclusivity, and user impact.

[![PyPI version](https://img.shields.io/pypi/v/rail-score-sdk.svg)](https://pypi.org/project/rail-score-sdk/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Features

- **Sync & Async Clients** — `RailScoreClient` (requests-based) and `AsyncRAILClient` (httpx-based, with built-in caching)
- **Evaluation** — Score content in `basic` (fast) or `deep` (detailed, with explanations, issues, suggestions) mode
- **Safe Regeneration** — Automatically iterate until content meets your quality threshold, server-side or with your own LLM
- **Compliance Checking** — Evaluate against GDPR, CCPA, HIPAA, EU AI Act, India DPDP, India AI Governance
- **Policy Engine** — `log_only`, `block`, `regenerate`, or `custom` callback when scores fall below threshold
- **Multi-Turn Sessions** — Conversation-aware evaluation with per-turn history and adaptive quality gating
- **Middleware** — Wrap any async LLM function with transparent RAIL evaluation and policy enforcement
- **LLM Provider Wrappers** — Drop-in wrappers for OpenAI, Anthropic, and Google Gemini
- **OpenTelemetry Observability** — Vendor-neutral tracing, metrics, and structured logs with per-project scoping
- **Compliance Incident Handling** — Tracked incidents and per-dimension human review queues
- **Observability Integrations** — Langfuse v3 and LiteLLM guardrail support
- **Type-Safe** — Full type hints and typed response models throughout

---

## Installation

```bash
pip install rail-score-sdk
```

**With optional extras:**

```bash
pip install "rail-score-sdk[openai]"        # OpenAI wrapper
pip install "rail-score-sdk[anthropic]"     # Anthropic wrapper
pip install "rail-score-sdk[google]"        # Google Gemini wrapper
pip install "rail-score-sdk[telemetry]"     # OpenTelemetry observability
pip install "rail-score-sdk[langfuse]"      # Langfuse v3 integration
pip install "rail-score-sdk[litellm]"       # LiteLLM guardrail
pip install "rail-score-sdk[integrations]"  # All of the above
```

---

## Quick Start

```python
from rail_score_sdk import RailScoreClient

client = RailScoreClient(api_key="your-api-key")

result = client.eval(
    content="AI should prioritize human welfare and be transparent.",
    mode="basic",
)

print(f"RAIL Score: {result.rail_score.score}/10")
print(f"Summary:    {result.rail_score.summary}")

for dim, ds in result.dimension_scores.items():
    print(f"  {dim}: {ds.score}/10")
```

**Async client:**

```python
import asyncio
from rail_score_sdk import AsyncRAILClient

async def main():
    async with AsyncRAILClient(api_key="your-api-key") as client:
        result = await client.eval("Your content here", mode="basic")
        print(f"Score: {result['rail_score']['score']}/10")

asyncio.run(main())
```

---

## Evaluation

Score content across all 8 RAIL dimensions.

```python
# Deep mode — per-dimension explanations, issues, suggestions
result = client.eval(
    content="Your content here",
    mode="deep",
    domain="healthcare",             # general · healthcare · finance · legal · education · code
    include_explanations=True,
    include_issues=True,
    include_suggestions=True,
)

for dim, ds in result.dimension_scores.items():
    print(f"  {dim}: {ds.score}/10 — {ds.explanation}")

# Custom dimension weights (must sum to 100)
result = client.eval(
    content="Your content here",
    weights={
        "safety": 30, "reliability": 20, "privacy": 15,
        "fairness": 10, "transparency": 10, "accountability": 5,
        "inclusivity": 5, "user_impact": 5,
    },
)
```

---

## Safe Regeneration

Evaluate and iteratively improve content until it meets your threshold.

```python
# Server-side (RAIL_Safe_LLM handles the loop)
result = client.safe_regenerate(
    content="Content to improve",
    regeneration_model="RAIL_Safe_LLM",
    max_regenerations=3,
    thresholds={"overall": {"score": 7.0}},
)
print(result.best_content)

# External mode (regenerate with your own LLM)
result = client.safe_regenerate(content="...", regeneration_model="external")
if result.status == "awaiting_regeneration":
    improved = my_llm(result.rail_prompt.system_prompt, result.rail_prompt.user_prompt)
    result = client.safe_regenerate_continue(
        session_id=result.session_id, regenerated_content=improved
    )
```

---

## Compliance Checking

**Supported frameworks:** `gdpr` · `ccpa` · `hipaa` · `eu_ai_act` · `india_dpdp` · `india_ai_gov`

```python
# Single framework
result = client.compliance_check(
    content="Our AI processes user health records...",
    framework="gdpr",
    context={"domain": "healthcare", "data_types": ["health_records"]},
)
print(f"Score: {result.compliance_score.score}/10  ({result.compliance_score.label})")
print(f"Passed: {result.requirements_passed}/{result.requirements_checked}")

# Multi-framework (up to 5 at once)
result = client.compliance_check(content="...", frameworks=["gdpr", "ccpa", "hipaa"])
print(f"Average: {result.cross_framework_summary.average_score}/10")
```

---

## Policy Engine

Control what happens when a response scores below your threshold.

```python
from rail_score_sdk import AsyncRAILClient, PolicyEngine, Policy, RAILBlockedError

async with AsyncRAILClient(api_key="your-api-key") as client:
    eval_response = await client.eval(content="Some content", mode="basic")

    # BLOCK — raises RAILBlockedError if score < threshold
    engine = PolicyEngine(policy=Policy.BLOCK, threshold=7.0)
    try:
        result = await engine.enforce("Some content", eval_response, client)
    except RAILBlockedError as e:
        print(f"Blocked — score={e.score}, threshold={e.threshold}")

    # REGENERATE — auto-improves content
    engine = PolicyEngine(policy=Policy.REGENERATE, threshold=7.0)
    result = await engine.enforce("Some content", eval_response, client)
    if result.was_regenerated:
        print(f"Improved: {result.content}")
```

---

## LLM Provider Wrappers

Drop-in wrappers that automatically evaluate every LLM response via RAIL Score.

```python
from rail_score_sdk.integrations import RAILOpenAI, RAILAnthropic, RAILGemini

# OpenAI
client = RAILOpenAI(
    openai_api_key="sk-...",
    rail_api_key="your-rail-api-key",
    rail_threshold=7.0,
    rail_policy="regenerate",
)
response = await client.chat_completion(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Explain quantum computing."}],
)
print(f"Score: {response.rail_score}/10  Regenerated: {response.was_regenerated}")

# Anthropic
client = RAILAnthropic(anthropic_api_key="sk-ant-...", rail_api_key="...", rail_threshold=7.0)
response = await client.message(model="claude-sonnet-4-5-20250929", max_tokens=1024, messages=[...])

# Google Gemini
client = RAILGemini(gemini_api_key="AIza...", rail_api_key="...", rail_threshold=7.0)
response = await client.generate(model="gemini-2.5-flash", contents="...")
```

---

## OpenTelemetry Observability

```bash
pip install "rail-score-sdk[telemetry]"
```

Every API call is automatically traced, metered, and logged once you pass a `RAILTelemetry` instance to the client.

```python
from rail_score_sdk import RailScoreClient
from rail_score_sdk.telemetry import RAILTelemetry, ComplianceLogger, IncidentLogger, HumanReviewQueue

# Configure telemetry (console for dev, OTLP for production)
telemetry = RAILTelemetry(
    org_id="acme-corp",
    project_id="customer-chatbot",
    environment="production",
    exporter="otlp",
    endpoint="localhost:4317",
)

# Every call auto-emits spans (rail.score, rail.project_id), metrics, and error logs
client = RailScoreClient(api_key="rail_xxx", telemetry=telemetry)

# Multiple projects — each instance is fully isolated
telemetry_b = RAILTelemetry(org_id="acme-corp", project_id="search-api", ...)
client_b = RailScoreClient(api_key="rail_xxx", telemetry=telemetry_b)
```

**Automatically emitted per request:**
- Span: `RAIL POST /railscore/v1/eval` with `rail.score`, `rail.confidence`, `rail.project_id`, `rail.org_id`
- Counters: `rail.requests`, `rail.errors`, `rail.credits.consumed`
- Histograms: `rail.request.duration`, `rail.score.distribution`

### ComplianceLogger

```python
comp_logger = ComplianceLogger(telemetry)
result = client.compliance_check(content="...", framework="gdpr")
comp_logger.log_compliance_result(result)    # INFO summary + WARNING/ERROR per issue
```

### IncidentLogger

```python
incident_logger = IncidentLogger(telemetry)

# Auto-raise from a compliance result
incident_id = incident_logger.log_compliance_incident(gdpr_result, threshold=6.0)

# Score-breach incident with unique ID for external ticketing
incident_id = incident_logger.log_score_breach(score=1.8, threshold=4.0)
```

### HumanReviewQueue

Flag any dimension scoring below a threshold (default 2.0) for human review. Items emit OTEL logs immediately and can be drained for forwarding to Jira, PagerDuty, Slack, etc.

```python
review_queue = HumanReviewQueue(telemetry, threshold=2.0)

# Check all 8 dimensions — enqueues anything below threshold
result = client.eval(content=text, mode="deep")
flagged = review_queue.check_and_enqueue(result, link_incident=True)

# Drain for external handling
for item in review_queue.drain():
    print(f"[{item.item_id}] {item.dimension}: {item.score:.1f}")
    my_ticketing_system.create(item)
```

---

## RAIL Dimensions

| Dimension | What it measures |
|-----------|-----------------|
| **Fairness** | Equitable treatment across groups — no bias or stereotyping |
| **Safety** | Prevention of harmful, toxic, or unsafe content |
| **Reliability** | Factual accuracy, consistency, calibrated uncertainty |
| **Transparency** | Clear reasoning, honest limitations, no deceptive framing |
| **Privacy** | Protection of personal data and data minimization |
| **Accountability** | Traceable reasoning, explicit assumptions, error signals |
| **Inclusivity** | Accessible, inclusive, culturally aware language |
| **User Impact** | Positive value at the right detail level and tone |

**Score labels:** Critical (0–2.9) · Poor (3–4.9) · Needs improvement (5–6.9) · Good (7–8.9) · Excellent (9–10)

> Scores below **2.0** on any single dimension are considered **concerning** and should be flagged for human review.

---

## Error Handling

```python
from rail_score_sdk.exceptions import (
    RailScoreError,           # base — all exceptions inherit from this
    AuthenticationError,      # 401
    InsufficientCreditsError, # 402 — e.balance, e.required
    ValidationError,          # 400
    ContentTooHarmfulError,   # 422
    RateLimitError,           # 429
    EvaluationFailedError,    # 500 — safe to retry
    ServiceUnavailableError,  # 503
    RAILBlockedError,         # policy=BLOCK triggered — e.score, e.threshold
)

try:
    result = client.eval(content="...")
except AuthenticationError:
    print("Check your API key")
except InsufficientCreditsError as e:
    print(f"Need {e.required} credits, have {e.balance}")
except RailScoreError as e:
    print(f"API error ({e.status_code}): {e.message}")
```

---

## Links

- **Documentation**: https://responsibleailabs.ai/developer/quickstart
- **API Reference**: https://responsibleailabs.ai/developer/api-reference
- **GitHub**: https://github.com/Responsible-AI-Labs/rail-score-sdk
- **Issues**: https://github.com/Responsible-AI-Labs/rail-score-sdk/issues
- **Support**: research@responsibleailabs.ai
