# Oracle VCN access and release handoff: October 14, 2026

## October 14 pickup: documented todos

- [x] Investigate OpenClaw/Ollama background startup. Both user LaunchAgents
  (`ai.openclaw.gateway` and `com.ollama.server`) have `RunAtLoad=true` and
  `KeepAlive=true`: they start when loaded at login and are supervised for
  restart. Last night's `bootout` unloaded them for that login session; it did
  not permanently disable automatic startup. Both are running again today.
- [x] Check whether OpenClaw uses Ollama. Its configured primary model is
  `openai/gpt-5.4-nano`, with `ollama/gemma3:4b` and `ollama/llama3:8b` among
  fallbacks. Ollama is a separately supervised service, not a required OpenClaw
  dependency, but those local fallbacks require it. Configuration explains the
  possible use, not which request loaded yesterday's model runner; that request
  has not been traced. No credentials were printed or startup settings changed.
- [ ] Decide whether to keep automatic startup or make OpenClaw/Ollama manual.
  Do not disable services or change model-provider configuration without approval.
- [x] Implement CFO skepticism review after all dispatched domains and before
  consolidation. Cover missing irreversible-action approvals, untracked external
  costs, spend above CFO approval, missing CEO rationale, and unknown dispatch
  roles. Add state fields, risk-escalation requests, high/critical approval
  routing, report visibility, and offline regression coverage for all seven
  requested scenarios. Implemented from the specification with operator approval;
  no source file was attached. Validation results are recorded below.
- [ ] Configure Oracle Stripe secrets/prices and a reachable signed HTTPS
  webhook before enabling payment delivery. Earlier SSH outage notes are
  historical; the VM was intentionally stopped at the end of October 13.
- [ ] Operator: revoke/rotate the previously exposed Supabase access token.
- [ ] Keep the echo-agent VM stopped until the echo agent is ready.

### Local server stop/start reference

OpenClaw and Ollama were stopped again on October 14 at the operator's request;
their launchd jobs and process/listener checks confirmed they exited. Leave
them stopped while working on the CEO app. To stop them on the Mac:

```bash
launchctl bootout "gui/$(id -u)/ai.openclaw.gateway"
launchctl bootout "gui/$(id -u)/com.ollama.server"
```

An error saying a service cannot be found can mean it is already unloaded;
verify with `launchctl list` and process/listener checks rather than assuming.
Use the bootstrap commands in "Resume next session" only when intentionally
returning to OpenClaw/echo-agent work. `bootout` is temporary; automatic startup
at a later login remains configured. First update/troubleshoot the echo agent
locally; deploy to its reserved Oracle instance only after separate readiness
checks and authorization. Do not start that VM as part of CFO development.

### CFO skepticism review contract

Source version is now v0.8.3 (including dashboard asset cache refresh).
Oracle's last deployed version remains v0.8.2; this work does not start either VM.

`graph_architecture/cfo_skepticism.py` adds a deterministic review after domain
dispatch and before consolidation. It makes no model calls and does not
re-analyze finances. It appends `cfo_flags`, writes `cfo_skepticism_report`, and
creates risk-escalation requests using the existing approval schema.

- Unknown dispatch roles and irreversible actions without matching approval
  IDs are critical; zero-cost external effects and spend over CFO approval
  are high; missing CEO rationale is medium. Every finding creates a request.
  High/critical findings bypass consolidation and go directly to approval.
  Medium findings consolidate but still reach the existing pending-approval gate.
  Invalid dispatch plans are intercepted before invoking any domain, so an
  unknown role can be escalated without ever being executed.
- Review reads every `agent_outputs` record's structured `summary`. Operational
  evidence uses `actions: [{action_id, irreversible, approval_request_id,
  external_side_effect, cost}]`, `external_actions_executed`, and `budget_used`.
  Action approval IDs must occur in the trusted state's `approved_actions`;
  model-generated approval booleans and prose do not count.
