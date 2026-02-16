# Pull Request

## Summary

Describe what changed and why.

## Validation

- [ ] Ran targeted checks for changed code
- [ ] Ran local smoke test for impacted endpoint/feature
- [ ] Included test evidence in PR description

## Quality Gates

- [ ] `black --check .` passes
- [ ] `flake8 . --max-line-length=100` passes
- [ ] `pytest -q` passes (or explained any known unrelated failures)

## Code Review Checklist

- [ ] Root cause is fixed (not only symptoms)
- [ ] No unrelated refactors mixed into this PR
- [ ] Error handling and logging are adequate
- [ ] Security/privacy impact reviewed
- [ ] Docs updated for behavior/config changes
