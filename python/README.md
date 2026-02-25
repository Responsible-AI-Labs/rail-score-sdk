# RAIL Score Python SDK

Official Python client library for the RAIL Score API — Evaluate AI-generated content across 8 dimensions of Responsible AI.

[![PyPI version](https://img.shields.io/pypi/v/rail-score-sdk.svg)](https://pypi.org/project/rail-score-sdk/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Evaluation** — Score content across 8 RAIL dimensions in basic (fast) or deep (detailed) mode
- **Protected Content** — Evaluate against a quality threshold and regenerate improved content
- **Compliance** — Check against GDPR, CCPA, HIPAA, EU AI Act, India DPDP, India AI Governance
- **Explanations** — Generate human-readable explanations for scores
- **Type-Safe** — Full type hints and typed response models
- **Error Handling** — Granular exception hierarchy for every error scenario

## Installation

```bash
pip install rail-score-sdk
```

For development:
```bash
pip install rail-score-sdk[dev]
```

## Quick Start

```python
from rail_score_sdk import RailScoreClient

client = RailScoreClient(api_key="your-api-key")

# Evaluate content
result = client.eval(
    content="AI should prioritize human welfare and be transparent.",
    mode="basic",
)

print(f"RAIL Score: {result.rail_score.score}/10")
print(f"Summary: {result.rail_score.summary}")

for dim, score in result.dimension_scores.items():
    print(f"  {dim}: {score.score}/10")
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

### Protected Content

Evaluate content against a quality threshold and optionally regenerate:

```python
# Step 1: Evaluate against threshold
eval_result = client.protected_evaluate(
    content="Content to check",
    threshold=7.0,
    mode="basic",
)

if eval_result.improvement_needed:
    print(eval_result.improvement_prompt)

    # Step 2: Regenerate improved content
    regen_result = client.protected_regenerate(
        content="Content to improve",
        issues_to_fix={
            "fairness": {
                "score": 2.0,
                "explanation": "Age-based stereotyping.",
                "issues": ["Age-based stereotyping"],
            }
        },
    )
    print(regen_result.improved_content)
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

## License

MIT License — see [LICENSE](LICENSE) for details.

## Links

- **Documentation**: https://responsibleailabs.ai/developer/docs
- **API Reference**: https://responsibleailabs.ai/developers/api-ref
- **PyPI**: https://pypi.org/project/rail-score-sdk/
- **GitHub**: https://github.com/RAILethicsHub/rail-score
- **Issues**: https://github.com/RAILethicsHub/rail-score/issues
- **Support**: research@responsibleailabs.ai