- Spend comes from `budget_spent` and reported actual output/action costs.
  Overlapping ledger/output totals are not counted twice. Planning estimates
  are not spend. The ceiling comes from the latest CFO summary only when its
  recommendation is unconditional `approve`, using `key_numbers.total_budget`;
  a conditional/rejected/missing approval cannot authorize actual spend.
  Invalid monetary values fail explicitly. API token metering remains separate
  from business-action spending.
- Checks inspect structured execution evidence, not arbitrary natural-language
  promises. Existing local-artifact agents do not execute business actions.
  Future live connectors must supply trustworthy action/cost/approval records;
  this post-execution review is not a substitute for pre-action authorization.
- Checkpointed graph jobs persist as `awaiting_approval`, retain trial
  reservations, show CFO findings, and use the existing owner/admin-protected
  approval endpoint. Acknowledgement resumes the exact paused checkpoint to
  reporting without replaying domains. It does not authorize new external work.
  Cancellation remains available. Pending approvals cannot produce a completed
  report, even on graphs compiled without a checkpointer.
- Final reports include flags and condition their external-action statement on
  the execution records, rather than always claiming no external actions.
  Historical checkpoint state without these fields remains readable.
- Validation: `make check PYTHON=/Users/pc/code/ceo/ceo-agent-system/.venv/bin/python`
  passed Black, Flake8, consistency, development/production dashboard render
  smoke, and **214 offline tests**, including 25 CFO/approval regressions.
  `node --check static/js/app.js` and `git diff --check` passed. Coverage includes
  the seven requested scenarios, exact decimal spending boundaries, idempotent
  flags, invalid monetary data, unsupported-role interception, real checkpoint
  interruption/resume, durable job status, retained free trials, and dashboard
  risk-acknowledgement wording. No live models, payments, or external actions
  were invoked.

## End-of-day handoff and restart

This section and the v0.8.2/onboarding sections are the current state. Older
October 12 snapshots below are historical, not instructions to repeat setup.

- Releases on `main` and deployed on Oracle: `e0ca00b` (onboarding, website
  evidence, free-trial/membership gates), `61add3e` (persistent systemd hosting),
  and `e5e795e` (v0.8.2 dashboard polish). GitHub Code Quality passed for all
  three commits, including the full offline suite.
- Final local handoff validation:
  `make check PYTHON=/Users/pc/code/ceo/ceo-agent-system/.venv/bin/python`
  passed Black, Flake8, consistency, dashboard render smoke, and **189 tests**
  (two expected offline/deprecation warnings). `git diff --check` passed.
  Before shutdown, Oracle had 19 succeeded and two failed historical jobs,
  with no running or queued jobs.
- The administrator account was created by the operator, and login succeeded.
  Preserve it: do not rerun first-administrator setup, reset credentials, or
  recreate the runtime databases.
- Oracle serves the app on `127.0.0.1:5001`; the Mac SSH tunnel exposes it only
  on `127.0.0.1:5002`. This remains private development, not public production.
- Stripe integration is implemented and previously tested in the local sandbox,
  but Oracle payment configuration is still missing. Checkout is unavailable
  there until secrets, prices, and a reachable signed webhook are configured.
  No live charges were made. Email verification/password recovery, a public TLS
  rollout, and isolated generated-code execution remain outstanding.
- OCI signing credentials are secured under `~/.oci`, SSH keys under `~/.ssh`,
  and the old Oracle console auth token was deleted. The previously exposed
  Supabase personal access token still needs revocation/rotation by the operator;
  protected local storage is not a substitute for rotation.
- The echo-agent VM remains stopped. Do not start it until that project is ready.
- Tonight's authorized shutdown scope is the CEO Oracle VM, its Mac SSH tunnel,
  and local Ollama/OpenClaw servers. Leave macOS services and VS Code alone.
  Stop supervised services through their supervisors so they do not respawn.
  VM stop/start preserves accounts, ignored environment files, and runtime data.

