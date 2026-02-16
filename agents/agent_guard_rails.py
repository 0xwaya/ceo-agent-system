"""
Agent Guard Rails and Execution Framework

Defines constraints and validation rules to keep AI agents focused
on their specific tasks and ensure they execute (not just recommend).
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AgentDomain(Enum):
    """Strict domain boundaries for agent specialization"""

    BRANDING = "branding"
    WEB_DEVELOPMENT = "web_development"
    LEGAL = "legal"
    MARTECH = "martech"
    CONTENT = "content"
    CAMPAIGNS = "campaigns"
    SECURITY = "security"
    CEO = "ceo"  # Executive orchestrator
    CFO = "cfo"  # Financial oversight only


class ExecutionMode(Enum):
    """Agent must execute work, not recommend vendors"""

    EXECUTE = "execute"  # Agent performs the work
    RECOMMEND = "recommend"  # Agent suggests external resources (FORBIDDEN)


class DeliverableType(Enum):
    """Types of production-ready outputs"""

    DESIGN_FILES = "design_files"  # Logo, graphics, brand assets
    CODE = "code"  # Website, applications, scripts
    DOCUMENTS = "documents"  # Legal filings, contracts, policies
    CONFIGURATION = "configuration"  # System setup, integrations
    CONTENT = "content"  # Copy, video, photography
    STRATEGY = "strategy"  # Plans, roadmaps, frameworks


class PaymentType(Enum):
    """Types of payments requiring user approval"""

    API_FEE = "api_fee"  # OpenAI, SendGrid, etc. (CFO can manage)
    LEGAL_FILING = "legal_filing"  # Government fees (CFO can manage)
    SOFTWARE_SUBSCRIPTION = "software_subscription"  # Requires user approval
    SERVICE_ORDER = "service_order"  # Requires user approval
    ADVERTISING_SPEND = "advertising_spend"  # Requires user approval
    HARDWARE_PURCHASE = "hardware_purchase"  # Requires user approval
    CONTRACTOR_PAYMENT = "contractor_payment"  # FORBIDDEN


class ApprovalLevel(Enum):
    """Approval levels for different actions"""

    AUTO_APPROVED = "auto_approved"  # CFO can approve (API fees only)
    USER_APPROVAL_REQUIRED = "user_approval_required"  # User must approve
    FORBIDDEN = "forbidden"  # Not allowed under any circumstances


@dataclass
class BudgetConstraint:
    """Enforce minimal budget for tools/platforms only"""

    domain: AgentDomain
    max_budget: float
    allowed_categories: List[str]
    forbidden_categories: List[str]


@dataclass
class ScopeConstraint:
    """Define what agent CAN and CANNOT do"""

    domain: AgentDomain
    permitted_tasks: List[str]
    forbidden_tasks: List[str]
    dependencies: List[AgentDomain]  # Other agents this agent can request help from


@dataclass
class QualityStandard:
    """Quality benchmarks from top universities"""

    domain: AgentDomain
    frameworks: List[str]  # e.g., "MIT Design Thinking", "Stanford d.school"
    metrics: Dict[str, Any]  # Measurable quality criteria
    validation_required: bool


@dataclass
class FinancialGuardRail:
    """Financial safety controls to prevent liability and losses"""

    payment_type: PaymentType
    approval_level: ApprovalLevel
    max_auto_approved_amount: float  # Maximum amount CFO can approve
    requires_user_confirmation: bool
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    liability_warning: Optional[str] = None


@dataclass
class PaymentApprovalWorkflow:
    """Defines approval workflow for payments"""

    payment_type: PaymentType
    required_approvers: List[str]  # e.g., ["CEO", "USER"]
    approval_timeout_hours: int
    auto_reject_on_timeout: bool
    notification_required: bool


# ============================================================================
# GUARD RAIL CONFIGURATIONS
# ============================================================================

BUDGET_CONSTRAINTS = {
    AgentDomain.BRANDING: BudgetConstraint(
        domain=AgentDomain.BRANDING,
        max_budget=150.0,
        allowed_categories=[
            "Design software subscription (Adobe CC, Figma)",
            "Font licenses",
            "Stock imagery for mood boards",
        ],
        forbidden_categories=[
            "External design agencies",
            "Freelance designers",
            "Branding consultants",
            "Design contests",
        ],
    ),
    AgentDomain.WEB_DEVELOPMENT: BudgetConstraint(
        domain=AgentDomain.WEB_DEVELOPMENT,
        max_budget=500.0,
        allowed_categories=[
            "Domain registration",
            "Web hosting (Vercel, Netlify, AWS)",
            "AR platform subscription (8th Wall)",
            "CMS subscription (Sanity.io free tier)",
            "SSL certificates",
        ],
        forbidden_categories=[
            "External web development agencies",
            "Freelance developers",
            "Template marketplace themes",
            "Development bootcamps",
        ],
    ),
    AgentDomain.LEGAL: BudgetConstraint(
        domain=AgentDomain.LEGAL,
        max_budget=500.0,
        allowed_categories=[
            "DBA filing fees",
            "Business registration costs",
            "Trademark search fees",
            "Government processing fees",
        ],
        forbidden_categories=[
            "External law firms",
            "Legal consultants",
            "Paralegal services",
            "Legal document preparation services",
        ],
    ),
    AgentDomain.MARTECH: BudgetConstraint(
        domain=AgentDomain.MARTECH,
        max_budget=200.0,
        allowed_categories=[
            "CRM free tier (HubSpot, Zoho)",
            "Email platform (Mailchimp free tier)",
            "Analytics tools (Google Analytics free)",
            "Zapier starter plan (optional)",
            "Minimal paid features",
        ],
        forbidden_categories=[
            "Marketing automation consultants",
            "CRM implementation agencies",
            "Integration specialists",
            "MarTech advisors",
        ],
    ),
    AgentDomain.CONTENT: BudgetConstraint(
        domain=AgentDomain.CONTENT,
        max_budget=150.0,
        allowed_categories=[
            "Canva Pro subscription",
            "Stock photos/videos",
            "Audio/music licenses",
            "Screen recording software",
        ],
        forbidden_categories=[
            "External content agencies",
            "Freelance writers",
            "Videographers",
            "Photographers",
            "Copywriters",
        ],
    ),
    AgentDomain.CAMPAIGNS: BudgetConstraint(
        domain=AgentDomain.CAMPAIGNS,
        max_budget=3000.0,
        allowed_categories=[
            "Google Ads spend",
            "Meta Ads spend",
            "LinkedIn Ads (if B2B)",
            "Ad platform fees",
        ],
        forbidden_categories=[
            "Marketing agencies",
            "Media buying consultants",
            "Ad creative agencies",
            "Campaign strategists",
        ],
    ),
    AgentDomain.SECURITY: BudgetConstraint(
        domain=AgentDomain.SECURITY,
        max_budget=400.0,
        allowed_categories=[
            "Security scanning and analysis tooling",
            "Educational security platform subscriptions",
            "Monitoring and alerting tools",
            "Testnet security experimentation resources",
        ],
        forbidden_categories=[
            "External security consultants",
            "Freelance auditors",
            "Bug bounty payouts without user approval",
            "Managed SOC outsourcing contracts",
        ],
    ),
}


SCOPE_CONSTRAINTS = {
    AgentDomain.BRANDING: ScopeConstraint(
        domain=AgentDomain.BRANDING,
        permitted_tasks=[
            "Design logos and visual identity systems",
            "Create brand guidelines and style guides",
            "Develop color palettes and typography systems",
            "Design business cards, letterhead, templates",
            "Create brand application mockups",
            "Conduct trademark searches",
            "Develop brand messaging and positioning",
        ],
        forbidden_tasks=[
            "Write website code",
            "Configure marketing automation",
            "File legal documents",
            "Run advertising campaigns",
            "Provide financial advice",
        ],
        dependencies=[AgentDomain.CFO],  # Can request budget approvals
    ),
    AgentDomain.WEB_DEVELOPMENT: ScopeConstraint(
        domain=AgentDomain.WEB_DEVELOPMENT,
        permitted_tasks=[
            "Write production-ready code (HTML, CSS, JavaScript, React, Next.js)",
            "Implement AR features with 8th Wall and Three.js",
            "Set up hosting and deployment",
            "Configure CDN and performance optimization",
            "Implement SEO best practices",
            "Set up analytics and tracking",
            "Create responsive designs",
            "Develop CMS integrations",
        ],
        forbidden_tasks=[
            "Design logos or brand identity",
            "Write marketing copy or content strategy",
            "Configure CRM systems",
            "Provide legal compliance advice",
            "Manage advertising budgets",
        ],
        dependencies=[AgentDomain.BRANDING, AgentDomain.CONTENT, AgentDomain.CFO],
    ),
    AgentDomain.LEGAL: ScopeConstraint(
        domain=AgentDomain.LEGAL,
        permitted_tasks=[
            "Prepare DBA registration documents",
            "Conduct trademark searches",
            "Draft business formation documents",
            "Create compliance checklists",
            "Research regulatory requirements",
            "Prepare contract templates",
            "Handle document filing processes",
        ],
        forbidden_tasks=[
            "Provide official legal advice (not a law firm)",
            "Represent client in court",
            "Design logos or websites",
            "Create marketing campaigns",
            "Manage budgets",
        ],
        dependencies=[AgentDomain.CFO],
    ),
    AgentDomain.MARTECH: ScopeConstraint(
        domain=AgentDomain.MARTECH,
        permitted_tasks=[
            "Configure CRM systems (HubSpot, Zoho)",
            "Set up email marketing automation",
            "Implement analytics tracking",
            "Create automation workflows",
            "Configure integration tools (Zapier)",
            "Set up conversion tracking",
            "Implement lead scoring systems",
        ],
        forbidden_tasks=[
            "Write website code (that's Web Dev)",
            "Create content or copy",
            "Design brand assets",
            "Manage ad campaigns",
            "File legal documents",
        ],
        dependencies=[AgentDomain.WEB_DEVELOPMENT, AgentDomain.CONTENT, AgentDomain.CFO],
    ),
    AgentDomain.CONTENT: ScopeConstraint(
        domain=AgentDomain.CONTENT,
        permitted_tasks=[
            "Write marketing copy and website content",
            "Create video scripts and storyboards",
            "Produce graphic designs for social media",
            "Develop content calendars",
            "Create email newsletters",
            "Write blog posts and articles",
            "Develop SEO-optimized content",
        ],
        forbidden_tasks=[
            "Code websites or applications",
            "Configure CRM systems",
            "Design logos (that's Branding)",
            "Manage advertising budgets",
            "Provide legal advice",
        ],
        dependencies=[AgentDomain.BRANDING, AgentDomain.MARTECH, AgentDomain.CFO],
    ),
    AgentDomain.CAMPAIGNS: ScopeConstraint(
        domain=AgentDomain.CAMPAIGNS,
        permitted_tasks=[
            "Create ad copy and creative assets",
            "Set up Google Ads campaigns",
            "Configure Meta Ads campaigns",
            "Develop targeting strategies",
            "Implement A/B testing",
            "Monitor and optimize campaign performance",
            "Create landing pages",
            "Analyze campaign data and ROI",
        ],
        forbidden_tasks=[
            "Design brand identity (that's Branding)",
            "Code the main website (that's Web Dev)",
            "Configure CRM (that's MarTech)",
            "File legal documents",
            "Create long-form content (that's Content)",
        ],
        dependencies=[
            AgentDomain.BRANDING,
            AgentDomain.WEB_DEVELOPMENT,
            AgentDomain.CONTENT,
            AgentDomain.MARTECH,
            AgentDomain.CFO,
        ],
    ),
    AgentDomain.SECURITY: ScopeConstraint(
        domain=AgentDomain.SECURITY,
        permitted_tasks=[
            "Run static security reviews on backend and frontend",
            "Perform smart contract threat modeling and checklist audits",
            "Validate secure headers, auth controls, and input validation paths",
            "Design security test plans and incident response playbooks",
            "Curate security education and upskilling roadmaps",
        ],
        forbidden_tasks=[
            "Approve production payments autonomously",
            "Disable security controls for convenience",
            "Deploy unreviewed contract code to mainnet",
            "Bypass user consent for risk-bearing operations",
        ],
        dependencies=[AgentDomain.WEB_DEVELOPMENT, AgentDomain.LEGAL, AgentDomain.CFO],
    ),
}


QUALITY_STANDARDS = {
    AgentDomain.BRANDING: QualityStandard(
        domain=AgentDomain.BRANDING,
        frameworks=[
            "Golden Ratio (1.618) in design",
            "RISD Design Principles",
            "Stanford d.school Design Thinking",
            "Gestalt Principles of Visual Perception",
        ],
        metrics={
            "scalability": "Logo must work from 16px to building signage",
            "color_accessibility": "WCAG AA compliant color contrast ratios",
            "file_formats": "Vector (SVG, AI, EPS) + Raster (PNG, JPG) deliverables",
            "brand_guideline_completeness": "40+ page comprehensive guide",
            "concept_variety": "Minimum 3-4 distinct design directions",
        },
        validation_required=True,
    ),
    AgentDomain.WEB_DEVELOPMENT: QualityStandard(
        domain=AgentDomain.WEB_DEVELOPMENT,
        frameworks=[
            "MIT 6.170 Software Studio",
            "Stanford CS 142 Web Applications",
            "Google Web Vitals",
            "WCAG 2.1 Accessibility Standards",
        ],
        metrics={
            "performance_score": "Lighthouse score ≥ 90",
            "mobile_responsiveness": "100% responsive design",
            "seo_score": "Lighthouse SEO score ≥ 95",
            "accessibility_score": "WCAG AA compliance minimum",
            "code_quality": "TypeScript strict mode, <5% code duplication",
            "test_coverage": "≥ 70% unit test coverage",
        },
        validation_required=True,
    ),
    AgentDomain.LEGAL: QualityStandard(
        domain=AgentDomain.LEGAL,
        frameworks=[
            "Harvard Law Business Law Clinic",
            "Stanford Law Entrepreneurship Program",
            "ABA Model Rules of Professional Conduct",
        ],
        metrics={
            "document_completeness": "All required fields completed accurately",
            "compliance_coverage": "100% regulatory requirements addressed",
            "risk_assessment": "All high/medium risks identified with mitigation",
            "citation_accuracy": "All legal references verified and current",
        },
        validation_required=True,
    ),
    AgentDomain.MARTECH: QualityStandard(
        domain=AgentDomain.MARTECH,
        frameworks=[
            "MIT Sloan Marketing Analytics",
            "Harvard Business School Marketing Strategy",
            "Google Analytics Best Practices",
        ],
        metrics={
            "integration_success": "100% of specified integrations functional",
            "data_accuracy": "Tracking validates against test scenarios",
            "automation_efficiency": "Workflows reduce manual tasks by ≥ 60%",
            "reporting_completeness": "All KPIs trackable in dashboards",
        },
        validation_required=True,
    ),
    AgentDomain.CONTENT: QualityStandard(
        domain=AgentDomain.CONTENT,
        frameworks=[
            "Stanford Writing Center Standards",
            "MIT Comparative Media Studies",
            "Content Marketing Institute Best Practices",
        ],
        metrics={
            "readability_score": "Flesch Reading Ease ≥ 60",
            "seo_optimization": "Target keywords naturally integrated",
            "originality": "100% unique content (no plagiarism)",
            "engagement_quality": "Clear CTAs, scannable formatting",
            "brand_consistency": "Adheres to brand voice guidelines",
        },
        validation_required=True,
    ),
    AgentDomain.CAMPAIGNS: QualityStandard(
        domain=AgentDomain.CAMPAIGNS,
        frameworks=[
            "Harvard Business School Marketing ROI",
            "Stanford GSB Digital Marketing",
            "Google Ads Best Practices",
        ],
        metrics={
            "targeting_precision": "Audience match ≥ 80% relevance score",
            "creative_variety": "Minimum 3 ad variations per campaign",
            "conversion_tracking": "100% of conversion events tracked",
            "budget_efficiency": "CPC within industry benchmarks",
            "testing_rigor": "Statistical significance (p < 0.05) for A/B tests",
        },
        validation_required=True,
    ),
    AgentDomain.SECURITY: QualityStandard(
        domain=AgentDomain.SECURITY,
        frameworks=[
            "OWASP ASVS",
            "NIST SSDF",
            "SCSVS smart contract controls",
            "Threat modeling with STRIDE",
        ],
        metrics={
            "critical_open_findings": "0 before release",
            "security_test_coverage": "Critical paths validated",
            "secrets_hygiene": "No secrets in source control",
            "header_hardening": "CSP + secure defaults validated",
            "contract_controls": "Access control and invariant checks completed",
        },
        validation_required=True,
    ),
}


# ============================================================================
# FINANCIAL GUARD RAILS - PREVENT LIABILITY & FINANCIAL LOSSES
# ============================================================================

FINANCIAL_GUARD_RAILS = {
    PaymentType.API_FEE: FinancialGuardRail(
        payment_type=PaymentType.API_FEE,
        approval_level=ApprovalLevel.AUTO_APPROVED,
        max_auto_approved_amount=100.0,  # CFO can approve up to $100/transaction
        requires_user_confirmation=False,
        risk_level="LOW",
        liability_warning=None,
    ),
    PaymentType.LEGAL_FILING: FinancialGuardRail(
        payment_type=PaymentType.LEGAL_FILING,
        approval_level=ApprovalLevel.AUTO_APPROVED,
        max_auto_approved_amount=500.0,  # CFO can approve government fees
        requires_user_confirmation=False,
        risk_level="LOW",
        liability_warning="Verify filing fee with official government source",
    ),
    PaymentType.SOFTWARE_SUBSCRIPTION: FinancialGuardRail(
        payment_type=PaymentType.SOFTWARE_SUBSCRIPTION,
        approval_level=ApprovalLevel.USER_APPROVAL_REQUIRED,
        max_auto_approved_amount=0.0,  # NO auto-approval
        requires_user_confirmation=True,
        risk_level="MEDIUM",
        liability_warning="Subscriptions create recurring financial obligations",
    ),
    PaymentType.SERVICE_ORDER: FinancialGuardRail(
        payment_type=PaymentType.SERVICE_ORDER,
        approval_level=ApprovalLevel.USER_APPROVAL_REQUIRED,
        max_auto_approved_amount=0.0,  # NO auto-approval
        requires_user_confirmation=True,
        risk_level="HIGH",
        liability_warning="Service orders may create contractual obligations and liability",
    ),
    PaymentType.ADVERTISING_SPEND: FinancialGuardRail(
        payment_type=PaymentType.ADVERTISING_SPEND,
        approval_level=ApprovalLevel.USER_APPROVAL_REQUIRED,
        max_auto_approved_amount=0.0,  # NO auto-approval
        requires_user_confirmation=True,
        risk_level="HIGH",
        liability_warning="Ad spend can be lost if campaigns underperform - requires ROI monitoring",
    ),
    PaymentType.HARDWARE_PURCHASE: FinancialGuardRail(
        payment_type=PaymentType.HARDWARE_PURCHASE,
        approval_level=ApprovalLevel.USER_APPROVAL_REQUIRED,
        max_auto_approved_amount=0.0,  # NO auto-approval
        requires_user_confirmation=True,
        risk_level="MEDIUM",
        liability_warning="Hardware deprecates rapidly - verify necessity",
    ),
    PaymentType.CONTRACTOR_PAYMENT: FinancialGuardRail(
        payment_type=PaymentType.CONTRACTOR_PAYMENT,
        approval_level=ApprovalLevel.FORBIDDEN,
        max_auto_approved_amount=0.0,
        requires_user_confirmation=False,
        risk_level="CRITICAL",
        liability_warning="FORBIDDEN: Agents must execute work, not hire contractors",
    ),
}


# Payment approval workflows
PAYMENT_APPROVAL_WORKFLOWS = {
    PaymentType.API_FEE: PaymentApprovalWorkflow(
        payment_type=PaymentType.API_FEE,
        required_approvers=["CFO"],  # CFO can approve alone
        approval_timeout_hours=0,  # Immediate
        auto_reject_on_timeout=False,
        notification_required=True,  # Notify user of API costs
    ),
    PaymentType.LEGAL_FILING: PaymentApprovalWorkflow(
        payment_type=PaymentType.LEGAL_FILING,
        required_approvers=["CFO"],  # CFO can approve government fees
        approval_timeout_hours=24,
        auto_reject_on_timeout=False,
        notification_required=True,
    ),
    PaymentType.SOFTWARE_SUBSCRIPTION: PaymentApprovalWorkflow(
        payment_type=PaymentType.SOFTWARE_SUBSCRIPTION,
        required_approvers=["CEO", "USER"],  # CEO proposes, User approves
        approval_timeout_hours=72,
        auto_reject_on_timeout=True,  # Auto-reject if user doesn't respond
        notification_required=True,
    ),
    PaymentType.SERVICE_ORDER: PaymentApprovalWorkflow(
        payment_type=PaymentType.SERVICE_ORDER,
        required_approvers=["CEO", "USER"],  # CEO proposes, User approves
        approval_timeout_hours=48,
        auto_reject_on_timeout=True,
        notification_required=True,
    ),
    PaymentType.ADVERTISING_SPEND: PaymentApprovalWorkflow(
        payment_type=PaymentType.ADVERTISING_SPEND,
        required_approvers=["CEO", "USER"],  # CEO proposes, User approves
        approval_timeout_hours=24,
        auto_reject_on_timeout=True,
        notification_required=True,
    ),
    PaymentType.HARDWARE_PURCHASE: PaymentApprovalWorkflow(
        payment_type=PaymentType.HARDWARE_PURCHASE,
        required_approvers=["CEO", "USER"],  # CEO proposes, User approves
        approval_timeout_hours=48,
        auto_reject_on_timeout=True,
        notification_required=True,
    ),
}


# ============================================================================
# GUARD RAIL ENFORCEMENT FUNCTIONS
# ============================================================================


class AgentGuardRail:
    """Enforces constraints and validates agent behavior"""

    def __init__(self, domain: AgentDomain):
        self.domain = domain
        self.budget_constraint = BUDGET_CONSTRAINTS.get(domain)
        self.scope_constraint = SCOPE_CONSTRAINTS.get(domain)
        self.quality_standard = QUALITY_STANDARDS.get(domain)

    def validate_execution_mode(self, action_description: str) -> bool:
        """Ensure agent is EXECUTING, not recommending external vendors"""
        forbidden_phrases = [
            "hire a",
            "contact an agency",
            "find a freelancer",
            "outsource to",
            "work with a consultant",
            "bring in an expert",
            "contract with",
        ]

        for phrase in forbidden_phrases:
            if phrase.lower() in action_description.lower():
                raise ValueError(
                    f"❌ GUARD RAIL VIOLATION: Agent attempted to recommend external vendor.\n"
                    f"   Phrase detected: '{phrase}'\n"
                    f"   Agent MUST execute work, not recommend vendors.\n"
                    f"   Budget is for tools/platforms only."
                )

        return True

    def validate_budget_spend(self, category: str, amount: float) -> bool:
        """Ensure spending stays within constraints"""
        if not self.budget_constraint:
            return True

        # Check if category is forbidden
        if category in self.budget_constraint.forbidden_categories:
            raise ValueError(
                f"❌ BUDGET GUARD RAIL VIOLATION: Attempted to spend on forbidden category.\n"
                f"   Category: {category}\n"
                f"   Amount: ${amount}\n"
                f"   Allowed categories: {', '.join(self.budget_constraint.allowed_categories)}"
            )

        # Check if amount exceeds max budget
        if amount > self.budget_constraint.max_budget:
            raise ValueError(
                f"❌ BUDGET GUARD RAIL VIOLATION: Amount exceeds maximum budget.\n"
                f"   Attempted: ${amount}\n"
                f"   Max allowed: ${self.budget_constraint.max_budget}\n"
                f"   Domain: {self.domain.value}"
            )

        return True

    def validate_task_scope(self, task_description: str) -> bool:
        """Ensure agent stays within permitted task scope"""
        if not self.scope_constraint:
            return True

        # Check for forbidden task indicators
        task_lower = task_description.lower()

        for forbidden_task in self.scope_constraint.forbidden_tasks:
            # Simple keyword matching (can be enhanced with NLP)
            forbidden_keywords = forbidden_task.lower().split()
            if any(keyword in task_lower for keyword in forbidden_keywords if len(keyword) > 4):
                raise ValueError(
                    f"❌ SCOPE GUARD RAIL VIOLATION: Task outside agent's domain.\n"
                    f"   Task: {task_description}\n"
                    f"   Forbidden: {forbidden_task}\n"
                    f"   This agent can only: {', '.join(self.scope_constraint.permitted_tasks[:3])}..."
                )

        return True

    def validate_deliverable_quality(self, deliverable: Dict[str, Any]) -> bool:
        """Validate deliverable meets quality standards"""
        if not self.quality_standard or not self.quality_standard.validation_required:
            return True

        deliverable_type = deliverable.get("type")
        quality_metrics = deliverable.get("quality_metrics", {})

        # Check each required metric
        for metric_name, required_value in self.quality_standard.metrics.items():
            actual_value = quality_metrics.get(metric_name)

            if actual_value is None:
                raise ValueError(
                    f"❌ QUALITY GUARD RAIL VIOLATION: Missing required quality metric.\n"
                    f"   Metric: {metric_name}\n"
                    f"   Required: {required_value}\n"
                    f"   Standard: {self.quality_standard.frameworks[0]}"
                )

        return True

    def get_permitted_tasks(self) -> List[str]:
        """Return list of tasks this agent CAN perform"""
        if self.scope_constraint:
            return self.scope_constraint.permitted_tasks
        return []

    def get_dependencies(self) -> List[AgentDomain]:
        """Return other agents this agent can request help from"""
        if self.scope_constraint:
            return self.scope_constraint.dependencies
        return []

    def validate_payment_request(
        self, payment_type: PaymentType, amount: float, description: str
    ) -> Dict[str, Any]:
        """
        Validate payment request against financial guard rails

        Returns:
            {
                "approved": bool,
                "approval_level": ApprovalLevel,
                "requires_user_approval": bool,
                "risk_level": str,
                "liability_warning": Optional[str],
                "recommendation": str
            }
        """
        guard_rail = FINANCIAL_GUARD_RAILS.get(payment_type)

        if not guard_rail:
            return {
                "approved": False,
                "approval_level": ApprovalLevel.USER_APPROVAL_REQUIRED,
                "requires_user_approval": True,
                "risk_level": "UNKNOWN",
                "liability_warning": "Unknown payment type - requires user approval",
                "recommendation": "DENY - Unknown payment type",
            }

        # Check if payment type is forbidden
        if guard_rail.approval_level == ApprovalLevel.FORBIDDEN:
            raise ValueError(
                f"❌ FINANCIAL GUARD RAIL VIOLATION: Forbidden payment type.\n"
                f"   Payment Type: {payment_type.value}\n"
                f"   Amount: ${amount:,.2f}\n"
                f"   Description: {description}\n"
                f"   Reason: {guard_rail.liability_warning}"
            )

        # Check if payment requires user approval
        if guard_rail.approval_level == ApprovalLevel.USER_APPROVAL_REQUIRED:
            return {
                "approved": False,  # Not auto-approved
                "approval_level": ApprovalLevel.USER_APPROVAL_REQUIRED,
                "requires_user_approval": True,
                "risk_level": guard_rail.risk_level,
                "liability_warning": guard_rail.liability_warning,
                "recommendation": "REQUIRES USER APPROVAL - Financial commitment pending user confirmation",
            }

        # Check if amount exceeds auto-approval limit
        if amount > guard_rail.max_auto_approved_amount:
            return {
                "approved": False,
                "approval_level": ApprovalLevel.USER_APPROVAL_REQUIRED,
                "requires_user_approval": True,
                "risk_level": "HIGH",
                "liability_warning": f"Amount ${amount:,.2f} exceeds CFO auto-approval limit of ${guard_rail.max_auto_approved_amount:,.2f}",
                "recommendation": "ESCALATE TO USER - Amount too high for auto-approval",
            }

        # Payment can be auto-approved by CFO
        return {
            "approved": True,
            "approval_level": ApprovalLevel.AUTO_APPROVED,
            "requires_user_approval": False,
            "risk_level": guard_rail.risk_level,
            "liability_warning": guard_rail.liability_warning,
            "recommendation": f"APPROVE - CFO can authorize {payment_type.value} up to ${guard_rail.max_auto_approved_amount:,.2f}",
        }

    def get_payment_approval_workflow(
        self, payment_type: PaymentType
    ) -> Optional[PaymentApprovalWorkflow]:
        """Get the approval workflow for a payment type"""
        return PAYMENT_APPROVAL_WORKFLOWS.get(payment_type)

    def check_liability_risk(self, action_description: str) -> List[str]:
        """
        Check if action creates potential liability or financial risk

        Returns list of warnings
        """
        warnings = []

        # Check for liability keywords
        liability_indicators = {
            "contract": "Contracts create legal obligations and potential liability",
            "agreement": "Agreements may have legal binding effects",
            "purchase": "Purchases are financial commitments - ensure necessary",
            "subscription": "Subscriptions create recurring obligations",
            "hire": "FORBIDDEN - Hiring creates employer liability",
            "employ": "FORBIDDEN - Employment creates legal obligations",
            "pay contractor": "FORBIDDEN - Contractor payments outside agent authority",
        }

        action_lower = action_description.lower()
        for keyword, warning in liability_indicators.items():
            if keyword in action_lower:
                warnings.append(warning)

        return warnings

    def enforce_execution_model(self, state: Dict) -> Dict:
        """Apply all guard rails before agent executes"""
        task_description = state.get("task_description", "")

        # 1. Validate execution mode (must execute, not recommend)
        self.validate_execution_mode(task_description)

        # 2. Validate task is within scope
        self.validate_task_scope(task_description)

        # 3. Add quality standards to state
        state["quality_standards"] = self.quality_standard.metrics if self.quality_standard else {}
        state["required_frameworks"] = (
            self.quality_standard.frameworks if self.quality_standard else []
        )

        # 4. Add budget constraints
        state["max_budget"] = self.budget_constraint.max_budget if self.budget_constraint else 0
        state["allowed_spend_categories"] = (
            self.budget_constraint.allowed_categories if self.budget_constraint else []
        )

        return state


# ============================================================================
# EXECUTION VALIDATORS
# ============================================================================


def validate_agent_output(domain: AgentDomain, output: Dict) -> Dict:
    """Validate that agent output is execution-focused, not recommendations"""

    guard_rail = AgentGuardRail(domain)

    # Check deliverables are production-ready
    deliverables = output.get("deliverables", [])
    if not deliverables:
        raise ValueError(
            f"❌ OUTPUT VALIDATION FAILED: No deliverables produced.\n"
            f"   Agent must produce production-ready outputs, not just recommendations."
        )

    # Check for recommendation language (should be minimal)
    recommendations = output.get("recommendations", [])
    for rec in recommendations:
        if any(phrase in rec.lower() for phrase in ["hire", "contact", "outsource", "agency"]):
            raise ValueError(
                f"❌ OUTPUT VALIDATION FAILED: Recommendation suggests external vendor.\n"
                f"   Recommendation: {rec}\n"
                f"   Agent must execute work internally."
            )

    # Validate budget usage
    budget_used = output.get("budget_used", 0)
    if budget_used > guard_rail.budget_constraint.max_budget:
        raise ValueError(
            f"❌ OUTPUT VALIDATION FAILED: Budget exceeded.\n"
            f"   Used: ${budget_used}\n"
            f"   Max: ${guard_rail.budget_constraint.max_budget}"
        )

    return output


def create_execution_summary(domain: AgentDomain) -> str:
    """Generate summary of what agent CAN do (for user clarity)"""
    guard_rail = AgentGuardRail(domain)

    summary = f"""
