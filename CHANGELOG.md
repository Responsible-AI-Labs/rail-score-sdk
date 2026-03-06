# Changelog

All notable changes to the RAIL Score Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[2.2.0]: https://github.com/Responsible-AI-Labs/rail-score-sdk/releases/tag/v2.2.0
[2.1.1]: https://github.com/Responsible-AI-Labs/rail-score-sdk/releases/tag/v2.1.1
[2.1.0]: https://github.com/Responsible-AI-Labs/rail-score-sdk/releases/tag/v2.1.0
[2.0.0]: https://github.com/Responsible-AI-Labs/rail-score-sdk/releases/tag/v2.0.0
[1.0.1]: https://github.com/Responsible-AI-Labs/rail-score-sdk/releases/tag/v1.0.1
[1.0.0]: https://github.com/Responsible-AI-Labs/rail-score-sdk/releases/tag/v1.0.0
