# RAIL Score SDK - Examples

This directory contains comprehensive examples demonstrating how to use the RAIL Score Python SDK.

## Quick Start

1. **Install the SDK:**
   ```bash
   pip install rail-score-sdk
   ```

2. **Get your API key:**
   - Sign up at https://responsibleailabs.ai
   - Get your API key from the dashboard
   - Replace `'your-rail-api-key-here'` in the examples

3. **Run an example:**
   ```bash
   python examples/basic_usage.py
   ```

## Examples Overview

### 🚀 Beginner Examples

#### 1. [basic_usage.py](basic_usage.py)
**What it demonstrates:**
- Initialize the RAIL Score client
- Calculate RAIL scores for content
- Display dimension scores and analysis
- Understand RAIL scoring results

**Best for:** First-time users, understanding basic RAIL scoring

**Key concepts:**
- `client.calculate()` method
- Dimension scores (fairness, safety, reliability, etc.)
- Overall analysis (strengths, weaknesses)
- RAIL score grading system

---

#### 2. [content_generation.py](content_generation.py)
**What it demonstrates:**
- Generate AI content with RAIL quality checks
- Set minimum score requirements
- Automatic regeneration if requirements not met
- Track generation metadata

**Best for:** Content creators, marketing teams, writers

**Key concepts:**
- `client.generate()` method
- RAIL requirements and auto-regeneration
- Generation history and attempts
- Context-aware content generation

---

#### 3. [tone_matching.py](tone_matching.py)
**What it demonstrates:**
- Analyze tone from text or URLs
- Create reusable tone profiles
- Match content to a specific tone
- Adjust content tone programmatically

**Best for:** Brand consistency, content teams, copywriters

**Key concepts:**
- `client.analyze_tone()` method
- `client.match_tone()` method
- Tone characteristics (formality, complexity, voice)
- Brand voice preservation

---

### 🎯 Intermediate Examples

#### 4. [regenerate_content.py](regenerate_content.py)
**What it demonstrates:**
- Improve existing content
- Target specific RAIL dimensions
- Iterative content improvement
- Preserve structure vs. tone

**Best for:** Content editors, quality improvement workflows

**Key concepts:**
- `client.regenerate()` method
- Dimension-specific improvements
- Keep structure/tone options
- Before/after score comparison
- Iterative improvement workflows

---

#### 5. [compliance_check.py](compliance_check.py)
**What it demonstrates:**
- Check GDPR compliance
- HIPAA compliance validation
- NIST cybersecurity framework
- SOC 2 compliance evaluation
- Comparative compliance analysis

**Best for:** Legal teams, compliance officers, security professionals

**Key concepts:**
- `client.check_compliance()` method
- Framework-specific checks (GDPR, HIPAA, NIST, SOC2)
- Violation detection and recommendations
- Compliance scoring and status

---

#### 6. [batch_processing.py](batch_processing.py)
**What it demonstrates:**
- Process multiple content items efficiently
- Error handling and retry logic
- Progress tracking for large batches
- Aggregate statistics and reporting
- Export results to CSV

**Best for:** Bulk content evaluation, data analysis, reporting

**Key concepts:**
- Batch processing patterns
- Error handling with retries
- Exponential backoff for rate limits
- Progress bars and status tracking
- Data export and analysis

---

### 🔧 Advanced Examples

#### 7. [error_handling.py](error_handling.py)
**What it demonstrates:**
- Handle authentication errors
- Manage rate limits with retry logic
- Handle insufficient credits gracefully
- Validation error management
- Comprehensive error handling patterns

**Best for:** Production applications, robust integrations

**Key concepts:**
- Custom exception types
- Retry mechanisms with exponential backoff
- Error recovery strategies
- Timeout handling
- Production-ready error patterns

---

#### 8. [advanced_features.py](advanced_features.py)
**What it demonstrates:**
- Custom dimension weights
- Model preference selection
- Source tracking and analytics
- Domain-specific evaluation
- Complete content workflows
- Metadata extraction and export

**Best for:** Advanced users, custom workflows, analytics

**Key concepts:**
- Custom weight configuration
- OpenAI vs Gemini vs Both models
- Domain-specific scoring
- Source attribution
- Multi-step workflows
- JSON export for integration

---

#### 9. [environment_config.py](environment_config.py)
**What it demonstrates:**
- Environment variable configuration
- Multi-environment setup (dev/staging/prod)
- Configuration classes and patterns
- Docker and Kubernetes deployment
- AWS Parameter Store integration
- Security best practices

**Best for:** DevOps, production deployments, team projects

