# Changelog

All notable changes to the RAIL Score Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.6.0] - 2026-06-07

### Added
- New exception `DPDPHostedOnlyError`.

### Changed
- `create_session` now raises `ValueError` immediately when `purpose` is empty instead of failing server-side with HTTP 400.
- `dpdp_audit` raises `DPDPHostedOnlyError` instead of a raw 404/501 when the compliance audit endpoint is unavailable.

### Fixed
- Package metadata version and `__version__` are synchronized (previously 2.5.1 vs 2.5.0).

## [2.4.0] - 2026-03-23

### Added
- **Agent evaluation namespace** (`client.agent`) on both `RailScoreClient` and `AsyncRAILClient`
  - `evaluate_tool_call()` — pre-execution risk assessment with ALLOW / FLAG / BLOCK decision, proxy variable detection, and compliance violation reporting
  - `evaluate_tool_result()` — post-execution output scanning for PII, prompt injection, and RAIL risk
  - `check_injection()` — standalone prompt injection detection with attack type classification
  - `evaluate_plan()` — pre-flight evaluation of multi-step agent plans (up to 20 steps); returns per-step decisions and an ALLOW_ALL / PARTIAL_BLOCK / BLOCK_ALL overall verdict
- **Tool risk registry** (`client.agent.registry`): `list_tools()`, `register_tool()`, `delete_tool()` — manage custom tool risk profiles with proxy variable watchlists and per-tool compliance rules
- **`AgentSession`** — client-side session tracking across multiple tool calls; accumulates risk scores, detects cross-call patterns (repeated PII access, escalating risk, blocked retries, compliance accumulation, dimension degradation), and exposes `risk_summary()` and `close()`
- **`AgentPolicy` / `AgentPolicyEngine`** — enforce per-tool thresholds with BLOCK, SUGGEST_FIX, LOG_ONLY, or AUTO_FIX modes; raises `AgentBlockedError` on violation
- **`AgentMiddleware`** — `@guard(tool_name=...)` decorator for automatic pre-call (and optional post-call) evaluation of any tool function
- **Framework integrations** under `rail_score_sdk.agent.integrations`: `RAILCrewAICallback`, `RAILLangGraphGuard`, `RAILAutoGenHook`
- **New exceptions**: `AgentBlockedError`, `PlanBlockedError`, `SessionClosedError`
- **New response models**: `AgentDecision`, `ToolResultRisk`, `InjectionCheck`, `PlanEvaluation`, `PlanStepResult`, `AgentDimensionScore`, `AgentContextSignals`, `AgentPolicyResult`, `AgentComplianceViolation`, `PiiDetection`, `PiiEntity`, `InjectionDetection`, `SessionRiskSummary`, `SessionPattern`, `SessionEvent`, `ComplianceExposure`, `ToolRiskProfile`, `ToolRegistryList`, `RegistryDeleteResult`
- `examples/agent_evaluation.py` — runnable example covering all agent evaluation methods
- **`HumanReviewQueue`** — per-dimension flagging queue with threshold-based enqueue, OTEL log emission, and `drain()` for forwarding to external systems (Jira, PagerDuty, Slack)
- **`IncidentLogger`** — tracked compliance and score-breach incidents with unique IDs and OTEL log severity mapping
- **`ComplianceLogger`** — structured per-framework compliance logs (INFO summary, WARNING/ERROR per issue)
- Telemetry `review_queue.py` and updated `compliance_logger.py` with full OTEL instrumentation
- `[agents]` optional dependency group: `crewai>=0.30`, `langgraph>=0.1`, `pyautogen>=0.2`
- PyPI trusted publishing via OIDC (no API token needed); build provenance attestations on every release
- `examples/complete_guide.ipynb` and `examples/telemetry_observability.py`

### Changed
- `client._request()` and `async_client._request()` extended to support `extra_headers` and all HTTP methods with params
- `pyproject.toml` is now the single build configuration (replaces `setup.py`)
- CI import check updated to verify all v2.4.0 exports including `client.agent` namespace
- PyPI publish workflow updated with provenance attestation step and v2.4.0 install verification

### Removed
- `setup.py` — superseded by `pyproject.toml`
- `DEPLOYMENT.md` — superseded by the GitHub Actions trusted publishing workflow
- `test_sdk_quick.py` and `test_with_api.py` — superseded by the `tests/e2e/` suite

## [2.2.1] - 2026-03-07

### Added
- Jupyter notebook examples: `quickstart.ipynb`, `safe_regenerate.ipynb`, `compliance_check.ipynb`

