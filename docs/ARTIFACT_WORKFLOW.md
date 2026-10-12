# Artifact Workflow (Real Execution Outputs)

**Current as of 2026-10-11 (v0.8).** Artifacts are private, owner-scoped outputs
for review; their contents are proposals, not proof that business actions ran.
The root [README](../README.md) is authoritative if this workflow summary differs.

## What Changed

- Durable graph and source-build job responses include artifact descriptors.
- Artifacts are persisted under ignored `data/artifacts/` (or `APP_ARTIFACT_DIR`),
  outside the static web root.
- Authenticated downloads verify owner, allowed path, and SHA-256 receipt. Artifact
  paths are not public static URLs.

## Folder Structure

```text
data/artifacts/generated_outputs/
  <agent_type>/
    <run_id>_<company_slug>/
      bundle.json
      metadata.json
      result.json
      summary.md
      ...agent-specific files...
```

## API Endpoints

- `POST /api/graph/execute` returns `202` and a durable `job_id`.
- `GET /api/jobs/<id>` reports owner-scoped job status and result.
- `GET /api/artifacts/runs` lists only the authenticated owner's artifacts.
- `GET /api/artifacts/file/<path>` is an authenticated, owner-checked download
  and verifies the file hash.
- `POST /api/builds/propose` creates an approval-gated source-build proposal;
  generated code is syntax-checked but never executed on the dashboard host.

## Agent-Specific Output Examples

- **Branding**: logo proposal SVGs, social avatar SVGs, palette CSS tokens, moodboard SVG
- **Web Development**: timeline markdown, Mermaid architecture file, homepage wireframe HTML
- **CFO**: financial report JSON, action plan markdown
- **Content/Campaigns/Legal/MarTech**: workflow markdown outputs aligned to domain deliverables

## Current Capability Notes

- The system produces persisted JSON/Markdown artifacts suitable for internal review and iteration.
- Source-build files are separate deliverables; a prepared runner request is not
  test execution. See [isolated runner boundaries](ISOLATED_RUNNER.md).
- For photorealistic image generation or external publication workflows, integrate dedicated media APIs (for example DALL·E, Stability, or design tooling APIs) and map outputs into this same artifact pipeline.
