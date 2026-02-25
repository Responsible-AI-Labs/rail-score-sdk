# RAIL Score SDKs

Official client libraries for the [RAIL Score API](https://responsibleailabs.ai) — Evaluate AI-generated content across 8 dimensions of Responsible AI.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

RAIL Score evaluates AI-generated content across 8 dimensions:

1. **Fairness** — Equitable treatment, no bias or stereotyping
2. **Safety** — Prevention of harmful, toxic, or unsafe content
3. **Reliability** — Factual accuracy, consistency, appropriate calibration
4. **Transparency** — Clear communication of limitations and reasoning
5. **Privacy** — Protection of personal information, data minimization
6. **Accountability** — Traceable reasoning, stated assumptions, error signals
7. **Inclusivity** — Inclusive language, accessibility, cultural awareness
8. **User Impact** — Positive value at the right detail level and tone

---

## Available SDKs

### Python SDK

[![PyPI version](https://img.shields.io/pypi/v/rail-score-sdk.svg)](https://pypi.org/project/rail-score-sdk/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**Status:** v2.0.0

```bash
pip install rail-score-sdk
```

**Features:**
- Evaluation in basic (fast) and deep (detailed) modes
- Protected content — evaluate + regenerate improved content
- Compliance checking — GDPR, CCPA, HIPAA, EU AI Act, India DPDP, India AI Governance
- Custom dimension weights and dimension filtering
- Explanation generation for pre-computed scores
- Full type hints and typed response models
- Granular exception hierarchy

**Documentation:** [python/README.md](python/README.md)

**Quick Start:**
```python
from rail_score_sdk import RailScoreClient

client = RailScoreClient(api_key="your-api-key")
result = client.eval(
    content="AI should prioritize human welfare and be transparent.",
    mode="basic",
)
print(f"RAIL Score: {result.rail_score.score}/10 — {result.rail_score.summary}")
```

---

### JavaScript/TypeScript SDK

**Status:** Coming Soon

---

## Common Use Cases

### Content Quality Assurance
- Evaluate AI-generated content before publishing
- Score against specific dimensions (safety, reliability, etc.)
- Get actionable improvement suggestions

### Compliance & Governance
- Check content against GDPR, CCPA, HIPAA
- Evaluate EU AI Act compliance with risk classification
- Multi-framework evaluation in a single request

### Content Protection Pipeline
- Evaluate content against a quality threshold
- Get structured improvement prompts for failing content
- Regenerate improved content automatically

---

## Resources

- **Documentation**: https://responsibleailabs.ai/developer/docs
- **API Reference**: https://responsibleailabs.ai/developers/api-ref
- **Dashboard**: https://responsibleailabs.ai/dashboard
- **Discord**: https://responsibleailabs.ai/discord
- **Email**: research@responsibleailabs.ai
- **Issues**: https://github.com/RAILethicsHub/rail-score/issues

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](python/CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.
