# Phased update and publication gates

Status: Phase 1 CEO release completed and pushed as `9d0e1c5` on 2026-10-11.
Echo/OpenClaw upgrades are deferred to a separate session at the owner's request.
The Oracle VCN login/SSH-tunnel walkthrough is documentation for connecting to
an existing instance; this documentation update does not connect, provision, or
deploy. Any application deployment is a separate task. Offline tests are
necessary, not sufficient, for deployment.
Phase 3 WayaLabs code is committed locally as `31669c0`; local validation passes,
but this follow-up commit has not been pushed and Vercel has not picked it up.

## Privacy and publication boundary

The owner's complete local OpenClaw workspace is private, including nested
source checkouts. Never recursively export it, treat `.gitignore` as an export
allowlist, or publish persona, memory, credentials, logs, backups or client data.
Detailed Echo review remains private. WayaLabs remains public; work only in its
existing checkout and restrict commits there to reviewed WayaLabs files. Never
publish adjacent OpenClaw state or create another clone.
Echo and OpenJaw repositories are private; historical public copies cannot be
recalled by changing repository visibility.

## Phase 1: CEO orchestrator

Completed and pushed as `9d0e1c5`: preserved text chat, removed unfinished audio
code/tests/setup references, and added approval-gated source-build preparation.
Explicit scenarios, owner-scoped artifacts, named authentication, CSRF, usage
reservations, and approval separation remain. Generated code is not executed on
the dashboard host. `make check` passed with 134 tests; JavaScript, dependency,
and staged-secret checks passed. These checks do not certify live model quality,
source-build correctness, or VCN readiness. The private admin app remains
separate from public demonstrations.

Baseline on October 11, 2026: formatting, lint, consistency, dashboard render and
134 offline tests passed. This does not certify live model quality, source-build
execution or Oracle readiness. See [current handoff](UPGRADE_NEXT_SESSION.md)
and [isolated runner boundaries](ISOLATED_RUNNER.md).

## Phase 2: private OpenClaw / OpenJaw / Echo

1. Resolve source ownership and migration scope in private. Upstream OpenClaw,
   private Echo runtime and an OpenJaw persona starter are distinct components;
   do not merge or delete them based only on similar names.
2. Build an independent private source checkout, excluding operational state.
   Follow the private review's authorization, shell, model-cost, memory-isolation,
   setup and bridge-compatibility gates before enabling remote operation.
3. Document actual interfaces and limitations. Remove unsupported absolute
   safety claims and historical test badges that are not reproducible.
4. Verify offline negative tests, dependency installation, secret exclusions and
   rollback. Push reviewed changes to private repositories only. Do not mutate
   the live gateway merely to synchronize a repository.

## Phase 3: WayaLabs public portal

1. Work only from the existing WayaLabs checkout; do not create a second clone. Keep
   OpenClaw and CEO distinct, and replace profile-only destinations with accurate
   case-study/sampler links.
2. Remove unsupported performance, production and client-success claims; use
   observed facts and explicitly stated limitations instead.
3. Implemented: a static CEO stack/orchestration walkthrough marked as R&D. It
   uses no backend, visitor storage, or live model output; step controls support
   pause/reset and reduced motion. No dashboard screenshot is published because
   the available capture contained stale private context. No audio.
4. Prefer a static sampler with no backend, API credentials, private memory,
   admin routes, execution controls or visitor-data persistence. It must not
   fetch artifacts directly from the private dashboard or embed its admin UI.
5. Local lint, 111 tests, production build, route/Cal.com-link smoke, generated
   social images, and desktop/mobile layout checks passed. Commit `31669c0`
   wires booking CTAs to `cal.com/wayalabs`; it is not pushed and Vercel has not
   deployed it. Push remains held pending the announced upstream Next security
   update and re-audit.

Limited live CEO chat is a separate later approval: authenticated service
boundary, temporary isolated sessions, bounded inputs/outputs, rate/concurrency
limits, per-session and global spending reservations, redacted structured
errors, retention policy and a kill switch. No admin tools, private memory,
shell, graph launch or external action connectors. Never put keys in the browser.

## Oracle VCN access tutorial and deployment boundary

The [Oracle VCN walkthrough](UPGRADE_NEXT_SESSION.md) explains direct SSH login,
bastion login, and optional dashboard tunneling to an existing instance. The
tutorial is available without recording host details in this repository; it
does not provision resources or deploy the app. A VCN is networking, not a
running application or an untrusted-code sandbox.

If application deployment is requested separately, identify the intended
instance and approved access method first. Do not guess a host or transfer the
full workstation repository.

1. Once the target is identified, inventory its OS, running service, version,
   environment configuration presence, listeners, capacity and rollback options
   without reading or printing secret values.
2. Keep the dashboard listener private, deny inbound access by default and use
   approved authenticated operator access. Require named authentication before
   sharing the CEO service. Production refuses auth-disabled mode. Separate
   service users, storage and credentials.
3. Review TLS, reverse-proxy trust, egress, instance metadata access, least-
   privilege IAM, secret delivery, disk permissions and bounded log retention.
   The CEO durable worker currently requires one server process.
4. Test a candidate release with synthetic data and verify ownership, revocation,
   CSRF, restart recovery, cost ceilings, backup/restore and rollback. Live model
   smoke tests require separately approved bounded spending.
5. Before changing the identified server, confirm its backup/rollback point,
   then deploy commit `9d0e1c5` or a newer reviewed commit and verify private
   health before operator cutover.
   Generated-code testing remains a separate disposable isolated runner project;
   see [runner design](ISOLATED_RUNNER.md).

## Current holds

No private workspace export, public live chat, tester provisioning, credential
rotation, live VCN session, provisioning, deployment or generated-code execution
has been performed. Echo/OpenClaw upgrades are deferred; do not change their
local settings or runtime as part of this CEO documentation update.