**Key concepts:**
- .env file management
- Environment-specific configs
- Secret management
- Docker/Kubernetes configuration
- Cloud platform integration
- Security best practices

---

## Example Progression

We recommend going through examples in this order:

### Level 1: Basics
1. `basic_usage.py` - Understand RAIL scoring
2. `content_generation.py` - Generate content with quality checks
3. `tone_matching.py` - Work with tone profiles

### Level 2: Intermediate
4. `regenerate_content.py` - Improve existing content
5. `compliance_check.py` - Regulatory compliance
6. `batch_processing.py` - Process multiple items

### Level 3: Advanced
7. `error_handling.py` - Production-ready error handling
8. `advanced_features.py` - Custom workflows and features
9. `environment_config.py` - Deployment and configuration

## Common Use Cases

### Content Quality Assurance
```python
# Combine: basic_usage.py + regenerate_content.py
1. Calculate RAIL score to identify weaknesses
2. Regenerate content to improve specific dimensions
3. Validate final content meets requirements
```

### Brand Voice Consistency
```python
# Combine: tone_matching.py + batch_processing.py
1. Analyze brand content to create tone profile
2. Batch process all content to match brand tone
3. Track consistency across content library
```

### Compliance Workflow
```python
# Combine: compliance_check.py + batch_processing.py + error_handling.py
1. Check all content against compliance frameworks
2. Handle errors gracefully with retries
3. Generate compliance reports
```

### Production Integration
```python
# Combine: environment_config.py + error_handling.py + advanced_features.py
1. Configure for multiple environments
2. Implement robust error handling
3. Use custom workflows for your use case
```

## Running Examples

### Basic Run
```bash
python examples/basic_usage.py
```

### With API Key from Environment
```bash
export RAIL_API_KEY=your-rail-api-key-here
python examples/basic_usage.py
```

### With .env File
Create `.env` file:
```
RAIL_API_KEY=your-rail-api-key-here
RAIL_BASE_URL=https://api.responsibleailabs.ai
RAIL_TIMEOUT=30
```

Then run:
```bash
python examples/environment_config.py
```

## Modifying Examples

All examples use `api_key='your-rail-api-key-here'`. Replace with:

### Option 1: Hardcode (for testing only)
```python
client = RailScoreClient(api_key='rail_abc123...')
```

### Option 2: Environment Variable (recommended)
```python
import os
client = RailScoreClient(api_key=os.getenv('RAIL_API_KEY'))
```

### Option 3: Configuration File
```python
import json
with open('config.json') as f:
    config = json.load(f)
client = RailScoreClient(api_key=config['api_key'])
```

## Example Output

Most examples include formatted output showing:
- Input content
- RAIL scores and grades
- Dimension-specific scores
- Suggestions and recommendations
- Metadata and performance metrics

Example output format:
```
RAIL Score: 8.5/10 (A)
Grade: A

Dimension Scores:
  Fairness: 8.2/10 (B+)
    Suggestion: Consider diverse perspectives...
  Safety: 9.1/10 (A)
  Reliability: 8.8/10 (A)
  ...

Strengths:
  • Clear and transparent explanation
  • Strong safety considerations
  ...

Weaknesses:
  • Could improve inclusivity
  ...
```

## Troubleshooting

### "Authentication failed"
- Check your API key is correct
- Get a new key from https://responsibleailabs.ai/dashboard

### "Rate limit exceeded"
- Free tier: 60 requests/minute
- Wait before retrying or upgrade your plan
- See `error_handling.py` for retry logic

### "Insufficient credits"
- Check credit balance in dashboard
- Purchase topup or upgrade plan
- Free tier gets 100 credits/month

### "Timeout error"
- Increase timeout: `RailScoreClient(api_key='...', timeout=60)`
- Default is 30 seconds
- Generation/regeneration may take longer

### "Module not found"
- Install SDK: `pip install rail-score-sdk`
- For dev dependencies: `pip install rail-score-sdk[dev]`

## Additional Resources

- **Documentation**: https://responsibleailabs.ai/developer/docs
- **API Reference**: https://responsibleailabs.ai/developers/api-ref
- **Dashboard**: https://responsibleailabs.ai/dashboard
- **Support**: research@responsibleailabs.ai
- **GitHub**: https://github.com/RAILethicsHub/sdks/python

## Contributing Examples

Have an example to share? We'd love to include it!

1. Fork the repository
2. Add your example file
3. Update this README
4. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## License

All examples are provided under the MIT License. See [LICENSE](../LICENSE) for details.
