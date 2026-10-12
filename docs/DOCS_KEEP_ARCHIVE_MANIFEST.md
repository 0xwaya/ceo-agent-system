# Documentation Keep vs Archive Manifest

**Date:** 2026-10-11
**Scope:** Documentation lifecycle and current-vs-historical status for `docs/`.

The root `README.md` is authoritative for current v0.8 behavior. Historical
architecture, audit, session, and setup documents are retained for context and
must not be treated as current security or deployment instructions.

## Keep (Active, user-facing)

- `README.md` — Primary entry and navigation.
- `QUICK_START.md` — Supported localhost dashboard path; legacy examples carry a warning.
- `CONTRIBUTING.md` — Contribution standards.
- `SECURITY.md` — Security policy.
- `ARTIFACT_WORKFLOW.md` — Current private artifact contract.
- `PHASED_UPDATE_PLAN.md` — Current release/privacy/deployment gates.
- `UPGRADE_NEXT_SESSION.md` — Current release handoff.
- `ISOLATED_RUNNER.md` — Current design-only runner status.
- `tests/README.md` — Test usage docs.

## Keep (Historical record, but still valuable)

The files in this section are snapshots, not current operational guidance.

- `SECURITY_AUDIT_2026.md` — Security audit baseline.
- `SECURITY_AUDIT_2026_02_17.md` — Security audit refresh snapshot.
- `SECURITY_PATCH_FEB_2026.md` — Security remediation record.
- `REORGANIZATION_SUMMARY.md` — Repository cleanup history.
- `ARCHITECTURE.md` — v0.5 system architecture snapshot.
- `CEO_AGENT_README.md` — v0.3 guide; not current operating instructions.
- `CEO_CFO_QUICK_REFERENCE.md` — v0.3 command/API snapshot.
- `GRAPH_DASHBOARD_QUICK_START.md` — Earlier dashboard UI snapshot.
- `GRAPH_UI_IMPLEMENTATION.md` / `IMPROVEMENT_PLAN.md` — historical implementation/backlog records.
- `SETUP_INSTRUCTIONS.md` / `GITHUB_SETUP.md` — historical setup proposals.
- `SESSION_MEMORY_2026_02_17.md` — dated session record.
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