🤖 {domain.value.upper().replace('_', ' ')} AGENT - EXECUTION CAPABILITIES

✅ THIS AGENT PERFORMS (does not recommend vendors):
"""
    for task in guard_rail.get_permitted_tasks():
        summary += f"   • {task}\n"

    summary += f"""
💰 BUDGET CONSTRAINT: ${guard_rail.budget_constraint.max_budget if guard_rail.budget_constraint else 0}
   Allowed spending:
"""
    if guard_rail.budget_constraint:
        for category in guard_rail.budget_constraint.allowed_categories:
            summary += f"   • {category}\n"

    summary += f"""
📊 QUALITY STANDARDS:
"""
    if guard_rail.quality_standard:
        for framework in guard_rail.quality_standard.frameworks:
            summary += f"   • {framework}\n"

    return summary


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example: Validate Branding Agent execution
    branding_guard = AgentGuardRail(AgentDomain.BRANDING)

    # Test 1: Valid execution
    try:
        branding_guard.validate_execution_mode(
            "Design 4 logo concepts using Golden Ratio principles"
        )
        print("✅ Valid execution mode")
    except ValueError as e:
        print(e)

    # Test 2: Invalid - recommending vendor
    try:
        branding_guard.validate_execution_mode("Hire a branding agency to create the logo")
        print("✅ Valid execution mode")
    except ValueError as e:
        print(e)

    # Test 3: Budget validation
    try:
        branding_guard.validate_budget_spend(
            "Design software subscription (Adobe CC, Figma)", 120.0
        )
        print("✅ Valid budget spend")
    except ValueError as e:
        print(e)

    # Test 4: Invalid budget
    try:
        branding_guard.validate_budget_spend("External design agencies", 10000.0)
        print("✅ Valid budget spend")
    except ValueError as e:
        print(e)

    # Print execution summary
    print(create_execution_summary(AgentDomain.BRANDING))
