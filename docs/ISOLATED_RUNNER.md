# Isolated source-build runner: design and local preparation

Oracle changes are **not authorized**. No runner has been deployed, contacted, or
configured. A VCN provides network boundaries, not a sandbox for hostile code.

## Implemented locally

1. Propose a Python CLI build from explicit scenario inputs. The immutable durable
   proposal waits for owner/admin approval before a metered model call.
2. Generate `tool.py`, `test_tool.py`, and `README.md` as actual private files.
   Only these names are accepted; source is size-limited and syntax-parsed.
   Parsing is not a security review and does not prove tests or functionality.
3. Download owner-checked, hash-verified files or approve a local ZIP.
4. Separately propose and approve a **runner request preparation**. This binds the
   request to the exact source receipt. File mutation makes preparation fail.
5. Download `runner-request.json`. It explicitly says `tests_status: not_run` and
   `runner_status: not_configured`. A successful preparation job means only that
   a request was prepared, not that any tests ran.

No generated source is imported or executed on the local machine. Generated tests
are also untrusted. No command, destination, or isolation override is accepted.
Builds are standard-library-only requests to the model, not a safety guarantee.

## Proposed Oracle topology (not implemented)

```text
Local approval/controller
  -> authenticated private broker/control plane
    -> separate disposable Oracle worker
      -> ephemeral isolated execution guest
    <- bounded test evidence tied to approved source hashes
```

- Keep the worker separate from the existing CEO dashboard VM. Prefer a disposable
  VM or microVM per test job, rather than treating a shared-host container as the
  sole boundary.
- Use a private subnet with no public IP; default-deny NSGs. Block guest outbound
  traffic, DNS and instance metadata. Control-plane traffic must terminate outside
  the guest and must not give generated code network access.
- Supply no `.env`, API key, SSH key, cloud principal, instance credentials, host
  filesystem mounts, container socket, or controller session.
- Run as an unprivileged user, with one CPU, 512 MiB memory, 32 processes, a
  60-second wall limit, 16 MiB workspace and 1 MiB output limit. These are requested
  constraints; an actual runner must independently enforce and attest them.
- Stage only the approved file hashes. Run the fixed unittest command from the
  request in the guest. Do not install model-selected dependencies.
- Validate broker identity, replay protection, approval/source binding, quotas,
  cancellation, VM destruction, timeouts and return-message size limits before
  enabling any remote dispatch.
- Return a controller-validated receipt including job/request hash, file hashes,
  runner/image identity, observed isolation, start/end times, exit status, test
  count/failures and bounded stdout/stderr. Guest claims alone cannot mark a build
  tested. Reject missing evidence and zero discovered tests.
- Model-written tests can agree with model-written bugs. Independent acceptance
  tests and owner review are required before calling a deliverable ready.

Remote transport, worker provisioning, sandbox enforcement, evidence verification,
independent acceptance execution, and the final test approval/dispatch integration
remain pending. No local endpoint accepts a caller-supplied “tests passed” receipt.
Do not manually execute the request on a normal VM or the dashboard host.

## API

- `POST /api/builds/propose` with `{"scenario": {...}}`.
- Existing `POST /api/jobs/<id>/approve` starts approved source generation.
- `POST /api/builds/<build-id>/propose-tests` with `{}` prepares a new approval.
- Approve that new job; `GET /api/jobs/<test-request-id>/runner-request` downloads
  the preparation result. It does not trigger execution.
- Existing job status/cancel, private artifact downloads and local ZIP approval
  work for source builds. Reviewer provisioning/approvals remain on hold.

## Local validation evidence

The offline quality gate passed with 134 tests and no audio-related test skip.
Build tests use synthetic model output to verify real file persistence, owner
downloads, exact content, approval separation, mutation rejection, source limits,
and runner-request states. Generated test files are never executed.
Browser smoke verified proposal/approval controls and cancellation with zero model
usage. Live source generation and isolated runner execution have not been tested.