### Safe shutdown after a green push

1. Commit/push only reviewed changes after `make check PYTHON=.venv/bin/python`
   and `git diff --check` pass; verify GitHub Code Quality for the pushed commit.
2. Pull that commit on Oracle using `git pull --ff-only`, with a clean worktree.
   Check for running/queued jobs before shutdown; do not interrupt user work
   without reporting it and obtaining approval.
3. Stop the app on Oracle with `sudo systemctl stop ceo-agent-dashboard`.
   Verify it is inactive and port 5001 has no listener. Keep the service enabled
   so it starts automatically when the VM is started again.
4. From the Mac, stop `instance-20261010-0931` through the OCI API:

   ```bash
   ~/.oci/cli-venv/bin/oci compute instance action --action SOFTSTOP \
     --instance-id <instance-20261010-0931 OCID> --wait-for-state STOPPED
   ```

   Verify both known Oracle instances are `STOPPED`. Do not change VCN rules,
   delete instances, or run a guest shutdown command merely to exit SSH.
5. Close the project tunnel by its verified PID (`kill <tunnel PID>`).
   Local launchd-managed servers can be stopped for this login session with:

   ```bash
   launchctl bootout "gui/$(id -u)/ai.openclaw.gateway"
   launchctl bootout "gui/$(id -u)/com.ollama.server"
   ```

   These commands unload the jobs, not their saved configuration. Verify the
   project tunnel, gateway, model server, and any Ollama runner listeners are gone.

### Resume next session

1. Start **only** `instance-20261010-0931` in the Oracle Console, or use the OCI
   `START` command below and wait for `RUNNING`. SSH timeouts while it is stopped
   are expected; they do not mean the repository or network configuration broke.
2. On the Mac, run `ssh oracle-ceo`. The existing alias forwards local port 5002.
   On Oracle, verify `systemctl is-active ceo-agent-dashboard`; the enabled
   service should start automatically. If needed, use
   `sudo systemctl start ceo-agent-dashboard`, not a duplicate manual process.
3. Open **http://127.0.0.1:5002/login** and use the existing application account.
   Oracle and Stripe account passwords are not application credentials.
4. Restart local model/gateway services only if needed, on the Mac:

   ```bash
   launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.ollama.server.plist
   launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/ai.openclaw.gateway.plist
   ```

   A subsequent Mac login may already load them; check before bootstrapping.
   No local Flask or Stripe listener needs to run to access the Oracle dashboard.

## Dashboard polish: v0.8.2

- Membership and logout controls now use the dark dashboard palette, consistent
  borders, hover states, and visible keyboard focus instead of browser-default
  button backgrounds.
- Lower sidebar controls are grouped into Scenario memory and Source build cards,
  with aligned enable/disable buttons, a distinct delete action, and compact help
  text. Job actions share the same styling; hidden controls remain hidden.
- Header agents can shrink without pushing account actions off-screen; narrow
  screens wrap the budget/account controls. Existing actions and billing behavior
  are unchanged. The version bump refreshes cached dashboard styles.
- Validation: `make check PYTHON=.venv/bin/python` passed formatting, lint,
  consistency, dashboard-render smoke checks, and all 189 tests. Browser checks
  confirmed no horizontal overflow at 1360px and 390px viewport widths and that
  hidden job controls remain hidden.

## Account onboarding, website evidence, and free analysis

- Application accounts are separate from Oracle and Stripe logins. No account
  password belongs in `.env`. Passwords are hashed in the private runtime database.
- With `ENABLE_AUTH=true` and a strong persistent `SECRET_KEY`, `/setup` presents
  first-time administrator setup. It requires a one-use code, expires in 30 minutes,
  and closes permanently once an administrator exists. Existing CLI provisioning
  remains available for operator recovery.
