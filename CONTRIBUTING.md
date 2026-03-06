# Contributing to RAIL Score Python SDK

Thank you for your interest in contributing to the RAIL Score Python SDK! We welcome contributions from the community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to research@responsibleailabs.ai.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a new branch for your changes
5. Make your changes
6. Test your changes
7. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip
- git

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/rail-score-sdk.git
cd rail-score-sdk

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (if available)
# pre-commit install
```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-endpoint` - for new features
- `fix/authentication-error` - for bug fixes
- `docs/update-readme` - for documentation changes
- `refactor/client-structure` - for refactoring

### Commit Messages

Write clear, concise commit messages:
- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests when relevant

Example:
```
Add support for custom timeout configuration

- Add timeout parameter to RailScoreClient
- Update documentation with timeout examples
- Add tests for timeout behavior

Fixes #123
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rail_score_sdk --cov-report=html

# Run specific test file
pytest tests/test_client.py

# Run specific test
pytest tests/test_client.py::test_calculate
```

### Writing Tests

- Write tests for all new features
- Maintain or improve code coverage
- Use descriptive test names
- Follow the existing test structure

Example:
```python
def test_calculate_with_custom_domain():
    """Test calculate endpoint with custom domain parameter."""
    client = RailScoreClient(api_key="test-key")
    result = client.calculate(
        content="Test content",
        domain="healthcare"
    )
    assert result.rail_score > 0
```

## Code Style

We use the following tools to maintain code quality:

### Black (Code Formatting)

```bash
# Format all files
black rail_score_sdk/

# Check formatting without modifying files
black --check rail_score_sdk/
```

### Flake8 (Linting)

```bash
# Run linter
flake8 rail_score_sdk/
```

### MyPy (Type Checking)

```bash
# Run type checker
mypy rail_score_sdk/
```

### Code Style Guidelines

- Follow PEP 8 style guide
- Use type hints for function signatures
- Write docstrings for all public functions and classes
- Keep functions focused and concise
- Use meaningful variable names
- Add comments for complex logic

Example:
```python
def calculate(
    self,
    content: str,
    domain: str = "general",
    explain_scores: bool = True,
) -> RailScoreResponse:
    """
    Calculate RAIL score for content.

    Args:
        content: Text content to evaluate (20-50000 characters)
        domain: Content domain (general, healthcare, law, etc.)
        explain_scores: Include detailed explanations for scores

    Returns:
        RailScoreResponse with score, grade, and dimension analysis

    Raises:
        ValidationError: If content is invalid
        AuthenticationError: If API key is invalid
    """
    # Implementation
```

## Submitting Changes

### Pull Request Process

1. **Update Documentation**: Ensure README and docstrings are updated
2. **Add Tests**: Include tests for new features or bug fixes
3. **Run Tests**: Ensure all tests pass locally
4. **Update CHANGELOG**: Add entry to CHANGELOG.md
5. **Create Pull Request**: Submit PR with clear description

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] All tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No breaking changes (or clearly documented)
```

## Reporting Bugs

### Before Submitting a Bug Report

- Check the documentation
- Search existing issues
- Verify you're using the latest version
- Collect relevant information (Python version, SDK version, error messages)

### Bug Report Template

```markdown
**Describe the bug**
Clear and concise description of the bug

**To Reproduce**
Steps to reproduce the behavior:
1. Initialize client with '...'
2. Call method '...'
3. See error

**Expected behavior**
What you expected to happen

**Actual behavior**
What actually happened

**Environment:**
- OS: [e.g., macOS 13.0]
- Python version: [e.g., 3.10.5]
- SDK version: [e.g., 1.0.0]

**Additional context**
Any other relevant information
```

## Feature Requests

We welcome feature requests! Please:

1. Check if the feature already exists
2. Search existing feature requests
3. Provide clear use cases
4. Explain why this feature would be useful

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
Clear description of the problem

**Describe the solution you'd like**
Clear description of what you want to happen

**Describe alternatives you've considered**
Alternative solutions or features

**Additional context**
Any other relevant information
```

## Development Workflow

### Typical Workflow

```bash
# 1. Update your fork
git checkout main
git pull upstream main

# 2. Create a new branch
git checkout -b feature/my-new-feature

# 3. Make changes
# Edit files...

# 4. Run tests and code quality checks
black rail_score_sdk/
flake8 rail_score_sdk/
mypy rail_score_sdk/
pytest

# 5. Commit changes
git add .
git commit -m "Add my new feature"

# 6. Push to your fork
git push origin feature/my-new-feature

# 7. Create pull request on GitHub
```

## Questions?

If you have questions or need help:

- Email: research@responsibleailabs.ai
- Discord: [Join our community](https://responsibleailabs.ai/discord)
- GitHub Issues: [Create an issue](https://github.com/Responsible-AI-Labs/rail-score-sdk/issues)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Acknowledgments

Thank you to all contributors who help make this project better!
