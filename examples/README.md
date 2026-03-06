# RAIL Score SDK v2 - Examples

This directory contains examples demonstrating how to use the RAIL Score Python SDK v2.

## Quick Start

1. **Install the SDK:**
   ```bash
   pip install rail-score-sdk
   ```

2. **Get your API key:**
   - Sign up at https://responsibleailabs.ai
   - Get your API key from the dashboard
   - Replace `'your-api-key-here'` in the examples

3. **Run an example:**
   ```bash
   python examples/basic_usage.py
   ```

## Examples

### [basic_usage.py](basic_usage.py)
Core evaluation workflow — basic mode and deep mode with explanations.

### [advanced_features.py](advanced_features.py)
Custom dimension weights, single-dimension evaluation, domain-specific scoring, and basic vs deep mode comparison.

### [compliance_check.py](compliance_check.py)
Single-framework and multi-framework compliance checks against GDPR, CCPA, HIPAA, EU AI Act, India DPDP, and India AI Governance. Includes strict mode and risk classification.

### [regenerate_content.py](regenerate_content.py)
Protected content workflow — evaluate content against a quality threshold, regenerate improved content, and the full evaluate-then-regenerate pipeline.

### [error_handling.py](error_handling.py)
Handling authentication errors, validation errors, insufficient credits, rate limiting with retry, and content-too-harmful rejections.

### [batch_processing.py](batch_processing.py)
Processing multiple content items with retry logic, progress tracking, and aggregate statistics.

## API Endpoints Covered

| Example | Endpoints |
|---------|-----------|
| basic_usage | `eval` |
| advanced_features | `eval`, `version` |
| compliance_check | `compliance/check` (single + multi-framework) |
| regenerate_content | `protected` (evaluate + regenerate) |
| error_handling | `eval`, `protected` |
| batch_processing | `eval` |