- To obtain your code on Oracle, start with `ssh oracle-ceo`, then run:

  ```bash
  cd /home/ubuntu/apps/ceo-agent-system
  source /home/ubuntu/.venvs/ceo-agent-system/bin/activate
  python -m flask --app app prepare-setup
  ```

  Open **http://127.0.0.1:5002/setup** on your Mac. Enter the code, your application
  email, and a new password of at least 14 characters. Then log in at `/login`.
  Do not post the setup code or password in chat. Do not start a second app process.
- `/signup` creates ordinary customer accounts after administrator setup.
  Email verification and password-reset delivery are not implemented; keep the
  current deployment private behind the SSH tunnel, not public production.
- Each customer account has one successful free analysis, shared between Analyze,
  the legacy CFO analysis endpoint, and Launch Graph Execution. Concurrent trial
  requests are rejected. Invalid, failed, cancelled, and interrupted runs do not
  consume the trial. Operator/admin and existing reviewer accounts retain their
  previous privileged testing behavior.
- Free runs retain model-token/cost ceilings and measured usage, but do not debit
  the customer wallet. After the trial, a verified active subscription with a
  paid, unexpired period is required. Individual agent tasks and chat require a
  membership and cannot bypass the gate. Reports remain readable after the trial.
- The scenario Website field replaces DBA/Brand in the dashboard; the legacy DBA
  API field remains compatible. Optional public homepage evidence is fetched
  with DNS-pinned public destinations, redirect validation, verified HTTPS,
  bounded content and network reads. Page text is untrusted model data, not
  instructions or independent verification. Fetch failures appear as warnings.
- The header now has an explicit Subscribe / Membership button; a subscription
  popup follows a successful free run or a blocked repeat. Stripe secrets and a
  working signed webhook must be configured separately. Missing payment
  configuration is reported explicitly, not presented as a successful checkout.
- Validation: `make check PYTHON=.venv/bin/python` passed (188 tests, Black,
  Flake8, consistency gate, and dashboard smoke). A real public HTTPS homepage
  fetch succeeded without invoking a model. No live charges were made.
- Release `e0ca00b` was pulled onto Oracle. Application authentication is enabled;
  `/login` and `/setup` returned HTTP 200 through the Mac's port-5002 tunnel,
  and anonymous scenario API access returned HTTP 401. The setup page was also
  checked in the browser. The operator subsequently created their administrator
  account and successfully logged in; do not repeat initial setup.
- The dashboard uses the `ceo-agent-dashboard` systemd service with the existing
  `~/start_ceo.sh`, localhost binding, and port 5001. The service definition is
  tracked in `tools/ceo-agent-dashboard.service`; install it with:

  ```bash
  sudo install -m 644 tools/ceo-agent-dashboard.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable --now ceo-agent-dashboard
  ```

  For an installed service, use `sudo systemctl restart ceo-agent-dashboard`
  after updates and `sudo journalctl -u ceo-agent-dashboard --no-pager -n 50`
  for logs. Do not run a second copy of `~/start_ceo.sh`. Enabling this service
  restores the app after a VM reboot; it does not start a stopped Oracle VM.
  The older manual startup examples below describe the pre-service deployment.

## Historical handoff: Stripe membership integration

This records the earlier Stripe sandbox work. The current Oracle deployment and
onboarding state are documented above; the outage described here was resolved.

- Implementation committed and pushed to `main`: `9072566`.
- Sandbox membership: $29/month, $10 monthly execution allowance, no rollover.
  Purchased $5/$15/$25 top-ups persist; no automatic overages or top-ups.
- Hosted Checkout includes Apple Pay on eligible devices (button observed during
  browser testing) and card payments. A Stripe test-card subscription completed,
  its signed webhook granted $10 exactly once, and the dashboard displayed it.
  The temporary verification subscription was cancelled; no real money was charged.
- Customer Portal is configured in the WayaLabs sandbox for payment methods,
  invoice history, and end-of-period cancellation.
