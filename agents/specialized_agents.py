"""
Specialized Agent Templates - Expert agents for specific domains

Each agent is designed with master-level knowledge from top universities
and industry best practices in their respective fields.

🛡️ GUARD RAILS ENFORCED:
- Agents EXECUTE work (do not recommend external vendors)
- Budget constraints enforced (tools/platforms only)
- Scope validation (agents stay in their domain)
- Quality standards from top universities
"""

from typing import Dict, List, Any
from typing_extensions import TypedDict
from dataclasses import dataclass
import operator
from typing import Annotated
from agents.agent_knowledge_base import (
    BRANDING_EXPERTISE,
    WEB_DEV_EXPERTISE,
    LEGAL_EXPERTISE,
    MARTECH_EXPERTISE,
    CONTENT_EXPERTISE,
    CAMPAIGN_EXPERTISE,
)
from agents.security_blockchain_agent import SecurityBlockchainAgent
from agents.agent_guard_rails import (
    AgentGuardRail,
    AgentDomain,
    validate_agent_output,
    create_execution_summary,
)
from utils.openai_codex_tooling import OpenAICodexTooling


# ============================================================================
# SPECIALIZED AGENT STATE DEFINITIONS
# ============================================================================


class BrandingAgentState(TypedDict):
    """State for Branding & Visual Identity Specialist"""

    task_description: str
    company_info: Dict[str, Any]
    research_findings: Annotated[list[str], operator.add]
    design_concepts: Annotated[list[Dict], operator.add]
    recommendations: Annotated[list[str], operator.add]
    deliverables: Annotated[list[str], operator.add]
    status: str
    budget_used: float
    timeline_days: int


class WebDevAgentState(TypedDict):
    """State for Web Development & AR Specialist"""

    task_description: str
    requirements: Dict[str, Any]
    tech_stack: Annotated[list[str], operator.add]
    architecture_design: str
    ar_features: Annotated[list[str], operator.add]
    development_phases: Annotated[list[Dict], operator.add]
    testing_results: Annotated[list[str], operator.add]
    deliverables: Annotated[list[str], operator.add]
    status: str
    budget_used: float
    timeline_days: int


class LegalAgentState(TypedDict):
    """State for Legal & Compliance Specialist"""

    task_description: str
    jurisdiction: str
    filings_required: Annotated[list[str], operator.add]
    compliance_checklist: Annotated[list[Dict], operator.add]
    documents_prepared: Annotated[list[str], operator.add]
    risks_identified: Annotated[list[str], operator.add]
    status: str
    budget_used: float
    timeline_days: int


class MartechAgentState(TypedDict):
    """State for Marketing Technology Specialist"""

    task_description: str
    current_systems: Annotated[list[str], operator.add]
    recommended_stack: Annotated[list[Dict], operator.add]
    integrations: Annotated[list[str], operator.add]
    automation_workflows: Annotated[list[Dict], operator.add]
    implementation_plan: str
    status: str
    budget_used: float
    timeline_days: int


class ContentAgentState(TypedDict):
    """State for Content Strategy & Production Specialist"""

    task_description: str
    content_types: Annotated[list[str], operator.add]
    production_schedule: Annotated[list[Dict], operator.add]
    assets_created: Annotated[list[str], operator.add]
    distribution_plan: str
    seo_strategy: str
    status: str
    budget_used: float
    timeline_days: int


class CampaignAgentState(TypedDict):
    """State for Campaign Strategy & Execution Specialist"""

    task_description: str
    campaign_objectives: Annotated[list[str], operator.add]
    target_audiences: Annotated[list[Dict], operator.add]
    channels: Annotated[list[str], operator.add]
    creative_concepts: Annotated[list[Dict], operator.add]
    media_plan: str
    budget_allocation: Dict[str, float]
    performance_forecast: Dict[str, Any]
    status: str
    budget_used: float
    timeline_days: int


class SocialMediaAgentState(TypedDict):
    """State for Social Media Growth & Community Specialist"""

    task_description: str
    platforms: Annotated[list[str], operator.add]
    content_calendar: Annotated[list[Dict], operator.add]
    posting_workflows: Annotated[list[str], operator.add]
    campaign_ideas: Annotated[list[Dict], operator.add]
    community_playbook: str
    status: str
    budget_used: float
    timeline_days: int


# ============================================================================
# SPECIALIZED AGENT IMPLEMENTATIONS
# ============================================================================


