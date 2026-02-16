# Documentation Keep vs Archive Manifest

**Date:** 2026-02-14
**Scope:** Optional documentation sweep for root-level and `graph_architecture/` markdown files.

## Keep (Active, user-facing)

- `README.md` — Primary entry and navigation.
- `QUICK_START.md` — Main runbook for common workflows.
- `SETUP_INSTRUCTIONS.md` — Setup path for real-world execution mode.
- `ARCHITECTURE.md` — Core architecture reference.
- `CONTRIBUTING.md` — Contribution standards.
- `SECURITY.md` — Security policy.
- `CEO_AGENT_README.md` — CEO-mode deep guide.
- `CEO_CFO_QUICK_REFERENCE.md` — Fast operating reference.
- `GRAPH_DASHBOARD_QUICK_START.md` — Graph UI onboarding.
- `graph_architecture/README.md` — Graph subsystem overview.
- `graph_architecture/IMPLEMENTATION_GUIDE.md` — Graph implementation details.
- `tests/README.md` — Test usage docs.

## Keep (Historical record, but still valuable)

- `SECURITY_AUDIT_2026.md` — Security audit baseline.
- `SECURITY_PATCH_FEB_2026.md` — Security remediation record.
- `REORGANIZATION_SUMMARY.md` — Repository cleanup history.
- `VOICE_INTEGRATION_ROADMAP.md` — Approved voice implementation direction.
- `VOICE_SETUP_GUIDE.md` / `VOICE_FREE_TIER_SETUP.md` — Voice deployment guidance.

## Archived (Moved to docs/archive)

These one-time status/snapshot docs were moved to `docs/archive/` to reduce root-level clutter while preserving historical context.

- `docs/archive/CODE_REVIEW_COMPLETE.md`
- `docs/archive/CODE_REVIEW_SENIOR_CONSULTANT.md`
- `docs/archive/DASHBOARD_FIXES.md`
- `docs/archive/UI_FIXES_SUMMARY.md`
- `docs/archive/UX_UI_IMPROVEMENTS.md`
- `docs/archive/TEST_RESULTS.md`
- `docs/archive/PYTHON_VERSION_STANDARDIZATION.md`
- `docs/archive/CEO_AGENT_REBRAND_SUMMARY.md`
- `docs/archive/CEO_CFO_UPGRADE_SUMMARY.md` *(superseded for daily use by quick reference, but still useful as migration history)*

## Sweep Actions Applied

- Removed stale links in `README.md` to deleted docs (`CHAT_GUIDE.md`, `README_CFO.md`).
- Repointed graph UI doc references in `GRAPH_UI_IMPLEMENTATION.md` to existing subgraph source files.
- Added this manifest so doc lifecycle decisions are explicit and repeatable.

## Suggested Next Step

- If desired, I can do a second archival pass for additional low-traffic docs after measuring inbound links.