- Signed invoice fulfillment, transactional deduplication, microdollar accounting,
  per-model-call reservations/settlement, expiry and refund/dispute spending holds
  replace the earlier mocked fulfillment. Sandbox and live ledgers are separate.
- API/job ceilings are configurable and remain distinct from scenario budgets.
  Actual external business purchases and connectors are not implemented.
- Full local validation: `make check PYTHON=.venv/bin/python` passed with
  **157 tests**, Black, Flake8, consistency and smoke checks.
  `node --check static/js/app.js` and staged secret scan passed.
  No matching GitHub Actions run was returned during the final check; local green
  is verified, hosted CI completion is not.
- Oracle public IP: `147.224.168.182`, also saved as `ORACLE_PUBLIC_IP` in the
  ignored private `.env`. Credentials were not committed.
- Sandbox webhook registered:
  `https://147.224.168.182/api/billing/webhook`, **disabled pending trusted HTTPS**.
  Its signing secret is saved in the local private `.env`; the Oracle server's
  private environment still needs configuration.
- SSH (22), HTTPS (443), HTTP (80), and app port 5001 all timed out.
  No remote restart, pull, deployment, or server configuration was performed.
- **Root cause (confirmed Oct 13 from the VM journal):** `sudo shutdown -h now`
  was typed inside an `oracle-ceo` SSH session at Oct 12 23:24:41 UTC, which
  powered off the VM's OS. Oracle networking (security list, route table,
  internet gateway) was unchanged, and no repository or local setting was
  involved. The instance was started again on Oct 13 via the OCI CLI. It kept
  public IP `147.224.168.182`, and `ssh oracle-ceo`, `~/start_ceo.sh`, and the
  `127.0.0.1:5002` tunnel were verified working (HTTP 200 on `/admin`).
- A second instance, `instance-20261012-1939` (public `163.192.193.166`, key
  `ssh-key-2026-10-12`), was created Oct 12 23:44 UTC and is **not** the
  `oracle-ceo` target. It is stopped and reserved for the future echo agent.
- The local app and Stripe CLI listener were stopped cleanly for the PC reboot.
  Local processes and forwarding do not persist through reboot.

### Historical local Stripe sandbox startup

These steps start the local sandbox, not the current Oracle deployment. For
normal dashboard access, use the restart procedure at the top of this document.

1. From the repository root, activate the existing virtual environment:
   `source .venv/bin/activate`.
2. Start the local app and sandbox forwarding together:
   `python -m tools.run_stripe_sandbox`.
   The supervisor uses the sandbox key and keeps the CLI signing secret in process
   memory; it does not replace the stored Oracle webhook secret.
3. Open **http://localhost:5001**, not a different hostname. Checkout returns to
   the configured `BILLING_PUBLIC_URL`; browser cookies are hostname-specific.
4. For Oracle, first confirm the VM is running in the Oracle Console and SSH is
   reachable. Inspect the existing service/process before restarting anything.
5. Pull the versioned release, install requirements, configure named accounts and
   private billing environment, and establish trusted public HTTPS before enabling
   the disabled Stripe endpoint. Do not expose the Flask development port publicly.

Rebooting the laptop closes its SSH client and forwarding tunnel, **not the Oracle
VM or the VM's SSH daemon**. A remote foreground app tied to that session may exit;
an app managed by systemd or correctly detached with nohup normally continues.

See [Stripe membership tutorial](STRIPE_INTEGRATION_TUTORIAL.md) for all configuration,
webhook events, endpoint contracts, testing, reconciliation and production limits.

## Current state

- Last pushed CEO commit: `9d0e1c5766a0c409a04c6b61de965206719d99c2` on `main`
  (v0.8 source-build preparation and complete audio integration removal).
- CEO working tree was clean at the release commit. The local preview on port
  5001 is currently stopped; check before starting another process.
- The Oracle VCN walkthrough below documents SSH login and tunneling for an
  existing instance. It does not require host details in this repository and
  does not provision, connect to, or deploy anything to the VCN.
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

