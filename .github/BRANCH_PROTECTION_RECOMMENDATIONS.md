# Branch Protection Recommendations

This document defines recommended protection rules for the `main` branch.

## Target Branch

- Branch pattern: `main`

## Recommended Required Checks

Add this required status check:

- `quality`

This maps to the GitHub Actions workflow job in `.github/workflows/code-quality.yml`.

## Recommended Protection Rules

Enable the following in GitHub repository settings for `main`:

- Require a pull request before merging
- Require approvals: **1 minimum**
- Dismiss stale pull request approvals when new commits are pushed
- Require review from code owners (enable after adding `CODEOWNERS`)
- Require status checks to pass before merging
- Require branches to be up to date before merging
- Require conversation resolution before merging
- Do not allow force pushes
- Do not allow deletions

## Merge Strategy Recommendations

- Allow squash merge
- Disable merge commits (optional but recommended for clean history)
- Allow rebase merge only if your team prefers linear rebases

## Admin Policy

Recommended: apply protections to administrators.

## Initial Setup Steps

1. Open GitHub repository settings.
2. Go to **Branches** → **Add branch ruleset** (or legacy branch protection rule).
3. Set branch pattern to `main`.
4. Enable pull request requirement and set approval minimum to 1.
5. Enable required status checks and select `quality`.
6. Enable conversation resolution.
7. Disable force pushes and deletions.
8. Save rules.

## Optional Hardening

- Add `.github/CODEOWNERS` and enable required code owner reviews.
- Add signed commit requirement if your org mandates signed commits.
- Add secret scanning and Dependabot security updates for dependency hardening.