### Fixed
- README: corrected `result.final_score` → `result.credits_consumed`, `result.iterations_used` → `result.best_iteration`, `result.thresholds_met` → status check
- Examples: removed unsupported `tradeoff_mode` and dimension-level thresholds from `regenerate_content.py`

## [2.2.0] - 2026-03-07

### Breaking Changes
- **`protected_evaluate()` removed**: Replaced by `safe_regenerate()` with `RAIL_Safe_LLM` or `external` modes
- **`protected_regenerate()` removed**: Use `safe_regenerate()` instead
- **`explain()` removed**: Endpoint no longer available in the API
- **`version()` removed**: Endpoint no longer available in the API
- **Response models removed**: `ProtectedEvalResult`, `ProtectedRegenerateResult`, `RegenerateMetadata`, `ExplainResult`, `VersionResponse`, `ModelInfoResponse`

### Added
- `safe_regenerate()` — Evaluate and regenerate content in a single call with configurable thresholds
  - `RAIL_Safe_LLM` mode: Server-side regeneration loop
  - `external` mode: Client-orchestrated regeneration with session management
- `safe_regenerate_continue()` — Continue an external-mode session with new regenerated content
- `SafeRegenerateResult` model with iteration history, threshold tracking, and credits breakdown
- `SessionExpiredError` exception for expired external-mode sessions (410 response)
- `CriticalContentEvaluation` model for content too harmful to regenerate (422 response)
- New response models: `IterationRecord`, `RailPrompt`, `SafeRegenerateMetadata`, `CreditsBreakdown`, `ThresholdDimensionResult`, `ThresholdsMet`
- End-to-end chatbot examples: OpenAI, Gemini wrapper, Langfuse 3 integration

### Changed
- PolicyEngine `regenerate` mode now uses `safe_regenerate()` internally
- Repository restructured: moved from `python/` subdirectory to root level
- Updated all GitHub URLs to `https://github.com/Responsible-AI-Labs/rail-score-sdk`

### Removed
- `protected_evaluate()` — Use `safe_regenerate()` instead
- `protected_regenerate()` — Use `safe_regenerate()` instead
- `explain()` — No replacement (endpoint removed from API)
- `version()` — No replacement (endpoint removed from API)
- Old response models: `ProtectedEvalResult`, `ProtectedRegenerateResult`, `RegenerateMetadata`, `ExplainResult`, `VersionResponse`, `ModelInfoResponse`

## [2.1.1] - 2026-02-25

### Fixed
- Updated README with comprehensive documentation for all v2.1.0 features
- Added usage examples for AsyncRAILClient, PolicyEngine, RAILSession, RAILMiddleware
- Added usage examples for all LLM provider wrappers (OpenAI, Anthropic, Gemini)
- Added documentation for Langfuse and LiteLLM observability integrations
- Added installation instructions for optional dependency groups

## [2.1.0] - 2026-02-25

### Added
- **AsyncRAILClient** — Non-blocking httpx-based client with in-memory caching and automatic retries
- **PolicyEngine** — Configurable enforcement policies: `log_only`, `block`, `regenerate`, `custom`
- **RAILSession** — Multi-turn conversation tracker with adaptive quality gating and context windowing
- **RAILMiddleware** — Provider-agnostic pre/post hooks around any async LLM generate function
- **RAILOpenAI** — Drop-in wrapper for `openai>=1.0` with automatic RAIL evaluation
- **RAILAnthropic** — Drop-in wrapper for `anthropic>=0.30` with automatic RAIL evaluation
- **RAILGemini** — Drop-in wrapper for `google-genai>=1.0` with automatic RAIL evaluation
- **RAILLangfuse** — Pushes RAIL scores to Langfuse v3 traces as numeric scores
- **RAILGuardrail** — LiteLLM custom guardrail with pre_call/post_call/during_call hooks
- `RAILBlockedError` exception for policy-blocked content
- `PolicyEvalResult` dataclass for policy enforcement results
- `TurnRecord` dataclass for session history tracking
- Optional dependency groups: `openai`, `anthropic`, `google`, `langfuse`, `litellm`, `integrations`
- `httpx>=0.27.0` added as core dependency for async client

## [2.0.0] - 2026-02-25