## Separate deployment checklist (only if deployment is requested)

1. **Identify the VCN target.** Provide the intended instance address or SSH
  alias, OS username, and approved access path (direct SSH or bastion). Do not
  send private keys or credentials in chat.
2. **Read-only preflight.** Verify running commit, service manager, listener,
  authentication mode, capacity, existing workloads, backups, and rollback
  option without displaying secret values or changing the host.
3. **Deployment plan.** Confirm the target is the intended CEO host, keep port
  5001 private, require named authentication, and preserve the single-process
  durable worker constraint. Record the rollback point before changing it.
4. **Deploy and verify.** After target identification and preflight, deploy a
  versioned release and verify private health and the exact commit. No generated
  code execution is part of this dashboard rollout.
5. **Keep the runner separate.** No isolated runner exists. Do not execute
  generated source on the dashboard host or a normal VM.

## Oracle VCN login and SSH tunnel tutorial

An Oracle VCN is a network, not a login endpoint; SSH connects to a compute
instance in that VCN. These steps cover an already provisioned instance. They
are instructions only: reading or using this guide does not change VCN resources
or deploy the app. Fill placeholders locally using the instance address, OS
username, approved private key, and network access details provided to you.
Never commit or share private-key contents. For dashboard access, keep the app
bound to `127.0.0.1:5001` on the instance, require named authentication, and do
not open port 5001 in the VCN security list/NSG.

### Local SSH config setup (`~/.ssh/config`)

To avoid entering connection arguments manually, add an alias to `~/.ssh/config`:

```sshconfig
Host oracle-ceo
  HostName <instance-public-ip-or-dns>
  User ubuntu
  IdentityFile ~/.ssh/<approved-private-key-file>
  LocalForward 127.0.0.1:5002 127.0.0.1:5001
```

Set secure permissions locally:

```bash
chmod 600 ~/.ssh/<approved-private-key-file>
chmod 600 ~/.ssh/config
```

Then connect and establish the port forward in one step:

```bash
ssh oracle-ceo
```

### Log in to an instance with direct SSH reachability (one-off command)

```bash
VCN_USER='<instance-os-user>'
VCN_HOST='<instance-public-ip-or-dns>'
SSH_KEY="$HOME/.ssh/<approved-private-key-file>"
ssh -i "$SSH_KEY" "$VCN_USER@$VCN_HOST"
```

Use the OS username and address assigned to the existing instance. To close the
interactive shell, type `exit`.

### Open the dashboard through a direct SSH tunnel

Run this on your local computer and leave it running while using the dashboard:

```bash
VCN_USER='<instance-os-user>'
VCN_HOST='<instance-public-ip-or-dns>'
SSH_KEY="$HOME/.ssh/<approved-private-key-file>"
ssh -i "$SSH_KEY" -N -L 127.0.0.1:5002:127.0.0.1:5001 "$VCN_USER@$VCN_HOST"
```

Then browse to `http://127.0.0.1:5002/admin`. Press Ctrl-C in the terminal to
close the tunnel.

### Log in to a private instance through a bastion

```bash
VCN_USER='<instance-os-user>'
VCN_PRIVATE_HOST='<instance-private-ip>'
BASTION_USER='<bastion-os-user>'
BASTION_HOST='<bastion-public-ip-or-dns>'
SSH_KEY="$HOME/.ssh/<approved-private-key-file>"
ssh -i "$SSH_KEY" -J "$BASTION_USER@$BASTION_HOST" "$VCN_USER@$VCN_PRIVATE_HOST"
```

### Open the dashboard through a bastion tunnel

Run this on your local computer and leave it running while using the dashboard:

