# SECURITY_NOTES.md — ceo-agent-system

Date: 2026-03-02 (America/New_York)

## Current posture (from repo behavior)
- App warns when `SECRET_KEY` is unset and uses insecure development fallback.
- App warns when `OPENAI_API_KEY` is unset.
- Rate limiting may be disabled if `Flask-Limiter` is not installed.
- Input validation is present (`utils/validators.py`, payload allowlists referenced in README).

## Actionable security recommendations

### 1) Production secret hygiene (Priority: High)
- Require `SECRET_KEY` in production startup path; fail closed when missing.
- Keep `.env` out of git, rotate any leaked dev secrets.

### 2) Rate-limiting baseline (Priority: High)
- Ensure `Flask-Limiter` is installed/enforced in production deployments.
- Apply limits on chat, agent-run, and admin-trigger routes.

### 3) Transport and session protections (Priority: Medium)
- Enforce HTTPS/TLS in production.
- Set secure cookie flags (`Secure`, `HttpOnly`, `SameSite=Lax/Strict`) where applicable.

### 4) Artifact safety (Priority: Medium)
- Keep generated artifacts in controlled directories only.
- Sanitize/validate file paths and filenames before persistence/render.

### 5) Dependency + CI hardening (Priority: Medium)
- Add regular dependency audit pass (e.g., `pip-audit`) in CI.
- Keep lock/constraints strategy for reproducible installs.

## Notes on Solidity standards
- No Solidity contracts were found in this repository.
- If smart contracts are introduced later, follow Cyfrin-aligned controls:
  - checks-effects-interactions
  - explicit access control and role separation
  - invariant/fuzz testing
  - pull over push payments
  - upgradeability threat modeling and storage layout checks.