### Breaking Changes
- **Authentication**: Changed from `X-API-Key` header to `Authorization: Bearer` header
- **Endpoints restructured**: All endpoint paths changed from `/api/v1/railscore/ui/...` to `/railscore/v1/...`
- **`calculate()` removed**: Replaced by `eval()` with `mode` parameter (`basic` or `deep`)
- **`generate()` removed**: Content generation endpoint no longer available
- **`regenerate()` removed**: Replaced by `protected_evaluate()` and `protected_regenerate()`
- **`analyze_tone()` removed**: Tone analysis endpoint no longer available
- **`match_tone()` removed**: Tone matching endpoint no longer available
- **`check_compliance()` renamed**: Now `compliance_check()` with new parameters and response structure
- **Response models rewritten**: All response dataclasses replaced to match the new API schema
- **Compliance frameworks changed**: Removed `nist` and `soc2`; added `eu_ai_act`, `india_dpdp`, `india_ai_gov`

### Added
- `eval()` — Unified evaluation with `basic` and `deep` modes
- `protected_evaluate()` — Evaluate content against a quality threshold
- `protected_regenerate()` — Regenerate improved content
- `compliance_check()` — Single and multi-framework compliance evaluation (up to 5 frameworks)
- Dimension filtering — Evaluate a subset of dimensions via the `dimensions` parameter
- Custom weights — Weight dimensions differently (must sum to 100)
- Domain and usecase parameters for context-aware scoring
- Multi-framework compliance with cross-framework summary
- Strict mode for compliance (8.5 threshold instead of 7.0)
- Compliance context object (`domain`, `system_type`, `data_types`, `risk_indicators`, `cross_border`)
- EU AI Act risk classification detail in compliance results
- Framework aliases (`ai_act` → `eu_ai_act`, `dpdp` → `india_dpdp`, etc.)
- New exceptions: `ContentTooHarmfulError` (422), `EvaluationFailedError` (500), `NotImplementedByServerError` (501)
- `InsufficientCreditsError` now exposes `balance` and `required` attributes

### Removed
- `calculate()` — Use `eval()` instead
- `generate()` — No replacement (endpoint removed from API)
- `regenerate()` — Use `protected_evaluate()` and `protected_regenerate()` instead
- `analyze_tone()` — No replacement (endpoint removed from API)
- `match_tone()` — No replacement (endpoint removed from API)
- Old response models: `RailScoreResponse`, `GenerateResponse`, `RegenerateResponse`, `ToneAnalyzeResponse`, `ToneMatchResponse`
- Old compliance response model (replaced with richer `ComplianceResult`)
- `DimensionScores`, `DimensionDetails`, `OverallAnalysis`, `EvaluationMetadata`, `ResponseMetadata` models

## [1.0.1] - 2025-01-18

### Fixed
- Corrected GitHub repository URLs in package metadata
- Updated all project URLs from old `sdks/python` structure to `rail-score/tree/main/python`
- Added missing Changelog link to project URLs

## [1.0.0] - 2025-01-18

### Added
- Initial release of RAIL Score Python SDK
- `RailScoreClient` class for API interactions
- Support for all RAIL Score API endpoints:
  - `calculate()` - Calculate RAIL scores for content
  - `generate()` - Generate content with RAIL checks
  - `regenerate()` - Improve existing content
  - `analyze_tone()` - Extract tone profiles from content
  - `match_tone()` - Adjust content to match tone profiles
  - `check_compliance()` - Check compliance (GDPR, HIPAA, NIST, SOC2)
  - `health()` - Check API health status
  - `version()` - Get API version information
- Comprehensive data models using dataclasses
- Custom exception hierarchy
- Full type hints throughout the codebase
- MIT License
- Python 3.8+ support

---

[2.4.0]: https://github.com/Responsible-AI-Labs/rail-score-sdk/releases/tag/v2.4.0
[2.2.1]: https://github.com/Responsible-AI-Labs/rail-score-sdk/releases/tag/v2.2.1
[2.2.0]: https://github.com/Responsible-AI-Labs/rail-score-sdk/releases/tag/v2.2.0
[2.1.1]: https://github.com/Responsible-AI-Labs/rail-score-sdk/releases/tag/v2.1.1
[2.1.0]: https://github.com/Responsible-AI-Labs/rail-score-sdk/releases/tag/v2.1.0
[2.0.0]: https://github.com/Responsible-AI-Labs/rail-score-sdk/releases/tag/v2.0.0
[1.0.1]: https://github.com/Responsible-AI-Labs/rail-score-sdk/releases/tag/v1.0.1
[1.0.0]: https://github.com/Responsible-AI-Labs/rail-score-sdk/releases/tag/v1.0.0
