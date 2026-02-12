"""
Agent Knowledge Base - Master-level expertise from top universities and industry sources

This module contains synthesized knowledge from:
- MIT OpenCourseWare (Business, Design, Technology)
- Stanford Graduate School of Business
- Harvard Business School
- RISD (Rhode Island School of Design)
- Carnegie Mellon Human-Computer Interaction Institute
- Top industry frameworks (Y Combinator, a16z, McKinsey, BCG)
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class ExpertiseArea:
    """Represents a domain of expertise with master-level knowledge"""
    name: str
    field: str
    key_principles: List[str]
    frameworks: List[str]
    tools: List[str]
    success_metrics: List[str]
    common_pitfalls: List[str]
    references: List[str]


# ============================================================================
# BRANDING & VISUAL IDENTITY EXPERTISE
# ============================================================================

BRANDING_EXPERTISE = ExpertiseArea(
    name="Brand Strategy & Visual Identity Design",
    field="Branding",
    key_principles=[
        "Brand Positioning Framework (Marty Neumeier): Unique, credible, sustainable differentiation",
        "Gestalt Principles: Visual perception - proximity, similarity, closure, continuity",
        "Golden Ratio (1.618): Mathematical beauty in logo proportions and layouts",
        "Color Psychology: Red (energy), Blue (trust), Green (growth), Purple (luxury)",
        "Typography Hierarchy: 60-30-10 rule for visual balance",
        "Brand Archetype Theory (Jung): Hero, Creator, Sage, Ruler for personality",
        "Semiotics in Design: Signs, symbols, and cultural meaning systems",
        "Consistency Principle: 7-12 touchpoints before brand recognition",
    ],
    frameworks=[
        "Brand Identity Prism (Kapferer): Physique, Personality, Culture, Relationship, Reflection, Self-image",
        "Golden Circle (Sinek): Why → How → What communication hierarchy",
        "AIDA Framework: Attention, Interest, Desire, Action in brand communication",
        "Brand Equity Model (Keller): Salience, Performance, Imagery, Judgments, Feelings, Resonance",
        "Design Thinking Process: Empathize, Define, Ideate, Prototype, Test",
        "Jobs To Be Done: Functional, emotional, social jobs brand fulfills",
    ],
    tools=[
        "Adobe Creative Suite: Illustrator (vector), Photoshop (raster), InDesign (layout)",
        "Figma/Sketch: Collaborative interface design and prototyping",
        "Pantone Matching System: Color consistency across materials",
        "Google Fonts/Adobe Fonts: Typography selection and pairing",
        "Brandfolder/Frontify: Brand asset management systems",
        "UsabilityHub/Maze: Logo testing and perception studies",
    ],
    success_metrics=[
        "Brand Recognition Rate: % of target audience recognizing brand unprompted",
        "Brand Recall: Top-of-mind awareness in category",
        "Net Promoter Score (NPS): Likelihood to recommend (-100 to +100)",
        "Brand Equity Value: Financial valuation of brand assets",
        "Consistency Score: Adherence to brand guidelines across touchpoints",
        "Perception Gap: Difference between intended and perceived brand attributes",
    ],
    common_pitfalls=[
        "Logo-centric thinking: Brand is ecosystem, not just visual mark",
        "Trend chasing: Following fads vs. timeless design principles",
        "Complex ≠ Professional: Simplicity aids recognition and reproduction",
        "Ignoring scalability: Logo must work 16px to 16ft",
        "Cultural insensitivity: Symbols/colors have different meanings globally",
        "Stakeholder design: Too many opinions dilute creative vision",
    ],
    references=[
        "MIT 15.834 - Marketing Strategy",
        "Stanford GSB: Branding and Customer Experience",
        "RISD Graphic Design Program Principles",
        "Paul Rand - 'Design, Form, and Chaos'",
        "Marty Neumeier - 'The Brand Gap'",
        "Debbie Millman - 'How to Think Like a Great Graphic Designer'",
    ]
)


# ============================================================================
# WEB DEVELOPMENT & AR INTEGRATION EXPERTISE
# ============================================================================

WEB_DEV_EXPERTISE = ExpertiseArea(
    name="Web Development & AR Integration",
    field="Technology",
    key_principles=[
        "Progressive Enhancement: Core content accessible, enhancements layered",
        "Mobile-First Design: 60%+ traffic mobile, design up from smallest screen",
        "Web Performance Budget: <3s load time, <100ms interaction response",
        "Semantic HTML: Proper element usage for accessibility and SEO",
        "WCAG 2.1 AA: Color contrast 4.5:1, keyboard navigation, screen reader support",
        "RESTful API Design: Stateless, cacheable, uniform interface",
        "Security First: HTTPS, input validation, XSS/CSRF protection, CSP headers",
        "WebAR Standards: Use of 8th Wall, AR.js, or WebXR Device API",
    ],
    frameworks=[
        "JAMstack Architecture: JavaScript, APIs, Markup (Gatsby, Next.js, Nuxt)",
        "Component-Based Design: Reusable UI elements (React, Vue, Svelte)",
        "Headless CMS: Content management decoupled from presentation (Contentful, Sanity)",
        "AR Frameworks: Three.js for 3D, A-Frame for WebVR, Model-Viewer for 3D models",
        "Conversion Rate Optimization: 5-second test, heatmaps, A/B testing",
        "Core Web Vitals: LCP (<2.5s), FID (<100ms), CLS (<0.1)",
    ],
    tools=[
        "Frontend: React/Next.js, TypeScript, Tailwind CSS, Framer Motion",
        "AR Integration: 8th Wall Web, Google Model Viewer, Zappar, AR.js",
        "3D Modeling: Blender, SketchUp for countertop visualizations",
        "Backend: Node.js, Express, PostgreSQL, Firebase/Supabase",
        "Testing: Cypress (E2E), Jest (unit), Lighthouse (performance)",
        "Analytics: Google Analytics 4, Hotjar, Microsoft Clarity",
        "Hosting: Vercel, Netlify, AWS Amplify for static sites",
    ],
    success_metrics=[
        "Time to Interactive (TTI): <3.8s on 4G",
        "Conversion Rate: Quote requests / unique visitors",
        "Bounce Rate: <40% (industry benchmark 41-55%)",
        "AR Engagement: % users activating AR, time in AR mode",
        "SEO Performance: Domain Authority, keyword rankings, organic traffic",
        "Accessibility Score: Lighthouse accessibility >90",
    ],
    common_pitfalls=[
        "Premature optimization: Build working version before micro-optimizations",
        "Ignoring cross-browser testing: Safari, Chrome, Firefox rendering differences",
        "Overreliance on frameworks: Adds bloat, consider vanilla JS for simple interactions",
        "Poor AR UX: Calibration complexity, lighting requirements, device compatibility",
        "Neglecting performance: Large images, unoptimized assets kill mobile experience",
        "Security vulnerabilities: SQL injection, XSS, insecure dependencies",
    ],
    references=[
        "MIT 6.170 - Software Studio",
        "Stanford CS 142 - Web Applications",
        "CMU 05-430 - Human-Computer Interaction",
        "Google Web Fundamentals",
        "Mozilla Developer Network (MDN)",
        "8th Wall WebAR Documentation",
    ]
)


# ============================================================================
# LEGAL & COMPLIANCE EXPERTISE (DBA Registration)
# ============================================================================

LEGAL_EXPERTISE = ExpertiseArea(
    name="Business Legal & Compliance",
    field="Legal",
    key_principles=[
        "DBA (Doing Business As): Trade name registration separate from LLC",
        "Name Availability Search: State and federal trademark databases",
        "Compliance Hierarchy: Federal → State → County → Municipal",
        "Trademark Protection: Common law (use) vs. registered (®) rights",
        "Corporate Veil: Maintain separate entity to protect personal assets",
        "Contract Fundamentals: Offer, acceptance, consideration, capacity, legality",
        "Industry Licensing: Contractor licenses, bonds, insurance requirements",
        "Privacy Laws: CCPA (California), GDPR (EU) implications for website",
    ],
    frameworks=[
        "Ohio DBA Process: County recorder filing + publication in local newspaper",
        "USPTO TESS Search: Comprehensive trademark conflict check",
        "Business Structure Decision Tree: Sole proprietor → Partnership → LLC → Corp",
        "Risk Assessment Matrix: Likelihood × Impact for legal exposures",
        "Compliance Calendar: Annual filings, license renewals, tax deadlines",
        "Contract Lifecycle: Draft → Review → Negotiate → Execute → Manage",
    ],
    tools=[
        "Ohio Business Gateway: Online DBA filing portal",
        "USPTO Trademark Search (TESS): Federal trademark database",
        "LegalZoom/Rocket Lawyer: Document templates and filing services",
        "DocuSign: Electronic signature management",
        "Clerky: Startup legal document automation",
        "Termsfeed: Privacy policy and terms of service generator",
    ],
    success_metrics=[
        "Filing Completion Time: Days from decision to registration",
        "Zero Legal Disputes: No trademark conflicts or contract breaches",
        "Compliance Rate: 100% of required filings on time",
        "Insurance Coverage Adequacy: General liability $1-2M, errors & omissions",
        "Contract Win Rate: % of proposals converting to signed contracts",
    ],
    common_pitfalls=[
        "Skipping trademark search: Costly rebrand if conflict discovered later",
        "Inconsistent name usage: DBA must be used consistently in all materials",
        "Missing deadlines: Late fees, loss of good standing, legal penalties",
        "DIY complex contracts: Employment, partnership agreements need attorney review",
        "Underinsuring: Countertop installation has liability risks (property damage)",
        "Privacy policy neglect: Required if collecting any customer data",
    ],
    references=[
        "Harvard Law School - Startup Legal Bootcamp",
        "Stanford Law - Entrepreneurship Legal Clinic Resources",
        "Ohio Revised Code Chapter 1329 (Trade Names)",
        "Small Business Administration (SBA) Legal Guides",
        "American Bar Association Business Law Resources",
    ]
)


# ============================================================================
# MARKETING TECHNOLOGY EXPERTISE
# ============================================================================

MARTECH_EXPERTISE = ExpertiseArea(
    name="Marketing Technology & CRM",
    field="Marketing Operations",
    key_principles=[
        "Customer Data Platform (CDP): Single source of truth for customer data",
        "Marketing Automation: Nurture sequences, behavior-triggered campaigns",
        "Attribution Modeling: Multi-touch attribution vs. last-click",
        "Funnel Optimization: Awareness → Consideration → Decision → Retention",
        "Personalization at Scale: Dynamic content based on user segments",
        "Privacy-First Marketing: Cookieless tracking, consent management",
        "Integration Architecture: APIs, webhooks, middleware (Zapier, Make)",
        "Data Hygiene: Deduplication, standardization, enrichment",
    ],
    frameworks=[
        "Marketing Technology Stack: Acquisition → Conversion → Retention → Analytics",
        "HubSpot Flywheel: Attract, Engage, Delight (vs. traditional funnel)",
        "RFM Analysis: Recency, Frequency, Monetary value for segmentation",
        "Lead Scoring: Demographic + behavioral signals to prioritize prospects",
        "Email Marketing Best Practices: Subject line A/B, send time optimization",
        "Marketing Mix Modeling: Statistical analysis of channel effectiveness",
    ],
    tools=[
        "CRM: HubSpot (SMB), Salesforce (enterprise), Pipedrive (sales-focused)",
        "Email Marketing: Mailchimp, ConvertKit, ActiveCampaign",
        "Analytics: Google Analytics 4, Mixpanel, Amplitude",
        "Booking Systems: Calendly, Acuity, Square Appointments",
        "Heatmaps/Session Recording: Hotjar, FullStory, Microsoft Clarity",
        "Marketing Automation: Zapier, Make (Integromat), Segment (CDP)",
        "Social Media Management: Buffer, Hootsuite, Later",
    ],
    success_metrics=[
        "Customer Acquisition Cost (CAC): Total marketing spend / new customers",
        "Lifetime Value (LTV): Average customer revenue over relationship",
        "LTV:CAC Ratio: Should be >3:1 for sustainable growth",
        "Marketing Qualified Leads (MQLs): Leads meeting scoring threshold",
        "SQL Conversion Rate: % of MQLs converting to sales opportunities",
        "Email Engagement: Open rate >20%, click rate >3%, unsubscribe <0.5%",
        "Pipeline Velocity: (Opportunities × Win Rate × Deal Size) / Sales Cycle Length",
    ],
    common_pitfalls=[
        "Tool sprawl: Too many disconnected tools creating data silos",
        "Over-automation: Losing human touch in customer interactions",
        "Ignoring data quality: 'Garbage in, garbage out' for automation",
        "Complexity before scale: Start simple, add complexity as you grow",
        "Vanity metrics focus: Followers/likes vs. revenue-driving KPIs",
        "Neglecting integrations: Manual data entry defeats automation purpose",
    ],
    references=[
        "MIT Sloan - Marketing Analytics",
        "Stanford GSB - Data-Driven Marketing",
        "Scott Brinker - Martech Landscape (10,000+ tools)",
        "HubSpot Academy - Inbound Marketing Certification",
        "Google Analytics Academy",
        "Salesforce Trailhead Learning Platform",
    ]
)


# ============================================================================
# CONTENT STRATEGY & PRODUCTION EXPERTISE
# ============================================================================

CONTENT_EXPERTISE = ExpertiseArea(
    name="Content Strategy & Production",
    field="Content Marketing",
    key_principles=[
        "Content Marketing ROI: 3x more leads than outbound, 62% lower cost per lead",
        "Pillar-Cluster Model: Topic clusters linking to pillar pages for SEO",
        "Storytelling Framework: Hero's journey, story spine (once upon a time...)",
        "E-E-A-T (Google): Experience, Expertise, Authoritativeness, Trustworthiness",
        "Content Atomization: One core asset → multiple formats (blog, video, social, email)",
        "Video Retention Curve: Hook in first 3s, value delivery by 15s, CTA before drop-off",
        "Visual Hierarchy: F-pattern reading, Z-pattern scanning, eye-tracking insights",
        "SEO Content: Search intent match (informational, navigational, transactional)",
    ],
    frameworks=[
        "Content Strategy Framework: Audience → Goals → Format → Distribution → Measurement",
        "Buyer's Journey Mapping: Awareness → Consideration → Decision content",
        "Content Calendar: 60% educational, 30% promotional, 10% entertaining",
        "Video Production Process: Pre-production → Production → Post → Distribution",
        "Case Study Structure: Challenge → Solution → Results (with metrics)",
        "Photography Shot List: Establishing, detail, process, before/after, lifestyle",
    ],
    tools=[
        "Video Production: Adobe Premiere Pro, Final Cut Pro, DaVinci Resolve",
        "Photography: Canon/Sony cameras, Adobe Lightroom, Capture One",
        "Graphic Design: Canva (easy), Adobe Creative Suite (pro)",
        "Content Management: WordPress, Contentful, Sanity",
        "SEO Tools: Ahrefs, SEMrush, Moz for keyword research",
        "Stock Assets: Unsplash, Pexels (free), Getty, Shutterstock (premium)",
        "Project Management: Asana, Monday.com, Notion for content calendars",
    ],
    success_metrics=[
        "Organic Traffic: Monthly unique visitors from search",
        "Engagement Rate: Time on page >2min, scroll depth >50%",
        "Video Completion Rate: % watching >75% of video",
        "Social Shares: Amplification factor for content reach",
        "Lead Generation: Downloads, form fills from content",
        "SEO Rankings: Keywords in top 3 positions (CTR 30%+)",
        "Brand Lift: Awareness, consideration, preference from surveys",
    ],
    common_pitfalls=[
        "Creating content without audience research: Build for your customer, not yourself",
        "Inconsistent publishing: Sporadic content damages trust and SEO",
        "Ignoring distribution: 80% promotion, 20% creation for new content",
        "Poor production quality: Blurry photos, bad audio kills credibility",
        "No repurposing plan: Leaving ROI on table by using content once",
        "Skipping keyword research: Writing content nobody searches for",
    ],
    references=[
        "MIT Comparative Media Studies - Digital Storytelling",
        "USC School of Cinematic Arts - Production Techniques",
        "Content Marketing Institute Research",
        "Ann Handley - 'Everybody Writes'",
        "Jay Baer - 'Youtility'",
        "HubSpot Content Marketing Playbook",
    ]
)


# ============================================================================
# CAMPAIGN STRATEGY & EXECUTION EXPERTISE
# ============================================================================

CAMPAIGN_EXPERTISE = ExpertiseArea(
    name="Integrated Campaign Strategy",
    field="Campaign Management",
    key_principles=[
        "Campaign Hierarchy: Brand → Campaign → Ad Group → Creative → Asset",
        "Message Architecture: Single-minded proposition (SMP) across channels",
        "Channel Mix: Earned (PR) + Owned (website) + Paid (ads) integration",
        "Frequency Management: 7-12 exposures for message retention",
        "Recency Theory: Last exposure before purchase most influential",
        "Day-parting: Ad scheduling when target audience most receptive",
        "Creative Testing: Minimum 3-5 variations for statistical significance",
        "Budget Allocation: 70-20-10 rule (proven, test, experimental)",
    ],
    frameworks=[
        "Campaign Brief Template: Objective, Audience, Message, Channels, Budget, Timeline, KPIs",
        "SOSTAC Planning: Situation, Objectives, Strategy, Tactics, Actions, Control",
        "Media Planning Process: Reach × Frequency = GRPs (Gross Rating Points)",
        "Creative Development: Research → Concept → Copy → Design → Test → Launch",
        "Launch Checklist: 50+ items from tracking setup to crisis plan",
        "Performance Review Cadence: Daily (optimization) → Weekly (tactics) → Monthly (strategy)",
    ],
    tools=[
        "Paid Social: Meta Ads Manager, LinkedIn Campaign Manager, TikTok Ads",
        "Paid Search: Google Ads, Microsoft Advertising",
        "Display/Programmatic: Google Display Network, The Trade Desk",
        "Local Ads: Google Local Services Ads, Nextdoor Ads, Yelp Ads",
        "Project Management: Asana, Monday.com, ClickUp for campaign tracking",
        "Collaboration: Figma, Miro for creative briefs and mood boards",
        "Reporting: Google Data Studio, Tableau, Power BI",
    ],
    success_metrics=[
        "ROAS (Return on Ad Spend): Revenue / ad spend, target >4:1",
        "Cost Per Acquisition (CPA): Ad spend / conversions",
        "Click-Through Rate (CTR): Clicks / impressions, benchmark 2-5%",
        "Quality Score (Google Ads): 7+ for lower CPCs",
        "Engagement Rate: (Likes + Comments + Shares) / Reach",
        "Brand Lift: Survey-based measurement of awareness increase",
        "Attribution: First-touch, last-touch, multi-touch revenue attribution",
    ],
    common_pitfalls=[
        "Launching without clear success metrics: Define KPIs before spend",
        "Insufficient testing budget: Need 15-20% of budget for experimentation",
        "Ignoring creative fatigue: Refresh ads every 2-4 weeks",
        "Platform tunnel vision: Over-investing in single channel creates risk",
        "Optimizing too early: Need statistical significance (100+ conversions)",
        "No dark post strategy: Organic ≠ paid, separate creative for each",
    ],
    references=[
        "Stanford GSB - Advertising and Brand Management",
        "Northwestern Kellogg - Integrated Marketing Communications",
        "Facebook Blueprint Certification",
        "Google Skillshop - Google Ads Certification",
        "Byron Sharp - 'How Brands Grow'",
        "Gary Vaynerchuk - 'Jab, Jab, Jab, Right Hook'",
    ]
)


# ============================================================================
# KNOWLEDGE BASE REGISTRY
# ============================================================================

EXPERTISE_REGISTRY: Dict[str, ExpertiseArea] = {
    "branding": BRANDING_EXPERTISE,
    "web_development": WEB_DEV_EXPERTISE,
    "legal": LEGAL_EXPERTISE,
    "martech": MARTECH_EXPERTISE,
    "content": CONTENT_EXPERTISE,
    "campaigns": CAMPAIGN_EXPERTISE,
}


def get_expertise(field: str) -> ExpertiseArea:
    """Retrieve expertise area by field name"""
    return EXPERTISE_REGISTRY.get(field.lower())


def get_all_expertise_areas() -> List[str]:
    """Get list of all available expertise areas"""
    return list(EXPERTISE_REGISTRY.keys())
