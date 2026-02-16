# Artifact Workflow (Real Execution Outputs)

This document describes how agent runs now generate reviewable output artifacts and how operators can inspect them.

## What Changed

- Agent execution responses now include an `artifacts` array with direct URLs to generated files.
- Each run is persisted under `static/generated_outputs/` with a stable run folder.
- The admin dashboard workspace renders a **Generated Files** panel for previews and direct opening.

## Folder Structure

```text
static/generated_outputs/
  <agent_type>/
    <run_id>_<company_slug>/
      bundle.json
      metadata.json
      result.json
      summary.md
      ...agent-specific files...
```

## API Endpoints

- `POST /api/agent/execute/<agent_type>`
- `POST /api/ceo/analyze`
- `GET /api/cfo/report`
- `GET /api/artifacts/runs`
- `GET /api/artifacts/runs/<agent_type>`

## Agent-Specific Output Examples

- **Branding**: logo proposal SVGs, social avatar SVGs, palette CSS tokens, moodboard SVG
- **Web Development**: timeline markdown, Mermaid architecture file, homepage wireframe HTML
- **CFO**: financial report JSON, action plan markdown
- **Content/Campaigns/Legal/MarTech**: workflow markdown outputs aligned to domain deliverables

## Current Capability Notes

- The system now produces concrete, versioned artifacts suitable for internal review and iteration.
- For photorealistic image generation or external publication workflows, integrate dedicated media APIs (for example DALL·E, Stability, or design tooling APIs) and map outputs into this same artifact pipeline.
