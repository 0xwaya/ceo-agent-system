# Upgrade handoff: October 11, 2026

## Current state

- Last pushed commit: `56dffa88abbb3ae9187e9167f706ea34ecdd1abb` on `main`
  (v0.8 truthful report execution, durable jobs, memory and access hardening).
- Subsequent fixes and source-build preparation remain local and uncommitted.
- Dashboard: `http://127.0.0.1:5001/`. Check availability before restarting;
  the current attached process may stop when the session ends.
- Local ignored `.env` now selects the approved `gpt-4.1-mini`, with verified
  input/output rates of $0.40/$1.60 per million tokens. Never print credentials.
- Fixed environment bootstrap order, scenario input validation, model access
  diagnostics, modern CTO/engineering guard-rail lookups, report display and
  consistency-gate whitespace parsing.
- Workspace-local ignored VS Code settings enable `python.terminal.useEnvFile`.
- Reports are not working products. Actual Python CLI source builds are a
  separate approval-gated path producing `tool.py`, `test_tool.py`, and `README.md`.
- Separate approval prepares a hash-bound runner request only. No remote runner,
  Oracle connection, generated-code execution or test-pass receipt is implemented.

## Evidence and limits

- Full offline quality gate: **134 passed**; the removed audio test is not part
  of the suite.
  Black, Flake8, consistency and dashboard render checks passed.
  JavaScript syntax, dependency and diff checks passed.
- Approved live engineering report smoke:
  `7f6b3e21bbce4d2fb0355763eeab9cb2` succeeded with CTO, engineering and software
  review, 9 files, 5,373 measured tokens and $0.00477 rate-calculated cost.
  All 9 authenticated downloads matched their file-size and SHA-256 receipts.
  This does not prove every agent or scenario.
- Source builds were tested with synthetic model output: actual file persistence,
  ownership, approval separation, mutation rejection and fail-closed runner states.
  Browser proposal/cancel smoke used no model tokens.
- **Live source generation and sandboxed tests have NOT been verified.**
- Earlier failed jobs remain failed; their reserved usage is not a confirmed charge.

## Tomorrow's TODOs, in order

1. **Resume safely.** Inspect the worktree, confirm pending changes, check the
   dashboard listener and active jobs. Preserve `.env`, retained memory, artifacts,
   jobs and the virtual environment. Do not start duplicate servers or interrupt jobs.
2. **Review source-build scope and approval UX.** Confirm Python CLI scope, fixed
   file names, standard-library requirements and explicit acceptance criteria.
   Check reload recovery and source-build/test-request/ZIP job transitions.
3. **Run one approved live source-generation test.** Use a synthetic small CLI
   request under existing 20,000-token/$1 limits, with explicit renewed approval.
   Inspect actual source, tests and instructions; verify downloads and hashes.
   Do not execute generated code on the Mac or existing dashboard VM.
4. **Design independent acceptance evidence.** Model-written tests cannot establish
   correctness alone. Define trusted acceptance checks, minimum discovered tests,
   and evidence for failures, timeout, cancellation and zero-test rejection.
5. **Finalize isolated Oracle runner design.** Specify separate disposable worker,
   broker identity, approval/hash binding, replay protection, default-deny network
   and metadata access, no credentials/host mounts, resource limits and destruction.
   Validate the proposed design before selecting resources/costs.
6. **Implement offline runner protocol verification.** Add request/response schema,
   source/image binding, bounded output, trusted evidence validation and fake-runner
   integration tests. Keep transport disabled; never accept an arbitrary
   caller-supplied “tests passed” claim.
7. **Approval checkpoint for Oracle.** Only after explicit authorization: read-only
   infrastructure discovery, cost proposal, separate provisioning approval, then
   isolation verification before any untrusted execution.
8. **End-to-end validation and release.** Once a real sandbox exists, separately
   approve a test run and verify build -> approval -> isolated tests -> evidence ->
   review/download. Test regression scenarios; update version/docs to actual scope.
9. **Commit/push checkpoint.** Review all pending changes, rerun quality gates and
   check credential/runtime exclusions. Obtain confirmation before publishing this
   new upgrade; do not deploy to Oracle as part of a Git push.

## Holds and safety boundaries

- Oracle work is **design and local implementation only** until renewed approval.
- Private login activation, Oracle SSH-tunnel testing and tester provisioning remain
  pending. Login-disabled mode is localhost-only, not safe shared tunnel access.
- The dashboard is text-chat only; no audio integration is included.
  Cross-account reviewer approvals remain undecided and blocked.
- No unrestricted generated-code execution, deployment, publishing, purchases or
  outreach. Keep actual tests distinct from syntax validation and report generation.
- Cleanup only exact task-generated temporary outputs; preserve persistent data.

## Start here

- [Runner design and current API](ISOLATED_RUNNER.md)
- [README](../README.md)
- [Source generation](../services/build_service.py)
- [Durable runtime and approval endpoints](../services/runtime_service.py)
- [Focused build tests](../tests/test_source_builds.py)
- [Roadmap](REAL_WORLD_EXECUTION_ROADMAP.md)

Validation command: `make check PYTHON=.venv/bin/python`.
Tests deliberately block live provider calls. Live testing requires a separate,
explicitly approved test; never infer it from a green offline suite.
