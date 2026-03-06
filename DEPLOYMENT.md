# PyPI Deployment Guide for rail-score-sdk

This guide provides step-by-step instructions for deploying the RAIL Score Python SDK to PyPI.

## Prerequisites

Before deploying, ensure you have:

1. **PyPI Account**: Register at https://pypi.org/account/register/
2. **API Token**: Generate at https://pypi.org/manage/account/token/
3. **Build Tools Installed**:
   ```bash
   pip install --upgrade pip setuptools wheel build twine
   ```

## Pre-Deployment Checklist

- [x] All code is committed to git
- [x] Version number updated in:
  - [x] `setup.py` (line 10)
  - [x] `rail_score_sdk/__init__.py` (line 35)
- [x] `CHANGELOG.md` updated with release notes
- [x] All tests passing
- [x] Documentation reviewed and updated
- [x] Example files working

## Deployment Steps

### 1. Clean Previous Builds

```bash
rm -rf build dist *.egg-info
```

### 2. Build Distribution Packages

```bash
python -m build
```

This creates:
- `dist/rail_score_sdk-1.0.0.tar.gz` (source distribution)
- `dist/rail_score_sdk-1.0.0-py3-none-any.whl` (wheel distribution)

### 3. Verify Package

```bash
twine check dist/*
```

Expected output:
```
Checking dist/rail_score_sdk-1.0.0-py3-none-any.whl: PASSED
Checking dist/rail_score_sdk-1.0.0.tar.gz: PASSED
```

### 4. Test on TestPyPI (Recommended)

Upload to TestPyPI first to verify everything works:

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ rail-score-sdk

# Verify import works
python -c "from rail_score_sdk import RailScoreClient; print('Success!')"
```

### 5. Deploy to PyPI

Once verified on TestPyPI, deploy to production PyPI:

```bash
twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your PyPI API token (starts with `pypi-`)

### 6. Verify Installation

After a few minutes, verify the package is available:

```bash
# Install from PyPI
pip install rail-score-sdk

# Verify installation
python -c "from rail_score_sdk import RailScoreClient, __version__; print(f'Version {__version__} installed successfully!')"
```

### 7. Create GitHub Release

1. Go to: https://github.com/Responsible-AI-Labs/rail-score-sdk/releases/new
2. Tag version: `v2.2.0`
3. Release title: `v2.2.0`
4. Description: Copy from CHANGELOG.md
5. Attach distribution files from `dist/`
6. Publish release

## Using GitHub Actions (Automated)

The repository includes GitHub Actions workflows for automated deployment:

### Automatic Deployment on Release

1. Create a new release on GitHub
2. GitHub Actions will automatically:
   - Build the package
   - Run tests
   - Upload to PyPI

### Manual Deployment

Trigger deployment manually:

1. Go to: https://github.com/Responsible-AI-Labs/rail-score-sdk/actions
2. Select "Publish Python Package"
3. Click "Run workflow"
4. Choose environment (testpypi or pypi)

## Post-Deployment

### 1. Update Documentation

- Update PyPI badge in README.md
- Announce release on Discord/Twitter/Blog
- Update documentation site

### 2. Monitor Package

- Check PyPI page: https://pypi.org/project/rail-score-sdk/
- Monitor download statistics
- Watch for user issues

### 3. Version Bump

For next development cycle:

```bash
# Update version to next planned release
# e.g., 1.0.0 -> 1.1.0-dev or 1.0.1-dev
```

## Troubleshooting

### Build Failures

**Problem**: Build fails with missing files
```bash
# Solution: Check MANIFEST.in includes all necessary files
cat MANIFEST.in
```

**Problem**: Import errors during build
```bash
# Solution: Verify all dependencies in requirements.txt
pip install -r requirements.txt
```

### Upload Failures

**Problem**: `File already exists` error
```bash
# Solution: Increment version number, can't re-upload same version
# Update version in setup.py and __init__.py
```

**Problem**: Authentication failed
```bash
# Solution: Verify API token
# 1. Check token format starts with pypi-
# 2. Generate new token at https://pypi.org/manage/account/token/
# 3. Use __token__ as username
```

**Problem**: Package name already taken
```bash
# Solution: Choose different package name in setup.py and pyproject.toml
# Current name: rail-score-sdk
```

### Import Failures After Installation

**Problem**: Module not found after installation
```bash
# Solution: Check package structure
python -c "import rail_score_sdk; print(rail_score_sdk.__file__)"

# Verify __init__.py exports
cat rail_score_sdk/__init__.py
```

## Version Management

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.x.x): Breaking API changes
- **MINOR** (x.1.x): New features, backwards compatible
- **PATCH** (x.x.1): Bug fixes, backwards compatible

### Version Update Checklist

When bumping version:

1. Update `setup.py` line 10
2. Update `rail_score_sdk/__init__.py` line 35
3. Update `pyproject.toml` line 7
4. Update `CHANGELOG.md`
5. Run tests
6. Build and verify
7. Deploy

## Security

### API Token Management

- **Never commit** API tokens to git
- Store tokens in environment variables:
  ```bash
  export TWINE_USERNAME=__token__
  export TWINE_PASSWORD=pypi-your-token-here
  ```
- Use GitHub Secrets for CI/CD:
  - `PYPI_API_TOKEN`
  - `TEST_PYPI_API_TOKEN`

### Package Signing (Optional)

For additional security, sign packages with GPG:

```bash
# Generate GPG key
gpg --gen-key

# Sign and upload
twine upload --sign dist/*
```

## Rollback Procedure

PyPI doesn't support deleting or replacing releases. If you need to rollback:

1. **Release new version** with fix:
   ```bash
   # Increment patch version
   # e.g., 1.0.0 -> 1.0.1
   ```

2. **Yank bad version** (makes it unavailable for new installs):
   - Go to PyPI project page
   - Click "Manage" → "Releases"
   - Select version → "Yank"

3. **Communicate**: Notify users via:
   - GitHub release notes
   - PyPI project description
   - Social media/blog

## Contact

For deployment issues or questions:

- Email: research@responsibleailabs.ai
- GitHub Issues: https://github.com/Responsible-AI-Labs/rail-score-sdk/python/issues
- Discord: https://responsibleailabs.ai/discord

## Resources

- **PyPI Documentation**: https://packaging.python.org/
- **Twine Documentation**: https://twine.readthedocs.io/
- **Packaging Guide**: https://packaging.python.org/guides/
- **PEP 517/518**: Modern Python packaging standards
