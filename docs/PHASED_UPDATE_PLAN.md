# Phased update and publication gates

Status: review and planning. No Oracle deployment or public live-agent access is
authorized by this document. Green offline tests are necessary, not sufficient,
for a release or deployment.

## Privacy and publication boundary

The owner's complete local OpenClaw workspace is private, including nested
source checkouts. Never recursively export it, treat `.gitignore` as an export
allowlist, or publish persona, memory, credentials, logs, backups or client data.
Detailed Echo review remains private. Public work must use a separate checkout
and explicitly approved, sanitized content. Echo and OpenJaw GitHub repositories
are now private; WayaLabs remains public. Historical public copies cannot be
recalled by changing repository visibility.

## Phase 1: CEO orchestrator

1. Preserve and review all pending changes, including source-build preparation.
   Complete removal of unfinished audio code, tests and active setup references;
   retain text chat inside the existing admin panel.
2. Keep explicit scenarios, owner-scoped artifacts, named authentication, CSRF,
   cost reservations and approval separation. Generated code is never executed
   on the dashboard host. Do not weaken authentication for legacy adapters.
3. Run `make check PYTHON=.venv/bin/python`, JavaScript syntax and dependency
   checks, plus a staged source/history secret scan. Review the exact staged
   changes. Commit and push only the reviewed source once every gate passes.
4. Separate the private admin application from all public demonstrations. A
   screenshot is evidence of the UI, not proof of completed business actions.

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

1. Work from a separate public-site checkout outside private operational state.
   Keep OpenClaw and the CEO project clearly distinguished. Replace profile-only
   project destinations with accurate case-study/repository/demo destinations.
2. Remove unsupported performance, production and client-success claims; use
   observed facts and explicitly stated limitations instead.
3. Add a minimal CEO page with a genuine, sanitized dashboard screenshot and a
   guided scenario/chat/output sample. Use reviewed real outputs for a recorded
   sample; label illustrative content as illustrative, never as a live result.
   Step-through playback must support pause/reset and reduced motion. No audio.
4. Prefer a static sampler with no backend, API credentials, private memory,
   admin routes, execution controls or visitor-data persistence. It must not
   fetch artifacts directly from the private dashboard or embed its admin UI.
5. Verify site tests, lint, production build, links, image rendering, keyboard
   access and desktop/mobile screenshots before pushing. Check the Git-linked
   Vercel deployment and deployed routes after a release; a push may auto-deploy.

Limited live CEO chat is a separate later approval: authenticated service
boundary, temporary isolated sessions, bounded inputs/outputs, rate/concurrency
limits, per-session and global spending reservations, redacted structured
errors, retention policy and a kill switch. No admin tools, private memory,
shell, graph launch or external action connectors. Never put keys in the browser.

## Oracle deployment planning, after source releases

A VCN is networking, not a running application or an untrusted-code sandbox.
Existing VCNs/instances have not been inspected. Plan independent private CEO
and Echo services; never copy a complete workstation workspace to either.

1. With explicit authorization, inventory compartments, VCNs, subnets, NSGs,
   instances, OS/images, capacity and existing workloads without changing them.
   Establish costs, backups, versioned releases and rollback targets.
2. Keep admin/gateway listeners private, deny inbound access by default and use
   approved authenticated operator access. Require named authentication before
   sharing the CEO service. Separate service users, storage and credentials.
3. Review TLS, reverse-proxy trust, egress, instance metadata access, least-
   privilege IAM, secret delivery, disk permissions and bounded log retention.
   The CEO durable worker currently requires one server process.
4. Test a candidate release with synthetic data and verify ownership, revocation,
   CSRF, restart recovery, cost ceilings, backup/restore and rollback. Live model
   smoke tests require separately approved bounded spending.
5. Obtain explicit deployment/cutover approval, record artifact commit hashes,
   deploy versioned releases and verify private health before operator cutover.
   Generated-code testing remains a separate disposable isolated runner project;
   see [runner design](ISOLATED_RUNNER.md).

## Current holds

No private workspace export, unreviewed commit/push, public live chat, tester
provisioning, credential rotation, Oracle access, provisioning, deployment or
generated-code execution has been performed as part of this review.