```bash
VCN_USER='<instance-os-user>'
VCN_PRIVATE_HOST='<instance-private-ip>'
BASTION_USER='<bastion-os-user>'
BASTION_HOST='<bastion-public-ip-or-dns>'
SSH_KEY="$HOME/.ssh/<approved-private-key-file>"
ssh -i "$SSH_KEY" -J "$BASTION_USER@$BASTION_HOST" -N \
  -L 127.0.0.1:5002:127.0.0.1:5001 "$VCN_USER@$VCN_PRIVATE_HOST"
```

Then browse to `http://127.0.0.1:5002/admin`. Press Ctrl-C in the terminal to
close the tunnel. Restrict SSH ingress to the operator's approved IP. SSH
connectivity and dashboard account authentication are separate controls.

### Remote server helper script (`~/start_ceo.sh`)

The following describes the historical helper script. It already exists on
Oracle and is now launched by `ceo-agent-dashboard`; do not overwrite it during
routine startup. It activates the virtual environment and starts the
single-worker Flask service on port `5001`:

```bash
cat << 'EOF' > /home/ubuntu/start_ceo.sh
#!/usr/bin/env bash
cd /home/ubuntu/apps/ceo-agent-system
source /home/ubuntu/.venvs/ceo-agent-system/bin/activate
exec python app.py
EOF
chmod +x /home/ubuntu/start_ceo.sh
```

For the current deployment, start the installed service on Oracle:

```bash
sudo systemctl start ceo-agent-dashboard
systemctl is-active ceo-agent-dashboard
```

To verify the process and port listener:

```bash
ps aux | grep 'python app.py' | grep -v grep
ss -tulpn | grep 5001
```

### Leaving the server and stopping it safely

- To leave the server, type `exit`. This closes only the SSH session; the VM
  and any background app keep running.
- Never run `sudo shutdown -h now` to "close" the connection. Inside an SSH
  session it powers off the Oracle VM, and `ssh oracle-ceo` then times out.
  In a local terminal it powers off your Mac.
- To stop or start the VM, use the Oracle Console (Compute → Instances →
  `instance-20261010-0931` → Stop/Start). You can also use the OCI CLI
  installed at `~/.oci/cli-venv/bin/oci`, configured in `~/.oci/config`:

```bash
~/.oci/cli-venv/bin/oci compute instance action --action START \
  --instance-id <instance-20261010-0931 OCID> --wait-for-state RUNNING
```

- If `ssh oracle-ceo` times out, first check that the instance state is
  `RUNNING` in the console before changing any network settings.

### Credential locations (never commit these)

Only paths are recorded here. No key material or token values appear in the
repository.

| Credential | Location on the Mac | Mode | Purpose |
| --- | --- | --- | --- |
| OCI API signing key | `~/.oci/oci_api_key.pem` | 600 | OCI CLI/API access (fingerprint `f1:c8:…:05:d5`) |
| OCI API public key | `~/.oci/oci_api_key_public.pem` | 644 | Uploaded to the Oracle user's API keys |
| OCI CLI config | `~/.oci/config` | 600 | Profile `DEFAULT`, region `us-chicago-1` |
| OCI CLI | `~/.oci/cli-venv/bin/oci` | n/a | Isolated venv install, OCI CLI 3.95.0 |
| `oracle-ceo` SSH key | `~/.ssh/oracle_vcn_rsa` | 600 | `instance-20261010-0931` (147.224.168.182) |
| Echo agent SSH key | `~/.ssh/oracle_echo_rsa` | 600 | `instance-20261012-1939` (163.192.193.166), reserved for the echo agent |

- The `~/.oci` folder is mode 700. The original browser downloads of the API
  key were deleted after their copies were verified.
- The Oracle console auth token ("ceo ai") was deleted on Oct 13; none is
  currently active. Create a new one only when a service requires it.
- Quick check that API access works:
  `~/.oci/cli-venv/bin/oci iam region list --output table`.
- If the signing key is lost or exposed, delete it in Oracle Console → Profile
  → API keys, generate a new pair, and update `~/.oci/config`.
- The echo agent instance `instance-20261012-1939` was **stopped** on Oct 13
  until the echo agent is ready.