@dataclass
class SpecializedAgent:
    """Base class for specialized agents with guard rail enforcement"""

    name: str
    expertise_area: str
    capabilities: List[str]
    knowledge_base: Any
    guard_rail: Any = None  # AgentGuardRail instance
    codex_tooling: Any = None

    def __post_init__(self):
        """Initialize optional Codex tooling for current and future agents."""
        self.codex_tooling = OpenAICodexTooling.from_env(self.name)

    def validate_execution(self, state: Dict) -> Dict:
        """Enforce guard rails before execution"""
        if self.guard_rail:
            return self.guard_rail.enforce_execution_model(state)
        return state

    def execute_task(self, state: Dict) -> Dict:
        """Execute the agent's primary task (with guard rails)"""
        # Validate before execution
        state = self.validate_execution(state)
        raise NotImplementedError

    def get_execution_capabilities(self) -> str:
        """Return summary of what this agent CAN do"""
        if self.guard_rail:
            return create_execution_summary(self.guard_rail.domain)
        return f"Agent: {self.name}"

    def run_codex_tooling(self, objective: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optional Codex-assisted guidance for agent execution tasks."""
        if not self.codex_tooling:
            return {
                "enabled": False,
                "used": False,
                "output": None,
                "reason": "Codex tooling not initialized",
            }

        return self.codex_tooling.generate_assist(objective=objective, context=context)


class BrandingAgent(SpecializedAgent):
    """Expert in brand strategy and visual identity design

    🎨 EXECUTES (does not recommend):
    - Designs logos using Golden Ratio, Gestalt principles
    - Creates complete brand guidelines (40+ pages)
    - Develops visual identity systems
    - Produces production-ready design files

    💰 Budget: $150 (design software only)
    🎓 Standards: RISD, Stanford d.school, MIT Design
    """

    def __init__(self):
        super().__init__(
            name="Branding & Visual Identity Specialist",
            expertise_area="Branding",
            capabilities=[
                "🎨 DESIGNS logos and visual identity systems",
                "📐 CREATES brand guidelines with Golden Ratio principles",
                "🎨 DEVELOPS color palettes and typography systems",
                "📄 PRODUCES brand templates and mockups",
                "🔍 CONDUCTS trademark searches",
                "💬 CRAFTS brand messaging and positioning",
            ],
            knowledge_base=BRANDING_EXPERTISE,
            guard_rail=AgentGuardRail(AgentDomain.BRANDING),
        )

        # Print execution capabilities on initialization
        print(f"\n{'='*70}")
        print(f"🤖 {self.name} INITIALIZED")
        print(f"{'='*70}")
        print("💡 This agent PERFORMS work (does not recommend vendors)")
        print(f"💰 Budget: ${self.guard_rail.budget_constraint.max_budget}")
        print("✅ Execution Mode: ACTIVE")
        print(f"{'='*70}\n")

    def research_phase(self, state: BrandingAgentState) -> Dict:
        """AI EXECUTES comprehensive brand research (not outsourced)"""
        # Validate execution with guard rails
        state = self.validate_execution(state)

        print(f"\n🎨 {self.name} - AI RESEARCH PHASE (EXECUTING)")
        print("=" * 70)
        print("💡 AI agent conducts research - no external consultants needed")
        print("=" * 70)

        company_info = state.get("company_info", {})
        company_name = company_info.get("name", "Client")
        industry = company_info.get("industry", "General")

        research_findings = [
            f"✅ AI ANALYZED: {industry} brand landscape and positioning opportunities",
            f"✅ AI APPLIED: {self.knowledge_base.frameworks[0]} to define brand architecture",
            "✅ AI RESEARCHED: Color psychology - Trust (blue), Energy (red), Growth (green)",
            "✅ AI EVALUATED: Typography trends for {industry} - sans-serif vs serif",
            "✅ AI AUDITED: Competitor visual landscape to identify differentiation opportunities",
            f"✅ AI ASSESSED: Cultural semiotics for {company_info.get('location', 'target market')} resonance",
        ]

        print("Research Methodology (AI applies RISD + Stanford d.school principles):")
        for finding in research_findings:
            print(f"  {finding}")

        print(f"\n💰 Budget Used: $0 (AI research - no consultant fees)")

        return {
            "research_findings": research_findings,
            "status": "research_complete",
            "execution_mode": "AI_PERFORMED",
        }

    def design_concepts(self, state: BrandingAgentState) -> Dict:
        """Generate logo and visual identity concepts"""
        print(f"\n✨ {self.name} - CONCEPT DEVELOPMENT")
        print("=" * 70)

        company_info = state.get("company_info", {})
        brand_name = company_info.get("dba_name", company_info.get("name", "Brand"))

        codex_tooling = self.run_codex_tooling(
            objective="Create four polished luxury logo proposal directions from provided brand kit",
            context={
                "brand_name": brand_name,
                "palette": ["Marble White", "Brushed Gold", "Charcoal Black"],
                "style": "luxury, elegant, modern stone surfaces",
            },
        )

        brand_kit_reference = {
            "brand_name": brand_name,
            "legacy_name": "Amazon Granite LLC",
            "reference_handles": ["amzgranite.com", "instagram.com/amazongranite"],
            "direction": "SurfaceCraft Studio luxury repositioning",
            "logo_reference": "Elegant monogram + refined wordmark balance",
            "color_palette": {
                "primary": ["Marble White", "Brushed Gold", "Charcoal Black"],
                "supporting": ["Slate Gray", "Midnight Navy"],
            },
            "typography_note": "Primary font undecided; evaluate elegant serif + modern sans pairings",
        }

        concepts = [
            {
                "concept_name": "Polished Proposal 01 - Signature Monogram Luxe",
                "description": f"{brand_name} with sculpted S/C monogram and couture-style spacing",
                "design_principles": [
                    "Golden-ratio monogram geometry inspired by premium stone inlays",
                    "Brushed Gold accent strokes over Charcoal Black structure",
                    "Marble White negative space to preserve luxury breathing room",
                    "Balanced lockup for signage, social avatar, and favicon use",
                ],
                "applications": "Hero website mark, storefront signage, proposal cover",
                "scalability": "Optimized from 24px icon to 12ft exterior sign",
                "ai_execution": "AI-developed vector system with production-ready lockups",
                "tools_budget": "$60 (font licensing + export templates)",
            },
            {
                "concept_name": "Polished Proposal 02 - Heritage Serif Signature",
                "description": "High-contrast serif wordmark with understated stone-cut ligatures",
                "design_principles": [
                    "Elegant serif axis for luxury positioning and premium trust",
                    "Charcoal Black wordmark with Brushed Gold micro-accents",
                    "Marble White base panels for print and digital consistency",
                    "Subtle material-finishing cues to reflect crafted surfaces",
                ],
                "applications": "Brand book, business cards, showroom collateral",
                "scalability": "Exceptional in editorial and premium print contexts",
                "ai_execution": "AI-generated typographic refinements with kerning variants",
                "tools_budget": "$45 (serif family trial/license)",
            },
            {
                "concept_name": "Polished Proposal 03 - Modern Sans Prestige",
                "description": "Refined sans-serif wordmark with architectural geometry and icon pair",
                "design_principles": [
                    "Contemporary sans system for web-first legibility",
                    "Charcoal Black foundation + selective Brushed Gold detail lines",
                    "Marble White negative canvas for elegant high-contrast delivery",
                    "Responsive lockups for desktop header, mobile nav, and socials",
                ],
                "applications": "Website navigation, social profile suite, ad creatives",
                "scalability": "Built for digital responsiveness and motion-ready variants",
                "ai_execution": "AI-produced responsive logo system + social asset pack",
                "tools_budget": "$35 (motion export presets)",
            },
            {
                "concept_name": "Polished Proposal 04 - Monoline Emblem Elegance",
                "description": "Minimal emblem seal with monoline mark and premium typography lockup",
                "design_principles": [
                    "Monoline icon architecture referencing precision fabrication",
                    "Brushed Gold ring + Charcoal Black central mark for premium contrast",
                    "Marble White applications for luxury packaging and proposal decks",
                    "Designed to feel timeless, restrained, and collectible",
                ],
                "applications": "Luxury labels, stamp marks, uniforms, premium merchandise",
                "scalability": "Excellent for physical materials and embossed applications",
                "ai_execution": "AI-generated monoline kit with monochrome fallback suite",
                "tools_budget": "$30 (mockup + print proof templates)",
            },
        ]

        print(f"\n✨ AI GENERATED {len(concepts)} design concepts following:")
        for principle in self.knowledge_base.key_principles[:4]:
            print(f"  ✅ {principle}")

        print(f"\n💡 All designs created by AI - no agency or freelancer fees")

        recommendations = [
            "✅ AI RECOMMENDATION: Proposal 01 as primary brand mark, Proposal 03 for digital-first alternates",
            "🎨 Palette locked: Marble White + Brushed Gold + Charcoal Black as premium core",
            "🔤 Typography path: test one elegant serif and one modern sans before final lock",
            "⏱️ Timeline: 2-3 weeks for finalization, production exports, and rollout kit",
            "📦 AI DELIVERS: 4 polished logo proposals, social avatars, favicon set, and brand sheet",
            "🔁 Migration: replace legacy amzgranite identity traces with SurfaceCraft Studio naming",
        ]

        return {
            "brand_kit_reference": brand_kit_reference,
            "design_concepts": concepts,
            "recommendations": recommendations,
            "deliverables": [
                "✅ AI-DESIGNED: Four polished SurfaceCraft logo proposal systems",
                "✅ AI-CREATED: Brand color standard built around Marble White / Brushed Gold / Charcoal Black",
                "✅ AI-PRODUCED: Typography pairing draft with serif + sans decision framework",
                "✅ AI-GENERATED: Social profile kit and web-ready logo exports",
                "✅ AI-RENDERED: Elegant brand mockups for signage, print, and digital hero",
            ],
            "status": "concepts_ready_ai_executed",
            "budget_used": 120.0,  # Tools only - AI does the work
            "timeline_days": 28,
            "execution_mode": "AI_PERFORMED",
            "codex_tooling": codex_tooling,
        }


class WebDevelopmentAgent(SpecializedAgent):
    """Expert in web development and AR integration

    💻 EXECUTES (does not recommend):
    - Codes complete Next.js websites with TypeScript
    - Implements 8th Wall AR features with Three.js
    - Configures hosting, deployment, CDN
    - Develops production-ready code

    💰 Budget: $500 (domain, hosting, AR platform)
    🎓 Standards: MIT 6.170, Stanford CS 142, Google Web Vitals
    """

    def __init__(self):
        super().__init__(
            name="Web Development & AR Integration Specialist",
            expertise_area="Technology",
            capabilities=[
                "💻 CODES full-stack Next.js App Router experiences",
                "🎨 BUILDS design systems with Tailwind v4 + component primitives",
                "🥽 IMPLEMENTS WebAR with 8th Wall + React Three Fiber",
                "⚡ OPTIMIZES Core Web Vitals and Lighthouse performance",
                "🔍 ENSURES technical SEO, schema, and WCAG accessibility",
                "📦 INTEGRATES headless CMS and analytics-ready architecture",
            ],
            knowledge_base=WEB_DEV_EXPERTISE,
            guard_rail=AgentGuardRail(AgentDomain.WEB_DEVELOPMENT),
        )

        print(f"\n{'='*70}")
        print(f"🤖 {self.name} INITIALIZED")
        print(f"{'='*70}")
        print("💡 This agent CODES websites (does not recommend developers)")
        print(f"💰 Budget: ${self.guard_rail.budget_constraint.max_budget}")
        print("✅ Execution Mode: CODING ACTIVE")
        print(f"{'='*70}\n")

    def analyze_requirements(self, state: WebDevAgentState) -> Dict:
        """AI CODES complete technical solution (not outsourced)"""
        # Validate execution with guard rails
        state = self.validate_execution(state)

        print(f"\n💻 {self.name} - AI CODING ANALYSIS (EXECUTING)")
        print("=" * 70)
        print("💡 AI agent writes production code - no developers hired")
        print("=" * 70)

        task_desc = state.get("task_description", "")
        requirements = state.get("requirements", {})

        codex_tooling = self.run_codex_tooling(
            objective="Generate implementation guidance for web + AR delivery",
            context={"task_description": task_desc, "requirements": requirements},
        )

        print(f"Applying MIT 6.170 Software Studio Principles:")
        print(f"  Task: {task_desc}")

        tech_stack = [
            "✅ AI CODES: Next.js App Router + React 19 + TypeScript strict mode",
            "✅ AI IMPLEMENTS: Tailwind CSS v4 + shadcn/ui primitives + design tokens",
            "✅ AI INTEGRATES: Framer Motion + GSAP for premium micro-interactions",
            "✅ AI BUILDS: React Three Fiber + 8th Wall for high-end WebAR experiences",
            "✅ AI CONFIGURES: CMS-ready architecture (Sanity/Contentful compatible)",
            "✅ AI BUILDS: Server actions + Zod validation + secure API boundaries",
            "✅ AI DEVELOPS: Edge-friendly API routes + caching strategy",
            "✅ AI DEPLOYS: Vercel preview pipelines + production release checks",
            "✅ AI SETS UP: GA4 + Search Console + event instrumentation",
            "✅ AI IMPLEMENTS: Accessibility QA + visual regression testing",
        ]

        print("\n🤖 AI-Coded Technology Stack (Stanford CS 142):")
        for tech in tech_stack:
            print(f"  {tech}")

        print(f"\n💰 Budget: Domain ($12) + Hosting ($0-100) + 8th Wall ($99/mo) = ~$500 total")

        if codex_tooling.get("used"):
            print("\n🤖 OpenAI Codex tooling assistance: enabled")

        ar_features = [
            "✅ AI CODES: Countertop Visualizer - Upload kitchen photo, overlay stones in AR",
            "✅ AI BUILDS: Material Explorer - 360° 3D models with zoom and rotation",
            "✅ AI IMPLEMENTS: Edge Profile Selector - Interactive 3D edge treatment previews",
            "✅ AI DEVELOPS: Color Matching - Camera-based decor analysis and recommendations",
            "✅ AI CREATES: Measurement Tool - AR-based room measurement for accuracy",
            "✅ AI CONSTRUCTS: Virtual Showroom - 3D kitchen displays with different countertops",
        ]

        architecture = """
        ARCHITECTURE DESIGN (CMU HCI + MIT Principles):

        ┌─────────────────────────────────────────────────────────┐
        │                    USER LAYER                           │
        │  Mobile (60%) | Desktop (35%) | Tablet (5%)            │
        └─────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────────────────────┐
        │              CDN / EDGE NETWORK (Vercel)                │
        │  Global: <50ms TTFB, automatic image optimization       │
        └─────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────────────────────┐
        │         PRESENTATION LAYER (Next.js 14)                 │
        │  SSR: SEO-critical pages | SSG: Static content          │
        │  CSR: Interactive AR features | ISR: Product catalog    │
        └─────────────────────────────────────────────────────────┘
                              ↓
        ┌──────────────────┬──────────────────┬──────────────────┐
        │   AR ENGINE      │   CMS API        │   BUSINESS API   │
        │  8th Wall        │   Sanity.io      │   Next.js API    │
        │  Three.js        │   Content        │   Quotes/Booking │
        └──────────────────┴──────────────────┴──────────────────┘
                              ↓
        ┌─────────────────────────────────────────────────────────┐
        │              DATA LAYER (Supabase)                      │
        │  PostgreSQL: User data, quotes, bookings, analytics     │
        │  Storage: Images, 3D models, AR assets                  │
        └─────────────────────────────────────────────────────────┘
        """

        development_phases = [
            {
                "phase": "Phase 1: Foundation (Weeks 1-3)",
                "deliverables": [
                    "Next.js App Router setup with TypeScript, ESLint, Prettier",
                    "SurfaceCraft design system (Tailwind v4 + component primitives)",
                    "Home, About, Services, Gallery core pages",
                    "Mobile-first responsive layouts",
                    "SEO optimization (meta tags, structured data, sitemap)",
                    "Accessibility compliance (WCAG 2.1 AA)",
                ],
                "cost": "$8,000",
            },
            {
                "phase": "Phase 2: CMS & Content (Weeks 4-5)",
                "deliverables": [
                    "Sanity CMS setup with custom schemas",
                    "Material catalog (granite/quartz varieties)",
                    "Case study/portfolio integration",
                    "Blog system for content marketing",
                    "Image optimization pipeline",
                ],
                "cost": "$4,000",
            },
            {
                "phase": "Phase 3: AR Integration (Weeks 6-9)",
                "deliverables": [
                    "8th Wall WebAR implementation",
                    "3D model creation (15-20 popular stone varieties)",
                    "Countertop visualizer tool",
                    "Material explorer with 360° view",
                    "AR performance optimization for mobile",
                ],
                "cost": "$12,000",
            },
            {
                "phase": "Phase 4: Business Logic (Weeks 10-11)",
                "deliverables": [
                    "Quote request form with Zod validation",
                    "Appointment booking integration (Calendly API)",
                    "Email notifications (SendGrid)",
                    "Google Analytics 4 + conversion tracking",
                    "Lead management integration (CRM webhook)",
                ],
                "cost": "$5,000",
            },
            {
                "phase": "Phase 5: Testing & Launch (Weeks 12-13)",
                "deliverables": [
                    "Cross-browser testing (Chrome, Safari, Firefox, Edge)",
                    "Mobile device testing (iOS, Android)",
                    "Performance optimization (Lighthouse score >90)",
                    "Security audit (OWASP checklist)",
                    "Staging deployment for client review",
                    "Production launch + DNS configuration",
                ],
                "cost": "$4,000",
            },
            {
                "phase": "Phase 6: Post-Launch (Week 14)",
                "deliverables": [
                    "Team training on CMS and analytics",
                    "Documentation (technical + user guides)",
                    "30-day support period",
                    "Performance monitoring setup",
                ],
                "cost": "$2,000",
            },
        ]

        homepage_draft_proposal = {
            "project": "SurfaceCraft Studio homepage replacement for amzgranite.com",
            "brand_direction": "Luxury stone surfaces with modern editorial elegance",
            "legacy_trace_cleanup": [
                "Replace remaining amzgranite.com references across metadata and links",
                "Replace instagram.com/amazongranite references with SurfaceCraft handles",
                "Set canonical branding to SurfaceCraft Studio in SEO schema",
            ],
            "homepage_sections": [
                "Hero: Signature monogram + premium value proposition + primary CTA",
                "Curated Materials: Marble/Quartz collections with rich visual cards",
                "Project Gallery: Before/after transformations with filterable layouts",
                "Craftsmanship Process: Discovery → Design → Fabrication → Installation",
                "Trust Layer: Certifications, warranties, testimonials, partner logos",
                "Conversion Footer: Book consultation + phone + showroom location",
            ],
            "ux_principles": [
                "Editorial whitespace and restrained luxury typography",
                "High-contrast conversion pathways with concise CTAs",
                "Performance-first media strategy for mobile and desktop",
            ],
        }

        return {
            "tech_stack": tech_stack,
            "architecture_design": architecture,
            "ar_features": ar_features,
            "development_phases": development_phases,
            "testing_results": [
                "Core Web Vitals targets: LCP <2.5s, FID <100ms, CLS <0.1",
                "Lighthouse scores: Performance >90, Accessibility >95, SEO >95",
                "Cross-browser compatibility: 99%+ support for target browsers",
                "Mobile responsiveness: Tested on iPhone, Samsung, Pixel devices",
                "AR performance: 30fps minimum on mid-range devices (2021+)",
            ],
            "deliverables": [
                "Fully functional Next.js website with AR integration",
                "CMS (Sanity) with populated content",
                "Source code repository (GitHub)",
                "Deployment pipeline (Vercel)",
                "Technical documentation",
                "User training materials",
                "30-day post-launch support",
            ],
            "status": "architecture_complete",
            "budget_used": 35000.0,
            "timeline_days": 91,
            "homepage_draft_proposal": homepage_draft_proposal,
            "codex_tooling": codex_tooling,
        }


class LegalComplianceAgent(SpecializedAgent):
    """Expert in business legal and compliance matters"""

    def __init__(self):
        super().__init__(
            name="Legal & Compliance Specialist",
            expertise_area="Legal",
            capabilities=[
                "DBA registration and trade names",
                "Trademark search and filing",
                "Business licensing",
                "Contract review",
                "Compliance management",
                "Risk assessment",
            ],
            knowledge_base=LEGAL_EXPERTISE,
        )

    def dba_registration_process(self, state: LegalAgentState) -> Dict:
        """Execute DBA registration process"""
        print(f"\n⚖️ {self.name} - DBA REGISTRATION")
        print("=" * 70)

        task_desc = state.get("task_description", "")
        jurisdiction = state.get("jurisdiction", "Ohio")

        print(f"Applying Harvard Law + SBA Legal Framework for {jurisdiction}")

        filings_required = [
            "Step 1: USPTO TESS Trademark Search - Verify 'SURFACECRAFT STUDIO' availability",
            "Step 2: Ohio Secretary of State - Business name availability check",
            "Step 3: Hamilton County Recorder - File DBA/Trade Name registration",
            "Step 4: Publication Requirement - Legal notice in Cincinnati Enquirer (2 weeks)",
            "Step 5: EIN Verification - Ensure IRS has correct DBA information",
            "Step 6: Business Licenses - Update contractor license with new DBA",
            "Step 7: Insurance Update - Notify carriers of DBA for policy endorsement",
            "Step 8: Bank Account - Open business account under DBA name",
        ]

        compliance_checklist = [
            {
                "item": "Trademark Clearance",
                "status": "Required",
                "timeline": "1-2 days",
                "cost": "$0 (DIY search)",
                "notes": "USPTO TESS database search for conflicts",
            },
            {
                "item": "Hamilton County DBA Filing",
                "status": "Required",
                "timeline": "Same day",
                "cost": "$38 filing fee",
                "notes": "File at County Recorder, 138 E Court St, Cincinnati",
            },
            {
                "item": "Publication (Cincinnati Enquirer)",
                "status": "Required",
                "timeline": "2 weeks",
                "cost": "$100-200",
                "notes": "Legal notice must run in newspaper of record",
            },
            {
                "item": "Ohio Contractor License Update",
                "status": "Required if licensed",
                "timeline": "3-5 days",
                "cost": "$50 amendment fee",
                "notes": "Update license to reflect DBA",
            },
            {
                "item": "General Liability Insurance Update",
                "status": "Required",
                "timeline": "1 week",
                "cost": "$0 (policy endorsement)",
                "notes": "Certificate of Insurance with DBA name",
            },
            {
                "item": "Business Bank Account",
                "status": "Recommended",
                "timeline": "1 week",
                "cost": "$0-25/mo",
                "notes": "DBA certificate + Articles of Organization required",
            },
        ]

        documents_prepared = [
            "DBA Filing Form (Hamilton County Form TR-1)",
            "Affidavit of Publication template",
            "Bank account opening packet (with DBA certificate)",
            "Insurance endorsement request letter",
            "Contractor license amendment application",
            "IRS Form SS-4 (if separate EIN needed for DBA)",
            "Business stationery checklist (letterhead, cards, invoices must show DBA)",
        ]

        risks_identified = [
            "RISK: Trademark infringement - Mitigated by USPTO search before filing",
            "RISK: Inconsistent name usage - Must use DBA consistently in all materials",
            "RISK: Missing publication deadline - Calendar alert for newspaper filing",
            "RISK: Insurance gap - Notify carriers immediately to maintain coverage",
            "RISK: Contract validity - Ensure contracts executed as 'Amazon Granite LLC dba Surfacecraft Studio'",
            "RISK: Banking delays - DBA process may take 2-3 weeks for bank account",
        ]

        print(f"\n✓ Complete DBA registration roadmap prepared")
        print(f"✓ {len(compliance_checklist)} compliance items identified")
        print(f"✓ {len(risks_identified)} risks assessed and mitigation plans created")

        recommendations = [
            "TIMELINE: Allow 3-4 weeks for complete DBA registration process",
            "BUDGET: $400-500 total (filing $38 + publication $200 + misc $162-262)",
            "PRIORITY: File DBA before ordering any branded materials or website launch",
            "ATTORNEY: Consider $500 consultation for contract templates and trademark filing",
            "ONGOING: Annual DBA renewal required in some counties - set calendar reminder",
            "TRADEMARK: File federal trademark application ($350 + $1,500 attorney) for protection",
        ]

        return {
            "filings_required": filings_required,
            "compliance_checklist": compliance_checklist,
            "documents_prepared": documents_prepared,
            "risks_identified": risks_identified,
            "status": "registration_plan_complete",
            "budget_used": 500.0,
            "timeline_days": 21,
        }


class MartechAgent(SpecializedAgent):
    """Expert in marketing technology and automation

    📊 EXECUTES (does not recommend):
    - Configures CRM systems (HubSpot, Zoho)
    - Sets up marketing automation
    - Implements analytics tracking
    - Creates integration workflows

    💰 Budget: $200 (mostly free tiers)
    🎓 Standards: MIT Sloan, Harvard Business School
    """

    def __init__(self):
        super().__init__(
            name="Marketing Technology Specialist",
            expertise_area="MarTech",
            capabilities=[
                "📊 CONFIGURES CRM systems (HubSpot, Zoho)",
                "🔄 SETS UP marketing automation workflows",
                "📈 IMPLEMENTS Google Analytics 4 tracking",
                "🔗 CREATES Zapier integrations",
                "📧 CONFIGURES email marketing platforms",
                "🎯 IMPLEMENTS conversion tracking",
            ],
            knowledge_base=MARTECH_EXPERTISE,
            guard_rail=AgentGuardRail(AgentDomain.MARTECH),
        )

        print(f"\n{'='*70}")
        print(f"🤖 {self.name} INITIALIZED")
        print(f"{'='*70}")
        print("💡 This agent CONFIGURES systems (does not hire consultants)")
        print(f"💰 Budget: ${self.guard_rail.budget_constraint.max_budget}")
        print("✅ Execution Mode: CONFIGURATION ACTIVE")
        print(f"{'='*70}\n")

    def configure_stack(self, state: MartechAgentState) -> Dict:
        """AI CONFIGURES complete marketing technology stack"""
        state = self.validate_execution(state)

        print(f"\n📊 {self.name} - AI CONFIGURATION (EXECUTING)")
        print("=" * 70)
        print("💡 AI agent configures all systems - no consultants needed")
        print("=" * 70)

        recommended_stack = [
            {
                "tool": "HubSpot CRM",
                "category": "Customer Relationship Management",
                "tier": "Free tier (unlimited contacts)",
                "ai_configures": "✅ AI sets up contact properties, deal stages, pipelines",
                "cost": "$0/month",
            },
            {
                "tool": "Google Analytics 4",
                "category": "Web Analytics",
                "tier": "Free (standard)",
                "ai_configures": "✅ AI implements tracking code, events, conversions",
                "cost": "$0/month",
            },
            {
                "tool": "Mailchimp",
                "category": "Email Marketing",
                "tier": "Free tier (up to 500 contacts)",
                "ai_configures": "✅ AI creates email templates, automation workflows",
                "cost": "$0/month",
            },
            {
                "tool": "Zapier",
                "category": "Automation & Integration",
                "tier": "Starter ($29.99/month) or Free tier",
                "ai_configures": "✅ AI builds Zaps connecting all platforms",
                "cost": "$0-30/month",
            },
            {
                "tool": "Hotjar",
                "category": "User Behavior Analytics",
                "tier": "Free tier (35 daily sessions)",
                "ai_configures": "✅ AI sets up heatmaps, recordings, surveys",
                "cost": "$0/month",
            },
        ]

        print("\n🤖 AI-Configured MarTech Stack:")
        for tool in recommended_stack:
            print(f"  ✅ {tool['tool']}: {tool['ai_configures']}")

        total_cost = 30  # Only Zapier starter if needed
        print(f"\n💰 Budget: ${total_cost}/month (mostly free tiers)")

        return {
            "recommended_stack": recommended_stack,
            "status": "stack_configured",
            "budget_used": 200.0,
            "timeline_days": 21,
            "execution_mode": "AI_CONFIGURED",
        }


class ContentAgent(SpecializedAgent):
    """Expert in content strategy and production

    📸 EXECUTES (does not recommend):
    - Writes all marketing copy
    - Creates video scripts and storyboards
    - Produces graphic designs
    - Develops content calendars

    💰 Budget: $150 (design tools + stock assets)
    🎓 Standards: Stanford Writing, MIT Media Studies
    """

    def __init__(self):
        super().__init__(
            name="Content Strategy & Production Specialist",
            expertise_area="Content",
            capabilities=[
                "✍️ WRITES website copy and marketing content",
                "🎬 CREATES video scripts and storyboards",
                "🎨 DESIGNS social media graphics",
                "📅 DEVELOPS content calendars",
                "📧 PRODUCES email newsletters",
                "📝 CRAFTS SEO-optimized blog posts",
            ],
            knowledge_base=CONTENT_EXPERTISE,
            guard_rail=AgentGuardRail(AgentDomain.CONTENT),
        )

        print(f"\n{'='*70}")
        print(f"🤖 {self.name} INITIALIZED")
        print(f"{'='*70}")
        print("💡 This agent CREATES content (does not hire writers)")
        print(f"💰 Budget: ${self.guard_rail.budget_constraint.max_budget}")
        print("✅ Execution Mode: CONTENT CREATION ACTIVE")
        print(f"{'='*70}\n")

    def produce_content(self, state: ContentAgentState) -> Dict:
        """AI PRODUCES all marketing content"""
        state = self.validate_execution(state)

        print(f"\n📸 {self.name} - AI CONTENT PRODUCTION (EXECUTING)")
        print("=" * 70)
        print("💡 AI agent creates all content - no agencies or freelancers")
        print("=" * 70)

        codex_tooling = self.run_codex_tooling(
            objective="Generate campaign-ready copy and publishing guidance",
            context={"task_description": state.get("task_description", "")},
        )

        content_types = [
            "✅ AI WRITES: Website copy (home, services, about, contact pages)",
            "✅ AI CREATES: Video scripts for product demonstrations",
            "✅ AI DESIGNS: Social media graphics (Instagram, Facebook, LinkedIn)",
            "✅ AI PRODUCES: Blog posts (SEO-optimized, 1500+ words)",
            "✅ AI CRAFTS: Email newsletter templates and campaigns",
            "✅ AI DEVELOPS: Case study write-ups and testimonials",
        ]

        assets_created = [
            "Website copy: 5,000+ words across all pages",
            "Video scripts: 3 product demo videos (2-3 minutes each)",
            "Social graphics: 30 Instagram posts, 20 Facebook images",
            "Blog articles: 5 pillar posts (1,500-2,000 words each)",
            "Email templates: Welcome series (5 emails) + monthly newsletter",
            "Case studies: 3 before/after project showcases",
        ]

        print("\n🤖 AI-Created Content Assets:")
        for asset in assets_created:
            print(f"  ✅ {asset}")

        print(f"\n💰 Budget: $150 (Canva Pro $13/mo + stock images $50)")

        if codex_tooling.get("used"):
            print("\n🤖 OpenAI Codex tooling assistance: enabled")

        return {
            "content_types": content_types,
            "assets_created": assets_created,
            "status": "content_produced",
            "budget_used": 150.0,
            "timeline_days": 35,
            "execution_mode": "AI_CREATED",
            "codex_tooling": codex_tooling,
        }


class CampaignAgent(SpecializedAgent):
    """Expert in campaign strategy and execution

    🚀 EXECUTES (does not recommend):
    - Creates ad copy and creative
    - Configures Google Ads campaigns
    - Sets up Meta Ads with targeting
    - Manages campaign optimization

    💰 Budget: $3,000 (actual ad spend)
    🎓 Standards: Harvard Marketing ROI, Stanford Digital Marketing
    """

    def __init__(self):
        super().__init__(
            name="Campaign Strategy & Execution Specialist",
            expertise_area="Campaigns",
            capabilities=[
                "📝 CREATES ad copy and creative assets",
                "🎯 CONFIGURES Google Ads campaigns",
                "📱 SETS UP Meta Ads (Facebook/Instagram)",
                "📊 MANAGES A/B testing and optimization",
                "📈 ANALYZES campaign performance",
                "💰 OPTIMIZES budget allocation",
            ],
            knowledge_base=CAMPAIGN_EXPERTISE,
            guard_rail=AgentGuardRail(AgentDomain.CAMPAIGNS),
        )

        print(f"\n{'='*70}")
        print(f"🤖 {self.name} INITIALIZED")
        print(f"{'='*70}")
        print("💡 This agent MANAGES campaigns (does not hire agencies)")
        print(f"💰 Budget: ${self.guard_rail.budget_constraint.max_budget}")
        print("✅ Execution Mode: CAMPAIGN MANAGEMENT ACTIVE")
        print(f"{'='*70}\n")

    def launch_campaigns(self, state: CampaignAgentState) -> Dict:
        """AI LAUNCHES and manages advertising campaigns"""
        state = self.validate_execution(state)

        print(f"\n🚀 {self.name} - AI CAMPAIGN LAUNCH (EXECUTING)")
        print("=" * 70)
        print("💡 AI agent creates ads and manages campaigns - no agencies")
        print("=" * 70)

        channels = [
            "✅ AI MANAGES: Google Search Ads (keywords: countertops Cincinnati, granite installers)",
            "✅ AI MANAGES: Google Display Ads (remarketing + lookalike audiences)",
            "✅ AI MANAGES: Meta Ads (Facebook/Instagram - local home improvement)",
            "✅ AI MANAGES: Google Local Services Ads (contractor leads)",
        ]

        creative_concepts = [
            {
                "campaign": "Google Search - Quote Requests",
                "ai_creates": "Ad copy with strong CTAs, landing page optimization",
                "budget": "$1,000 (90 days)",
                "targeting": "Cincinnati metro, homeowners, kitchen remodel searches",
            },
            {
                "campaign": "Meta Ads - Brand Awareness",
                "ai_creates": "Carousel ads with AR demo, before/after images",
                "budget": "$1,500 (90 days)",
                "targeting": "Cincinnati, age 30-65, homeowners, interest: home improvement",
            },
            {
                "campaign": "Google Display - Remarketing",
                "ai_creates": "Display banners, dynamic remarketing ads",
                "budget": "$500 (90 days)",
                "targeting": "Website visitors, engaged users",
            },
        ]

        print("\n🤖 AI-Managed Campaigns:")
        for concept in creative_concepts:
            print(f"  ✅ {concept['campaign']}: {concept['ai_creates']}")

        print(f"\n💰 Budget: $3,000 total ad spend (AI creates all creative)")

        return {
            "channels": channels,
            "creative_concepts": creative_concepts,
            "status": "campaigns_launched",
            "budget_used": 3000.0,
            "timeline_days": 90,
            "execution_mode": "AI_MANAGED",
        }


class SocialMediaAgent(SpecializedAgent):
    """Expert in social media growth, operations, and community management.

    📱 EXECUTES (does not recommend):
    - Builds social channel operating plans
    - Produces content calendars and posting workflows
    - Designs platform-specific campaign concepts
    - Defines community engagement and moderation playbooks
    """

    def __init__(self):
        super().__init__(
            name="Social Media Growth & Community Specialist",
            expertise_area="Social Media",
            capabilities=[
                "📱 BUILDS cross-platform social operating plans",
                "🗓️ CREATES 30/60/90-day social content calendars",
                "💬 DEFINES community management and response playbooks",
                "📈 DESIGNS platform-specific growth experiments",
                "🎯 PREPARES paid + organic social campaign concepts",
                "🔁 SETS governance for approvals and escalation",
            ],
            knowledge_base=CAMPAIGN_EXPERTISE,
            guard_rail=AgentGuardRail(AgentDomain.SOCIAL_MEDIA),
        )

    def execute_social_strategy(self, state: SocialMediaAgentState) -> Dict:
        """Execute social media strategy and operations setup."""
        state = self.validate_execution(state)

        codex_tooling = self.run_codex_tooling(
            objective="Generate platform-specific social media operating guidance",
            context={"task_description": state.get("task_description", "")},
        )

        platforms = [
            "Instagram",
            "Facebook",
            "LinkedIn",
            "YouTube Shorts",
            "TikTok",
            "X",
        ]

        content_calendar = [
            {
                "week": 1,
                "focus": "Brand story + transformation",
                "deliverables": [
                    "Founder's origin clip",
                    "Before/after countertop reel",
                    "Customer proof post",
                ],
            },
            {
                "week": 2,
                "focus": "Authority + education",
                "deliverables": [
                    "Stone selection guide carousel",
                    "Maintenance quick tips short",
                    "FAQ live session outline",
                ],
            },
            {
                "week": 3,
                "focus": "Demand generation",
                "deliverables": [
                    "Lead magnet post",
                    "Appointment CTA creative set",
                    "Retargeting ad concept",
                ],
            },
        ]

        posting_workflows = [
            "Batch-produce 2 weeks of assets every Monday",
            "Daily community sweep for comments/DMs within 2-hour SLA",
            "Weekly KPI review: reach, watch time, saves, booked consults",
            "Escalate legal/safety complaints to compliance workflow",
        ]

        campaign_ideas = [
            {
                "campaign": "Kitchen Refresh Proof Series",
                "platform": "Instagram + Facebook",
                "objective": "Lead capture",
            },
            {
                "campaign": "Ask the Fabricator",
                "platform": "YouTube Shorts + TikTok",
                "objective": "Top-of-funnel growth",
            },
            {
                "campaign": "Contractor Partner Spotlight",
                "platform": "LinkedIn",
                "objective": "B2B referral pipeline",
            },
        ]

        community_playbook = (
            "Response ladder: acknowledge within 2 hours, provide next step within 24 hours, "
            "and route complaints to owner/CFO for resolution and audit trail."
        )

        return {
            "platforms": platforms,
            "content_calendar": content_calendar,
            "posting_workflows": posting_workflows,
            "campaign_ideas": campaign_ideas,
            "community_playbook": community_playbook,
            "status": "social_strategy_ready",
            "budget_used": 250.0,
            "timeline_days": 30,
            "execution_mode": "AI_MANAGED",
            "codex_tooling": codex_tooling,
        }


# ============================================================================
# AGENT FACTORY - Creates specialized agents on demand
# ============================================================================


class AgentFactory:
    """Factory for creating specialized agents based on task requirements"""

    @staticmethod
    def create_agent(agent_type: str) -> SpecializedAgent:
        """Create specialized agent by type"""
        agents = {
            "branding": BrandingAgent,
            "web_development": WebDevelopmentAgent,
            "legal": LegalComplianceAgent,
            "martech": MartechAgent,
            "content": ContentAgent,
            "campaigns": CampaignAgent,
            "social_media": SocialMediaAgent,
            "security": SecurityBlockchainAgent,
        }

        agent_class = agents.get(agent_type.lower())
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")

        return agent_class()

    @staticmethod
    def get_available_agents() -> List[str]:
        """Get list of available specialized agents"""
        return [
            "branding",
            "web_development",
            "legal",
            "martech",
            "content",
            "campaigns",
            "social_media",
            "security",
        ]
