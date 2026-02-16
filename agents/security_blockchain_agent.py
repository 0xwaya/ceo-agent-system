"""Software + Blockchain Security Specialist Agent.

Provides high-signal security review capabilities for backend/frontend code and
curated security learning guidance, including smart contract security tracks.
Knowledge profile is aligned to the project date context (Feb 2026).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List
import re


@dataclass
class SecurityFinding:
    severity: str
    area: str
    title: str
    detail: str
    file_path: str


class SecurityBlockchainAgent:
    """Specialized agent for software + blockchain security operations."""

    def __init__(self):
        self.name = "Software & Blockchain Security Specialist"
        self.expertise_area = "Software Security + Blockchain Security"
        self.capabilities = [
            "Static security review for backend/frontend attack surface",
            "Smart-contract security checklist (EVM threat models + exploit classes)",
            "Security architecture hardening recommendations",
            "Operational security readiness before API key onboarding",
            "Learning roadmap from top software/Web3 security education platforms",
            "Best-practice guidance for secure SDLC, CI, and incident readiness",
        ]
        self.knowledge_as_of = "2026-02"

    def get_best_practices(self) -> Dict[str, List[str]]:
        """Return software and Web3 security best-practice checklists."""
        return {
            "software_security": [
                "Adopt OWASP ASVS controls for auth, session, and input validation",
                "Use strict CSP, secure cookie flags, and CSRF defenses",
                "Run SAST + dependency/CVE scanning in CI before merge",
                "Enforce least privilege for secrets, tokens, and infrastructure IAM",
                "Add threat modeling and abuse-case reviews to sprint planning",
            ],
            "web3_security": [
                "Apply checks-effects-interactions and reentrancy protections",
                "Constrain privileged functions with role-based access controls",
                "Use invariant testing, fuzzing, and differential testing for contracts",
                "Validate upgradeability safety (storage layout, initializer guards)",
                "Require independent audit + bounty window before mainnet deployment",
            ],
            "operational_security": [
                "Maintain incident runbooks with severity triage and comms pathways",
                "Enable centralized logging, alerting, and tamper-evident audit trails",
                "Rotate credentials regularly and immediately after suspected exposure",
                "Gate production rollouts with security review checklists",
            ],
        }

    def get_learning_sources(self) -> Dict[str, Any]:
        """Return curated learning platforms and study tracks."""
        return {
            "as_of": self.knowledge_as_of,
            "platforms": [
                {
                    "name": "Cyfrin",
                    "focus": "Solidity, smart contract auditing, protocol security",
                    "tracks": [
                        "Smart contract security fundamentals",
                        "Foundry-based testing and invariant fuzzing",
                        "Audit methodology and contest workflows",
                    ],
                },
                {
                    "name": "Secureum",
                    "focus": "Ethereum protocol and smart contract security deep dives",
                    "tracks": [
                        "Security bootcamps",
                        "EVM internals and exploit patterns",
                        "Advanced audit war-room practices",
                    ],
                },
                {
                    "name": "OpenZeppelin Docs + Forum",
                    "focus": "Secure contract patterns, upgradeability, access control",
                    "tracks": [
                        "Upgradeable contracts",
                        "Defender operations",
                        "Best-practice standards",
                    ],
                },
                {
                    "name": "PortSwigger Web Security Academy",
                    "focus": "Web app vulnerabilities and exploit labs",
                    "tracks": [
                        "XSS/CSRF/SSRF",
                        "Auth/session flaws",
                        "Advanced deserialization and request smuggling",
                    ],
                },
                {
                    "name": "Damn Vulnerable DeFi + Ethernaut",
                    "focus": "Hands-on vulnerable contract exploitation labs",
                    "tracks": [
                        "DeFi exploit classes",
                        "Privilege/escalation and price-oracle attacks",
                        "Challenge-based red-team practice",
                    ],
                },
                {
                    "name": "Trail of Bits Blog + Building Secure Contracts",
                    "focus": "Advanced smart contract reviews and secure coding patterns",
                    "tracks": [
                        "Formal threat modeling for protocols",
                        "Common audit findings and remediation patterns",
                        "Testing and verification workflows",
                    ],
                },
                {
                    "name": "Consensys Diligence Knowledge Base",
                    "focus": "EVM security techniques, fuzzing, and audit heuristics",
                    "tracks": [
                        "Fuzzing strategies for Solidity",
                        "Secure architecture reviews",
                        "Postmortem-driven hardening",
                    ],
                },
            ],
            "datasets_and_feeds": [
                "SWC Registry (smart contract weakness classes)",
                "DASP Top 10",
                "OWASP ASVS + MASVS + API Security Top 10",
                "NVD/CVE feeds for dependency tracking",
                "Immunefi incident disclosures",
                "Rekt News incident corpus for exploit pattern analysis",
                "SCSVS (Smart Contract Security Verification Standard)",
            ],
            "tooling_best_practice_stack": [
                "Semgrep/Bandit for Python SAST",
                "pip-audit/Safety for dependency vulnerability checks",
                "Slither + Mythril for Solidity static analysis",
                "Foundry fuzz/invariant tests + Echidna campaigns",
                "OpenZeppelin Defender for operations and access controls",
            ],
        }

    def run_security_review(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run a focused static review of backend/frontend/security posture."""
        project_root = Path(state.get("project_root") or Path(__file__).resolve().parents[1])
        findings: List[SecurityFinding] = []
        upgrades: List[str] = []

        app_file = project_root / "app.py"
        if app_file.exists():
            app_content = app_file.read_text(encoding="utf-8")

            if "Content-Security-Policy" in app_content:
                upgrades.append("Security headers already include CSP and defensive defaults")
            else:
                findings.append(
                    SecurityFinding(
                        severity="high",
                        area="backend",
                        title="Missing CSP header",
                        detail="Add Content-Security-Policy with explicit script/style/connect sources.",
                        file_path="app.py",
                    )
                )

            if "SESSION_COOKIE_HTTPONLY" not in app_content:
                findings.append(
                    SecurityFinding(
                        severity="medium",
                        area="backend",
                        title="Cookie security flags not explicitly set",
                        detail="Set SESSION_COOKIE_HTTPONLY, SESSION_COOKIE_SAMESITE, and prod-only secure cookies.",
                        file_path="app.py",
                    )
                )

        templates_dir = project_root / "templates"
        if templates_dir.exists():
            for html_file in templates_dir.glob("*.html"):
                content = html_file.read_text(encoding="utf-8")
                if "<html" in content and "<html lang=" not in content:
                    findings.append(
                        SecurityFinding(
                            severity="low",
                            area="frontend",
                            title="Missing html lang attribute",
                            detail="Set lang attribute for accessibility and scanner hygiene.",
                            file_path=str(html_file.relative_to(project_root)),
                        )
                    )

        static_js_dir = project_root / "static" / "js"
        if static_js_dir.exists():
            for js_file in static_js_dir.glob("*.js"):
                js_content = js_file.read_text(encoding="utf-8")
                if re.search(r"innerHTML\s*=", js_content):
                    findings.append(
                        SecurityFinding(
                            severity="medium",
                            area="frontend",
                            title="Potential DOM injection sink",
                            detail="Prefer textContent or sanitize untrusted values before assigning innerHTML.",
                            file_path=str(js_file.relative_to(project_root)),
                        )
                    )

        summary = {
            "review_date": date.today().isoformat(),
            "knowledge_as_of": self.knowledge_as_of,
            "security_domains": ["software_security", "web3_security", "operational_security"],
            "total_findings": len(findings),
            "findings": [finding.__dict__ for finding in findings],
            "upgrades_identified": upgrades,
            "learning_sources": self.get_learning_sources(),
            "best_practices": self.get_best_practices(),
            "next_actions": [
                "Resolve high/medium findings before adding live API secrets",
                "Enable dependency scanning in CI with CVE alerts",
                "Run blockchain-specific test suites before on-chain integrations",
            ],
        }
        return summary
