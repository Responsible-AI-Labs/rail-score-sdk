<!-- Thanks for contributing! Keep the title in conventional-commit form, e.g. "feat(dpdp): add scan_file". -->

## Summary

<!-- What does this PR change, and why? -->

## Type of change

- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change
- [ ] Documentation only

## Checklist

- [ ] Title follows conventional commits (`type(scope): description`)
- [ ] Sync and async clients updated together (if the change touches client methods)
- [ ] New parameters are keyword-only with safe defaults; no breaking changes to public signatures
- [ ] Response parsers read every field with `.get` and a safe default
- [ ] Tests added/updated and passing (`pytest`)
- [ ] Formatted with `black` and lint clean (`flake8`)
- [ ] `CHANGELOG.md` updated
- [ ] Docstrings and README updated for any new public API

## Testing

<!-- How did you verify this change? Commands, output, or screenshots. -->
