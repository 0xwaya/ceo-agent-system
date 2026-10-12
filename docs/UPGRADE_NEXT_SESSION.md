# Oracle VCN access and release handoff: October 12, 2026

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

On the remote instance, create a helper script to activate the virtual
environment and start the single-worker Flask service on port `5001`:

```bash
cat << 'EOF' > /home/ubuntu/start_ceo.sh
#!/usr/bin/env bash
cd /home/ubuntu/apps/ceo-agent-system
source /home/ubuntu/.venvs/ceo-agent-system/bin/activate
exec python app.py
EOF
chmod +x /home/ubuntu/start_ceo.sh
```

To run it in the background on the server:

```bash
nohup /home/ubuntu/start_ceo.sh > /home/ubuntu/apps/ceo-agent-system/app.log 2>&1 &
```

To verify the process and port listener:

```bash
ps aux | grep 'python app.py' | grep -v grep
ss -tulpn | grep 5001
```

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
3. **Executive Action Clarity**:
   - Clear distinction between passive report review and approval-gated actions.
   - Contextual chat drawer with instant agent-switching and thread indicators.

## Holds and safety boundaries

- No live Oracle SSH session, VCN change, or app deployment has been made; this
  walkthrough does not verify host reachability or credentials.
- Dashboard login activation and tester provisioning are separate from SSH host
  login. Login-disabled mode is localhost-only, not safe shared dashboard access.
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