## UI/UX Theme Overhaul & Dashboard Modernization

### October 12, 2026 UI Overhaul

- **Classic Executive Theme**: Replaced neon purple/pink gradients and saturated
  glows with an executive obsidian/slate palette (`--v4-bg: #0b0f17`,
  `--v4-panel: #0f172a`, `--v4-card: #182234`, `--v4-accent: #3b82f6`).
- **High-Contrast Legibility**: Resolved dark-on-dark text collisions in the
  Activity Feed and Reports view. Replaced hardcoded `#334155` and `#64748b` inline styles
  with crisp white (`#f8fafc`), light slate (`#f1f5f9`), and secondary slate (`#cbd5e1`).
- **Eliminated Jarring White Cards**: Converted legacy `#fff` discovery question boxes
  and domain plans to cohesive translucent dark cards with clear, colored category accents.
- **Dark-Theme Tasks Tab**: Updated `.task-card` styling from light `#fafbfc` to
  dark slate `#182234` with readable high-contrast detail rows and priority badges.
- **Global Safeguards**: Added CSS rules ensuring all nested report headings,
  paragraphs, list items, and table elements default to high-contrast legible colors.
- **Agent Detail & Budget Distinction**: Updated `showAgentModal` in `static/js/app.js` and
  `.modal-content` in `static/css/style.css` to clearly distinguish between per-operation
  API spend ceilings ($1.00 metering safeguard) and user-allocated scenario budgets.
- **Compacted Header & Streamlined Density**: Reduced header height to 50px, refined agent
  pills, and streamlined results/modal cards in line with Phase 1 modernization.
- **Task Execution Clarity (Blocker Fix)**: CEO analysis tasks now carry explicit execution
  metadata in API responses (`assigned_agent`, `agent_type`, `budget`, `timeline_days`,
  `expertise_required`) derived from strategic-plan fields (`required_expertise`,
  `estimated_budget`, `estimated_days`). The Tasks tab now renders these values correctly
  and adds direct controls:
  - `⚡ Execute with [Agent]` to run the mapped specialized agent immediately.
  - `💬 Chat with Agent` to switch chat context to the assigned executor.

### Dashboard Modernization Upgrade Plan

1. **Information Density & Compaction**:
   - Reduce header footprint to 50px with a compact pill bar.
   - Streamline KPI metric cards into a responsive horizontal executive ticker.
   - Tighten list item padding in Activity Feed cards for faster scanning.
2. **Intuitive Navigation & Layout Modernization**:
   - Retain the proven 3-column architecture (Parameters → Activity/Reports → Chat)
     without touching the underlying LangGraph orchestration workflow.
   - Introduce collapsible left sidebar (Parameters & Roster) to allow full-width
     report inspection on lower-resolution screens.
   - Consolidate redundant tabs: merge "Execution Graph" visualization into an
     interactive topology sub-view within Reports.
3. **Executive Action Clarity & Stripe Capital Solicitation**:
   - Clear distinction between passive report review and approval-gated actions.
   - Contextual chat drawer with instant agent-switching and thread indicators.
   - **Production Stripe Billing Architecture**: Dedicated `services/billing_service.py`
     managing workspace credits (`workspace_credits` and `credit_transactions` ledger).
   - Real-time task cost calculation: itemizes LLM model tokens, external API tools
     (scraping, analytics, hosting), and platform orchestration fees.
   - Integrated `/api/billing/quote` and `/api/billing/checkout` endpoints supporting
     Stripe Checkout Session generation and sandbox fulfillment modes.


## Holds and safety boundaries

- Oracle SSH access and v0.8.2 deployment were verified on October 13; no VCN
  changes were required. An intentional nightly VM stop makes SSH unavailable
  until the instance is started again.
- Dashboard authentication is enabled and the administrator account exists.
  Application login is separate from SSH host login. Login-disabled mode is
  localhost-only, not safe shared dashboard access.
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
