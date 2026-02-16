"""Artifact persistence and discovery for agent execution outputs."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
from uuid import uuid4


class ArtifactService:
    """Persist generated agent outputs to static files for UI preview/review."""

    def __init__(self, static_root: Optional[Path] = None):
        if static_root is None:
            static_root = Path(__file__).resolve().parents[1] / "static"
        self.static_root = Path(static_root)
        self.output_root = self.static_root / "generated_outputs"
        self.output_root.mkdir(parents=True, exist_ok=True)

    def persist_agent_execution(
        self,
        *,
        agent_type: str,
        agent_name: str,
        task: str,
        company_info: Dict[str, Any],
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Persist a full execution bundle and return artifact descriptors."""
        run_id = self._build_run_id()
        agent_slug = self._slugify(agent_type or agent_name or "agent")
        company_slug = self._slugify(
            company_info.get("dba_name")
            or company_info.get("company_name")
            or company_info.get("name")
            or "company"
        )

        run_dir = self.output_root / agent_slug / f"{run_id}_{company_slug}"
        run_dir.mkdir(parents=True, exist_ok=True)

        artifacts: List[Dict[str, Any]] = []

        metadata = {
            "run_id": run_id,
            "agent_type": agent_type,
            "agent_name": agent_name,
            "task": task,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "company": {
                "name": company_info.get("name") or company_info.get("company_name"),
                "dba_name": company_info.get("dba_name"),
                "industry": company_info.get("industry"),
                "location": company_info.get("location"),
            },
        }

        metadata_path = run_dir / "metadata.json"
        self._write_json(metadata_path, metadata)
        artifacts.append(self._artifact_entry(metadata_path, "Run Metadata", "json"))

        result_path = run_dir / "result.json"
        self._write_json(result_path, result)
        artifacts.append(self._artifact_entry(result_path, "Execution Result", "json"))

        summary_path = run_dir / "summary.md"
        self._write_text(summary_path, self._build_summary_markdown(metadata, result))
        artifacts.append(self._artifact_entry(summary_path, "Summary", "markdown"))

        deliverables = result.get("deliverables") or []
        if isinstance(deliverables, list) and deliverables:
            deliverables_path = run_dir / "deliverables.md"
            self._write_text(
                deliverables_path, self._build_list_markdown("Deliverables", deliverables)
            )
            artifacts.append(self._artifact_entry(deliverables_path, "Deliverables", "markdown"))

        artifacts.extend(self._create_domain_artifacts(agent_type, result, run_dir))

        bundle = {
            "run_id": run_id,
            "agent_type": agent_type,
            "agent_name": agent_name,
            "directory": str(run_dir.relative_to(self.static_root)),
            "directory_url": f"/static/{run_dir.relative_to(self.static_root).as_posix()}",
            "artifacts": artifacts,
        }

        bundle_path = run_dir / "bundle.json"
        self._write_json(bundle_path, bundle)

        return bundle

    def list_artifact_runs(
        self, agent_type: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List persisted runs (newest first), optionally by agent type."""
        run_dirs = list(self.output_root.glob("*/*"))

        if agent_type:
            slug = self._slugify(agent_type)
            run_dirs = [path for path in run_dirs if path.parent.name == slug]

        run_dirs = [path for path in run_dirs if path.is_dir()]
        run_dirs.sort(key=lambda item: item.stat().st_mtime, reverse=True)

        runs: List[Dict[str, Any]] = []
        for run_dir in run_dirs[: max(limit, 1)]:
            bundle_path = run_dir / "bundle.json"
            metadata_path = run_dir / "metadata.json"
            if bundle_path.exists():
                try:
                    runs.append(json.loads(bundle_path.read_text(encoding="utf-8")))
                    continue
                except Exception:
                    pass

            if metadata_path.exists():
                try:
                    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                except Exception:
                    metadata = {}
            else:
                metadata = {}

            runs.append(
                {
                    "run_id": metadata.get("run_id", run_dir.name),
                    "agent_type": metadata.get("agent_type", run_dir.parent.name),
                    "agent_name": metadata.get("agent_name", run_dir.parent.name),
                    "directory": str(run_dir.relative_to(self.static_root)),
                    "directory_url": f"/static/{run_dir.relative_to(self.static_root).as_posix()}",
                    "artifacts": self._discover_files(run_dir),
                }
            )

        return runs

    def _create_domain_artifacts(
        self, agent_type: str, result: Dict[str, Any], run_dir: Path
    ) -> List[Dict[str, Any]]:
        artifacts: List[Dict[str, Any]] = []

        if agent_type == "branding":
            concepts = result.get("design_concepts") or []
            for idx, concept in enumerate(concepts, start=1):
                concept_name = concept.get("concept_name", f"Concept {idx}")
                concept_description = concept.get("description", "No description provided")
                svg_path = run_dir / f"logo_proposal_{idx:02d}.svg"
                svg_markup = self._build_logo_preview_svg(
                    title=concept_name,
                    subtitle=concept_description,
                    variant_index=idx,
                )
                self._write_text(svg_path, svg_markup)
                artifacts.append(
                    self._artifact_entry(
                        svg_path, f"Logo Proposal {idx:02d}", "image", "image/svg+xml"
                    )
                )

                icon_path = run_dir / f"logo_avatar_{idx:02d}.svg"
                self._write_text(icon_path, self._build_logo_avatar_svg(concept_name, idx))
                artifacts.append(
                    self._artifact_entry(
                        icon_path, f"Social Avatar {idx:02d}", "image", "image/svg+xml"
                    )
                )

            palette_path = run_dir / "brand_palette.css"
            self._write_text(
                palette_path,
                "\n".join(
                    [
                        ":root {",
                        "  --brand-marble-white: #F8F8F6;",
                        "  --brand-brushed-gold: #D4AF37;",
                        "  --brand-charcoal-black: #121212;",
                        "  --brand-slate-gray: #5F6772;",
                        "  --brand-midnight-navy: #1C2333;",
                        "}",
                    ]
                ),
            )
            artifacts.append(
                self._artifact_entry(palette_path, "Brand Palette Tokens", "file", "text/css")
            )

            moodboard_path = run_dir / "brand_moodboard.svg"
            self._write_text(moodboard_path, self._build_brand_moodboard_svg())
            artifacts.append(
                self._artifact_entry(moodboard_path, "Brand Moodboard", "image", "image/svg+xml")
            )

        if agent_type == "web_development":
            phases = result.get("timeline") or result.get("development_phases") or []
            if phases:
                timeline_path = run_dir / "implementation_timeline.md"
                rendered = []
                for idx, phase in enumerate(phases, start=1):
                    if isinstance(phase, dict):
                        phase_label = phase.get("phase", phase.get("week", f"Phase {idx}"))
                        phase_description = phase.get(
                            "description", phase.get("deliverable", "Milestone")
                        )
                        rendered.append(f"{idx}. {phase_label}: {phase_description}")
                    else:
                        rendered.append(f"{idx}. {phase}")
                self._write_text(
                    timeline_path, self._build_list_markdown("Implementation Timeline", rendered)
                )
                artifacts.append(
                    self._artifact_entry(timeline_path, "Implementation Timeline", "markdown")
                )

            architecture_path = run_dir / "architecture_diagram.mmd"
            self._write_text(architecture_path, self._build_web_architecture_mermaid(result))
            artifacts.append(
                self._artifact_entry(
                    architecture_path, "Architecture Diagram (Mermaid)", "file", "text/plain"
                )
            )

            homepage_path = run_dir / "homepage_wireframe.html"
            self._write_text(homepage_path, self._build_homepage_wireframe_html(result))
            artifacts.append(
                self._artifact_entry(homepage_path, "Homepage Wireframe", "file", "text/html")
            )

        if agent_type == "cfo" and result.get("report"):
            report_path = run_dir / "financial_report.json"
            self._write_json(report_path, result.get("report"))
            artifacts.append(self._artifact_entry(report_path, "Financial Report", "json"))

            recommendations = result.get("report", {}).get("cfo_recommendations") or []
            if recommendations:
                plan_path = run_dir / "financial_action_plan.md"
                self._write_text(
                    plan_path, self._build_list_markdown("CFO Action Plan", recommendations)
                )
                artifacts.append(
                    self._artifact_entry(plan_path, "Financial Action Plan", "markdown")
                )

        if agent_type == "content":
            assets = result.get("deliverables") or result.get("assets") or []
            if assets:
                calendar_path = run_dir / "content_plan.md"
                self._write_text(
                    calendar_path, self._build_list_markdown("Content Deliverables", assets)
                )
                artifacts.append(self._artifact_entry(calendar_path, "Content Plan", "markdown"))

        if agent_type == "campaigns":
            campaign_items = result.get("deliverables") or result.get("timeline") or []
            if campaign_items:
                campaign_path = run_dir / "campaign_execution_plan.md"
                self._write_text(
                    campaign_path,
                    self._build_list_markdown("Campaign Execution Plan", campaign_items),
                )
                artifacts.append(
                    self._artifact_entry(campaign_path, "Campaign Execution Plan", "markdown")
                )

        if agent_type == "legal":
            legal_items = result.get("deliverables") or []
            if legal_items:
                checklist_path = run_dir / "legal_checklist.md"
                self._write_text(
                    checklist_path, self._build_list_markdown("Legal Checklist", legal_items)
                )
                artifacts.append(
                    self._artifact_entry(checklist_path, "Legal Checklist", "markdown")
                )

        if agent_type == "martech":
            stack_items = result.get("deliverables") or result.get("tech_stack") or []
            if stack_items:
                stack_path = run_dir / "martech_stack.md"
                self._write_text(
                    stack_path, self._build_list_markdown("MarTech Stack", stack_items)
                )
                artifacts.append(self._artifact_entry(stack_path, "MarTech Stack", "markdown"))

        return artifacts

    def _build_summary_markdown(self, metadata: Dict[str, Any], result: Dict[str, Any]) -> str:
        status = result.get("status", "executed")
        budget_used = result.get("budget_used", 0)
        timeline_days = result.get("timeline_days") or result.get("timeline") or "N/A"
        company_name = (
            metadata.get("company", {}).get("dba_name")
            or metadata.get("company", {}).get("name")
            or "Company"
        )

        return "\n".join(
            [
                f"# {metadata.get('agent_name', 'Agent')} Execution Summary",
                "",
                f"- Run ID: {metadata.get('run_id', 'n/a')}",
                f"- Company: {company_name}",
                f"- Status: {status}",
                f"- Budget Used: ${budget_used}",
                f"- Timeline: {timeline_days}",
                "",
                "## Task",
                metadata.get("task", "No task provided"),
                "",
                "## Notes",
                (
                    "Artifacts in this folder can be reviewed directly "
                    "from the dashboard output panel."
                ),
            ]
        )

    def _build_list_markdown(self, title: str, items: List[Any]) -> str:
        rendered_items = []
        for item in items:
            if isinstance(item, dict):
                rendered_items.append(f"- {json.dumps(item, ensure_ascii=False)}")
            else:
                rendered_items.append(f"- {item}")
        return "\n".join([f"# {title}", "", *rendered_items])

    def _build_logo_preview_svg(self, title: str, subtitle: str, variant_index: int = 1) -> str:
        safe_title = self._xml_escape(title)
        safe_subtitle = self._xml_escape(subtitle)
        monogram = ["SC", "SS", "AG", "LS"][max(0, (variant_index - 1) % 4)]
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'width="1200" height="800" viewBox="0 0 1200 800">'
            '<defs><linearGradient id="gold" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0%" stop-color="#D4AF37"/><stop offset="100%" stop-color="#B8860B"/>'
            "</linearGradient></defs>"
            '<rect width="1200" height="800" fill="#0F0F10"/>'
            '<rect x="80" y="80" width="1040" height="640" rx="24" fill="#F8F8F6"/>'
            '<circle cx="220" cy="220" r="84" fill="none" stroke="url(#gold)" stroke-width="12"/>'
            f'<text x="220" y="238" text-anchor="middle" '
            f'font-size="48" font-weight="700" fill="#111111">{monogram}</text>'
            f'<text x="340" y="220" font-size="40" font-weight="700" '
            f'fill="#111111">{safe_title}</text>'
            f'<text x="340" y="276" font-size="24" fill="#333333">{safe_subtitle}</text>'
            '<text x="100" y="690" font-size="20" fill="#666666">'
            "AI-generated proposal preview artifact"
            "</text>"
            "</svg>"
        )

    def _build_logo_avatar_svg(self, title: str, variant_index: int) -> str:
        initials = "".join([part[:1].upper() for part in title.split()[:2]]) or "SC"
        ring_size = 10 + (variant_index % 3)
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'width="512" height="512" viewBox="0 0 512 512">'
            '<rect width="512" height="512" rx="96" fill="#121212"/>'
            f'<circle cx="256" cy="256" r="172" fill="none" '
            f'stroke="#D4AF37" stroke-width="{ring_size}"/>'
            f'<text x="256" y="286" text-anchor="middle" font-size="124" '
            f'font-weight="700" fill="#F8F8F6">{self._xml_escape(initials)}</text>'
            "</svg>"
        )

    def _build_brand_moodboard_svg(self) -> str:
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'width="1200" height="700" viewBox="0 0 1200 700">'
            '<rect width="1200" height="700" fill="#101113"/>'
            '<rect x="70" y="70" width="1060" height="560" rx="24" fill="#F8F8F6"/>'
            '<rect x="120" y="150" width="220" height="220" fill="#F8F8F6" stroke="#D4AF37"/>'
            '<rect x="360" y="150" width="220" height="220" fill="#D4AF37"/>'
            '<rect x="600" y="150" width="220" height="220" fill="#121212"/>'
            '<rect x="840" y="150" width="220" height="220" fill="#5F6772"/>'
            '<text x="120" y="450" font-size="44" fill="#121212" '
            'font-weight="700">SurfaceCraft Studio</text>'
            '<text x="120" y="495" font-size="26" fill="#2E3138">'
            "Marble White / Brushed Gold / Charcoal Black"
            "</text>"
            '<text x="120" y="560" font-size="22" fill="#555B66">'
            "Luxury material brand moodboard • AI generated review board"
            "</text>"
            "</svg>"
        )

    def _build_web_architecture_mermaid(self, result: Dict[str, Any]) -> str:
        tech_stack = result.get("tech_stack") or []
        stack_label = ", ".join([str(item) for item in tech_stack[:4]]) or "Web Stack"
        return "\n".join(
            [
                "flowchart LR",
                "    U[Users] --> W[Web App]",
                "    W --> A[API Layer]",
                "    A --> DB[(Data Store)]",
                "    A --> S[Services & Integrations]",
                f"    W -.-> T[{stack_label}]",
            ]
        )

    def _build_homepage_wireframe_html(self, result: Dict[str, Any]) -> str:
        deliverables = result.get("deliverables") or []
        highlights = "".join(
            [f"<li>{self._xml_escape(str(item))}</li>" for item in deliverables[:5]]
        )
        if not highlights:
            highlights = (
                "<li>Core value proposition</li><li>Primary CTA</li><li>Service highlights</li>"
            )
        return "\n".join(
            [
                "<!DOCTYPE html>",
                '<html lang="en">',
                "<head>",
                '  <meta charset="UTF-8" />',
                '  <meta name="viewport" content="width=device-width, initial-scale=1.0" />',
                "  <title>Generated Homepage Wireframe</title>",
                (
                    "  <style>body{font-family:Arial,sans-serif;background:#0f1115;"
                    "color:#f5f7fa;margin:0;padding:24px;}"
                    "section{border:1px solid #2b303b;border-radius:12px;padding:16px;"
                    "margin-bottom:16px;background:#171b22;}"
                    "h1,h2{margin:0 0 10px;}"
                    "button{background:#2563eb;color:#fff;border:none;border-radius:8px;"
                    "padding:10px 16px;}</style>"
                ),
                "</head>",
                "<body>",
                (
                    "  <section><h1>Hero Section</h1>"
                    "<p>Premium positioning statement and CTA.</p>"
                    "<button>Book Consultation</button></section>"
                ),
                "  <section><h2>Execution Highlights</h2><ul>",
                f"  {highlights}",
                "  </ul></section>",
                (
                    "  <section><h2>Proof & Trust</h2>"
                    "<p>Portfolio, testimonials, and certifications.</p></section>"
                ),
                "</body>",
                "</html>",
            ]
        )

    def _artifact_entry(
        self, path: Path, title: str, artifact_type: str, mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        relative = path.relative_to(self.static_root).as_posix()
        extension = path.suffix.lower().lstrip(".")
        return {
            "title": title,
            "type": artifact_type,
            "extension": extension,
            "mime_type": mime_type or self._guess_mime(extension),
            "path": relative,
            "url": f"/static/{relative}",
        }

    def _discover_files(self, run_dir: Path) -> List[Dict[str, Any]]:
        files = []
        for file_path in sorted(run_dir.iterdir()):
            if not file_path.is_file():
                continue
            if file_path.name == "bundle.json":
                continue
            files.append(
                self._artifact_entry(
                    file_path,
                    file_path.name,
                    "image"
                    if file_path.suffix.lower() in {".svg", ".png", ".jpg", ".jpeg", ".webp"}
                    else "file",
                )
            )
        return files

    def _build_run_id(self) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        return f"{timestamp}-{uuid4().hex[:8]}"

    def _write_json(self, path: Path, data: Any) -> None:
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
        )

    def _write_text(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    def _slugify(self, value: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", "-", (value or "").strip().lower())
        return normalized.strip("-") or "agent"

    def _xml_escape(self, value: str) -> str:
        return (
            str(value or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def _guess_mime(self, extension: str) -> str:
        mapping = {
            "json": "application/json",
            "md": "text/markdown",
            "svg": "image/svg+xml",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "webp": "image/webp",
            "html": "text/html",
            "css": "text/css",
            "mmd": "text/plain",
            "txt": "text/plain",
        }
        return mapping.get(extension.lower(), "application/octet-stream")


artifact_service = ArtifactService()
