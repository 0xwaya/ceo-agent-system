"""
Interactive Multi-Agent Chat Interface

An advanced interactive chat system that allows real-time conversation with:
- Individual specialized agents (Legal, Branding, Web Dev, etc.)
- Multiple agents simultaneously (roundtable discussion)
- CFO orchestrator for strategic guidance
- Dynamic agent invocation based on conversation context

Features:
- Natural language interaction
- Context-aware agent suggestions
- Multi-agent collaboration
- Session memory and history
- Rich formatting and visual feedback
"""

import sys
import os
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime

# Import specialized agents
from agents.specialized_agents import (
    AgentFactory,
    BrandingAgent,
    WebDevelopmentAgent,
    LegalComplianceAgent,
    BrandingAgentState,
    WebDevAgentState,
    LegalAgentState,
)

from agents.agent_knowledge_base import get_expertise, get_all_expertise_areas


# ============================================================================
# CHAT SESSION STATE
# ============================================================================


@dataclass
class ChatMessage:
    """Represents a single chat message"""

    speaker: str  # "user", "cfo", "branding", "legal", etc.
    content: str
    timestamp: datetime
    agent_type: Optional[str] = None


class ChatSession:
    """Manages the interactive chat session"""

    def __init__(self):
        self.messages: List[ChatMessage] = []
        self.active_agents: Set[str] = set()
        self.context: Dict = {
            "company_name": "",
            "industry": "",
            "location": "",
            "objectives": [],
            "budget": 0.0,
        }
        self.session_start = datetime.now()

    def add_message(self, speaker: str, content: str, agent_type: Optional[str] = None):
        """Add a message to the chat history"""
        msg = ChatMessage(
            speaker=speaker, content=content, timestamp=datetime.now(), agent_type=agent_type
        )
        self.messages.append(msg)

    def get_history(self, last_n: int = 10) -> List[ChatMessage]:
        """Get recent chat history"""
        return self.messages[-last_n:]

    def invoke_agent(self, agent_type: str):
        """Add an agent to the active conversation"""
        self.active_agents.add(agent_type)

    def dismiss_agent(self, agent_type: str):
        """Remove an agent from the conversation"""
        self.active_agents.discard(agent_type)

    def clear_agents(self):
        """Clear all active agents"""
        self.active_agents.clear()


# ============================================================================
# CHAT INTERFACE
# ============================================================================


class InteractiveChatInterface:
    """Main interactive chat interface"""

    def __init__(self):
        self.session = ChatSession()
        self.factory = AgentFactory()
        self.running = True

        # Agent emoji mapping for visual appeal
        self.agent_emoji = {
            "cfo": "💼",
            "branding": "🎨",
            "web_development": "💻",
            "legal": "⚖️",
            "martech": "📊",
            "content": "📸",
            "campaigns": "🚀",
            "user": "👤",
        }

        # Agent descriptions
        self.agent_info = {
            "cfo": "CFO Agent - Strategic planning, budget management, orchestration",
            "branding": "Branding Agent - Logo design, visual identity, brand strategy",
            "web_development": "Web Dev Agent - Website development, AR integration, tech stack",
            "legal": "Legal Agent - DBA registration, compliance, trademark filing",
            "martech": "MarTech Agent - CRM setup, analytics, marketing automation",
            "content": "Content Agent - Video, photography, case studies, SEO content",
            "campaigns": "Campaign Agent - Media planning, ad campaigns, optimization",
        }

    def print_header(self):
        """Print the chat interface header"""
        os.system("clear" if os.name == "posix" else "cls")
        print("=" * 80)
        print("🤖 MULTI-AGENT INTERACTIVE CHAT SYSTEM")
        print("=" * 80)
        print("Chat with specialized AI agents powered by master-level expertise")
        print("from MIT, Stanford, Harvard, RISD, CMU, and top industry leaders")
        print("=" * 80)

        if self.session.active_agents:
            print(f"\n🎯 Active Agents: ", end="")
            for agent in sorted(self.session.active_agents):
                emoji = self.agent_emoji.get(agent, "🤖")
                print(f"{emoji} {agent.replace('_', ' ').title()}  ", end="")
            print("\n")
        else:
            print("\n💡 No agents active. Use '@agent' to invoke or '/help' for commands\n")

    def print_help(self):
        """Print help information"""
        print("\n" + "=" * 80)
        print("📖 HELP & COMMANDS")
        print("=" * 80)

        print("\n🔹 Chat Commands:")
        print("  /help              - Show this help message")
        print("  /agents            - List all available agents")
        print("  /active            - Show currently active agents")
        print("  /invoke <agent>    - Add an agent to the conversation")
        print("  /dismiss <agent>   - Remove an agent from the conversation")
        print("  /all               - Invoke all agents (roundtable discussion)")
        print("  /clear             - Clear all active agents")
        print("  /history           - Show recent conversation history")
        print("  /context           - Show current session context")
        print("  /reset             - Reset the entire session")
        print("  /exit or /quit     - Exit the chat")

        print("\n🔹 Quick Actions:")
        print("  @cfo               - Mention CFO agent directly")
        print("  @branding          - Mention Branding agent directly")
        print("  @legal             - Mention Legal agent directly")
        print("  @web               - Mention Web Development agent")
        print("  @all               - Address all active agents")

        print("\n🔹 Available Agents:")
        for agent_type, description in self.agent_info.items():
            emoji = self.agent_emoji.get(agent_type, "🤖")
            print(f"  {emoji} {description}")

        print("\n" + "=" * 80)

    def list_agents(self):
        """List all available agents"""
        print("\n" + "=" * 80)
        print("🤖 AVAILABLE SPECIALIZED AGENTS")
        print("=" * 80)

        for agent_type, description in self.agent_info.items():
            emoji = self.agent_emoji.get(agent_type, "🤖")
            status = "✅ ACTIVE" if agent_type in self.session.active_agents else "⚪ Available"
            print(f"\n{emoji} {agent_type.replace('_', ' ').upper()}")
            print(f"   {description}")
            print(f"   Status: {status}")

            # Show expertise info if agent is invokable
            if agent_type in ["branding", "web_development", "legal"]:
                try:
                    agent = self.factory.create_agent(agent_type)
                    print(f"   Capabilities: {', '.join(agent.capabilities[:3])}...")
                except:
                    pass

        print("\n" + "=" * 80)

    def show_context(self):
        """Display current session context"""
        print("\n" + "=" * 80)
        print("📋 SESSION CONTEXT")
        print("=" * 80)

        ctx = self.session.context
        print(f"\nCompany: {ctx.get('company_name', 'Not set')}")
        print(f"Industry: {ctx.get('industry', 'Not set')}")
        print(f"Location: {ctx.get('location', 'Not set')}")
        print(f"Budget: ${ctx.get('budget', 0):,.0f}")

        objectives = ctx.get("objectives", [])
        if objectives:
            print(f"\nObjectives ({len(objectives)}):")
            for i, obj in enumerate(objectives, 1):
                print(f"  {i}. {obj}")
        else:
            print("\nObjectives: None set")

        print(
            f"\nSession Duration: {(datetime.now() - self.session.session_start).seconds // 60} minutes"
        )
        print(f"Messages: {len(self.session.messages)}")
        print("\n" + "=" * 80)

    def show_history(self):
        """Display recent conversation history"""
        print("\n" + "=" * 80)
        print("💬 RECENT CONVERSATION HISTORY")
        print("=" * 80)

        history = self.session.get_history(last_n=15)

        for msg in history:
            emoji = self.agent_emoji.get(msg.speaker, "💬")
            timestamp = msg.timestamp.strftime("%H:%M:%S")
            speaker = msg.speaker.replace("_", " ").title()

            print(f"\n[{timestamp}] {emoji} {speaker}:")
            # Wrap long messages
            content_lines = msg.content.split("\n")
            for line in content_lines[:3]:  # Show first 3 lines
                print(f"  {line}")
            if len(content_lines) > 3:
                print(f"  ... ({len(content_lines) - 3} more lines)")

        print("\n" + "=" * 80)

    def invoke_agent_interactive(self, agent_type: str):
        """Invoke an agent interactively"""
        agent_type = agent_type.lower().strip()

        # Handle aliases
        aliases = {
            "web": "web_development",
            "webdev": "web_development",
            "brand": "branding",
            "marketing": "martech",
            "campaign": "campaigns",
        }
        agent_type = aliases.get(agent_type, agent_type)

        if agent_type in self.agent_info:
            self.session.invoke_agent(agent_type)
            emoji = self.agent_emoji.get(agent_type, "🤖")
            print(
                f"\n{emoji} {agent_type.replace('_', ' ').title()} agent joined the conversation!"
            )
            self.session.add_message("system", f"{agent_type} agent joined", agent_type)

            # Agent introduction
            self.agent_introduction(agent_type)
        else:
            print(f"\n❌ Unknown agent type: {agent_type}")
            print("Use /agents to see available agents")

    def agent_introduction(self, agent_type: str):
        """Agent introduces itself when joining"""
        emoji = self.agent_emoji.get(agent_type, "🤖")

        intros = {
            "cfo": "Hello! I'm the CFO Agent. I specialize in strategic planning, budget management, and orchestrating specialized teams. How can I help you achieve your business objectives?",
            "branding": "Hi there! I'm the Branding Agent, trained in design principles from RISD and Stanford. I can help with logo design, visual identity systems, brand strategy, and positioning. What branding challenges can I solve for you?",
            "web_development": "Hey! I'm the Web Development Agent with expertise from MIT and CMU. I specialize in Next.js, AR integration, performance optimization, and modern web architectures. Need help with your digital presence?",
            "legal": "Good day! I'm the Legal & Compliance Agent. I can assist with DBA registration, trademark searches, business licensing, and legal compliance. What legal matters can I help you navigate?",
            "martech": "Hello! I'm the Marketing Technology Agent. I can help set up your CRM, analytics, marketing automation, and integrate your entire martech stack. What systems do you need?",
            "content": "Hi! I'm the Content Strategy Agent. I specialize in video production, photography, case studies, and SEO content. Let's create compelling content that converts!",
            "campaigns": "Hey there! I'm the Campaign Strategy Agent. I can help plan and execute multi-channel campaigns, optimize ad spend, and drive measurable results. Ready to launch?",
        }

        intro = intros.get(
            agent_type, f"Hello! I'm the {agent_type.replace('_', ' ').title()} agent."
        )
        print(f"\n{emoji} {agent_type.replace('_', ' ').title()}: {intro}\n")

    def process_user_message(self, message: str) -> bool:
        """Process user message and generate responses"""

        # Check for commands
        if message.startswith("/"):
            return self.handle_command(message)

        # Add user message to history
        self.session.add_message("user", message)

        # Check for @mentions
        mentioned_agents = self.extract_mentions(message)
        for agent in mentioned_agents:
            if agent not in self.session.active_agents:
                self.invoke_agent_interactive(agent)

        # Generate responses from active agents
        if self.session.active_agents:
            self.generate_agent_responses(message)
        else:
            print(
                "\n💡 Tip: Invoke an agent with /invoke <agent> or @agent to get expert responses!"
            )

        return True

    def extract_mentions(self, message: str) -> List[str]:
        """Extract @mentions from message"""
        words = message.split()
        mentions = []

        for word in words:
            if word.startswith("@"):
                agent = word[1:].lower().strip(",.!?")
                if agent == "all":
                    return list(self.agent_info.keys())
                elif agent in self.agent_info or agent in ["web", "brand", "marketing"]:
                    mentions.append(agent)

        return mentions

    def generate_agent_responses(self, user_message: str):
        """Generate contextual responses from active agents"""

        # Analyze message for keywords to determine which agents should respond
        responding_agents = self.determine_responding_agents(user_message)

        if not responding_agents:
            # If no specific match, let all active agents respond briefly
            responding_agents = list(self.session.active_agents)

        for agent_type in responding_agents:
            self.generate_single_agent_response(agent_type, user_message)

    def determine_responding_agents(self, message: str) -> List[str]:
        """Determine which agents should respond based on message content"""
        message_lower = message.lower()
        responding = []

        # Keyword mapping
        keywords = {
            "branding": [
                "logo",
                "brand",
                "design",
                "visual",
                "identity",
                "color",
                "typography",
                "style guide",
            ],
            "web_development": [
                "website",
                "web",
                "ar",
                "augmented reality",
                "app",
                "development",
                "code",
                "tech",
            ],
            "legal": [
                "legal",
                "dba",
                "trademark",
                "registration",
                "compliance",
                "license",
                "contract",
            ],
            "martech": ["crm", "analytics", "marketing tech", "automation", "tracking", "email"],
            "content": ["content", "video", "photo", "photography", "case study", "blog", "seo"],
            "campaigns": [
                "campaign",
                "ads",
                "advertising",
                "facebook",
                "google ads",
                "launch",
                "marketing",
            ],
            "cfo": ["budget", "cost", "strategy", "plan", "timeline", "roi", "investment"],
        }

        for agent_type, agent_keywords in keywords.items():
            if agent_type in self.session.active_agents:
                if any(keyword in message_lower for keyword in agent_keywords):
                    responding.append(agent_type)

        return responding

    def generate_single_agent_response(self, agent_type: str, user_message: str):
        """Generate response from a single agent"""
        emoji = self.agent_emoji.get(agent_type, "🤖")
        agent_name = agent_type.replace("_", " ").title()

        # Generate contextual response based on agent type
        response = self.get_contextual_response(agent_type, user_message)

        print(f"\n{emoji} {agent_name}:")
        print(f"  {response}")

        self.session.add_message(agent_type, response, agent_type)

    def get_contextual_response(self, agent_type: str, message: str) -> str:
        """Get contextual response based on agent expertise and message"""
        message_lower = message.lower()

        # Branding Agent responses
        if agent_type == "branding":
            if "logo" in message_lower:
                return "For your logo, I recommend following the Golden Ratio (1.618) for proportions and ensuring it works at all sizes from 16px to 16ft. Should we explore a minimalist modern approach or something more classic? I can create 4 design concepts for you."
            elif "color" in message_lower or "colour" in message_lower:
                return "Color choice is crucial! Based on color psychology: Blue conveys trust (great for B2B), Red creates energy/urgency, Green suggests growth/eco-friendly. For SURFACECRAFT STUDIO, I'd suggest a sophisticated palette with Navy (#1A365D) for trust + Warm Gray (#D4C5B9) for craftsmanship. Thoughts?"
            elif "brand" in message_lower:
                return "Let's build a comprehensive brand strategy using the Brand Identity Prism framework. We'll define your Physique (how you look), Personality (your character), Culture (your values), Relationship (how you interact), Reflection (customer perception), and Self-image (customer aspiration). Where should we start?"
            else:
                return "I can help with logo design, visual identity systems, brand positioning, typography, color theory, and brand guidelines. What aspect of branding would you like to explore?"

        # Web Development Agent responses
        elif agent_type == "web_development":
            if "ar" in message_lower or "augmented" in message_lower:
                return "For AR integration, I recommend 8th Wall Web for WebAR - no app download needed! Users can visualize countertops in their kitchen using just their phone browser. We'll use Three.js for 3D rendering and create photorealistic models of your stone varieties. Want to see the technical architecture?"
            elif "website" in message_lower or "site" in message_lower:
                return "I'll build your website with Next.js 14 for optimal performance (SSR + SSG), integrate a headless CMS (Sanity), ensure Core Web Vitals >90, and make it fully responsive. Timeline: ~13 weeks, budget $25-35K. Should I break down the development phases?"
            elif "performance" in message_lower or "speed" in message_lower:
                return "Performance is critical! I target: LCP <2.5s, FID <100ms, CLS <0.1. We'll use edge CDN (Vercel), optimize images (WebP/AVIF), lazy-load components, and implement aggressive caching. Your mobile users will thank you!"
            else:
                return "I specialize in Next.js, React, AR integration, performance optimization, and modern web architecture. What technical challenge can I solve for you?"

        # Legal Agent responses
        elif agent_type == "legal":
            if "dba" in message_lower:
                return "For DBA registration in Ohio: (1) USPTO trademark search first, (2) File with Hamilton County Recorder ($38), (3) Publish in Cincinnati Enquirer for 2 weeks ($100-200), (4) Update licenses and insurance. Total timeline: 3 weeks, cost: ~$500. Should I prepare the filing checklist?"
            elif "trademark" in message_lower:
                return "Trademark protection is essential! I'll conduct a comprehensive USPTO TESS search to check for conflicts. Federal trademark registration costs $350 filing + ~$1,500 for attorney (recommended). This gives you nationwide protection with the ® symbol. Want me to run the initial search?"
            elif "contract" in message_lower or "agreement" in message_lower:
                return "For contracts, ensure you have: offer, acceptance, consideration, capacity, and legality. I can review your customer agreements, vendor contracts, and employment docs. What type of contract do you need help with?"
            else:
                return "I handle DBA registration, trademark filing, business licensing, compliance, and contract review. What legal matter can I assist you with?"

        # MarTech Agent responses
        elif agent_type == "martech":
            if "crm" in message_lower:
                return "For CRM, I recommend HubSpot (free tier → $50/mo) for SMBs or Salesforce ($75+/user) for enterprise needs. We'll set up: lead capture, pipeline stages, automation, and reporting. Your sales team will have visibility into every customer interaction. Which CRM interests you?"
            elif "analytics" in message_lower or "tracking" in message_lower:
                return "I'll implement Google Analytics 4 with custom event tracking, set up conversion goals, create dashboards for key metrics (traffic, leads, conversions), and integrate heatmaps (Hotjar/Clarity) for user behavior insights. Want to see the recommended KPIs?"
            elif "automation" in message_lower:
                return "Marketing automation saves hours! I'll set up: lead nurture sequences, behavior-triggered emails, lead scoring, and workflow automations using HubSpot or ActiveCampaign. Average ROI increase: 25-30%. What processes should we automate first?"
            else:
                return "I specialize in CRM setup, marketing automation, analytics implementation, and tech stack integration. What marketing technology do you need?"

        # Content Agent responses
        elif agent_type == "content":
            if "video" in message_lower:
                return "For your brand video, I recommend a 2-3 minute piece with: (1) Hook in first 3 seconds, (2) Your origin story, (3) Craftsmanship showcase, (4) Customer testimonials, (5) Strong CTA. Budget: $8-12K for professional production with drone footage and motion graphics. Sound good?"
            elif "photo" in message_lower or "photography" in message_lower:
                return "Professional photography is essential! I'll create a shot list: wide establishing shots, detail close-ups, process documentation, before/after transformations, and lifestyle images. We need 50+ high-res images for website, social, and marketing. Budget: $3-5K for a full-day shoot."
            elif "seo" in message_lower or "blog" in message_lower:
                return "For SEO content, I use the pillar-cluster model: create comprehensive pillar pages (e.g., 'Countertop Installation Guide') and supporting cluster content (quartz vs granite, edge profiles, etc.). Target E-E-A-T: Experience, Expertise, Authoritativeness, Trust. Want keyword research?"
            else:
                return "I create video content, photography, case studies, blog posts, and social media assets. All optimized for engagement and SEO. What content do you need?"

        # Campaign Agent responses
        elif agent_type == "campaigns":
            if (
                "facebook" in message_lower
                or "instagram" in message_lower
                or "meta" in message_lower
            ):
                return "For Meta (Facebook/Instagram) campaigns, I recommend: carousel ads showcasing different stone varieties, video ads featuring AR visualizer, and lead gen forms for quote requests. Budget: $2-3K/month, target ROAS >4:1. Should I draft the campaign structure?"
            elif "google" in message_lower or "search" in message_lower:
                return "Google Ads strategy: (1) Search campaigns targeting 'granite countertops Cincinnati', 'quartz fabricator near me', (2) Local Services Ads for immediate leads, (3) Display remarketing. Budget: $3-5K/month. Quality Score >7 = lower CPCs. Want the keyword list?"
            elif "budget" in message_lower or "spend" in message_lower:
                return "For campaign budgets, I follow the 70-20-10 rule: 70% proven channels, 20% testing, 10% experimental. With $25K budget over 90 days, that's ~$8K/month. I'd allocate: Google Ads $3.5K, Meta $2.5K, Local partnerships $1.5K, Contingency $500. Agree?"
            else:
                return "I plan and execute multi-channel campaigns: Google Ads, Meta, LinkedIn, local partnerships. I optimize for ROAS, track attribution, and scale what works. What campaign are you planning?"

        # CFO Agent responses
        elif agent_type == "cfo":
            if "budget" in message_lower or "cost" in message_lower:
                return "Let me break down the financial picture: Total project budget ~$95K across 6 domains. Largest investments: Web ($35K, 36%), Campaigns ($25K, 26%), Content ($15K, 16%). I maintain 15% contingency for unforeseen costs. Want the detailed budget allocation?"
            elif "timeline" in message_lower or "schedule" in message_lower:
                return "Strategic timeline: Legal (Days 1-21) → Branding (22-49) → Web Dev (50-140) → MarTech (141-161) → Content (162-196) → Campaigns (197-287). Critical path: 287 days, but we can parallelize where dependencies allow. Need a Gantt chart?"
            elif "roi" in message_lower or "return" in message_lower:
                return "Expected ROI over 12 months: Initial investment $95K, projected new revenue $350-500K from enhanced brand positioning, AR differentiator, and digital marketing. Target LTV:CAC ratio >3:1, payback period <6 months. Want the detailed financial model?"
            else:
                return "As CFO, I oversee strategic planning, budget allocation, risk management, and multi-agent coordination. I ensure your investment delivers maximum ROI. What strategic question can I answer?"

        return f"I'm here to help with {agent_type.replace('_', ' ')} expertise. What would you like to know?"

    def handle_command(self, command: str) -> bool:
        """Handle slash commands"""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ["/exit", "/quit"]:
            print("\n👋 Thank you for using the Multi-Agent Chat System. Goodbye!")
            return False

        elif cmd == "/help":
            self.print_help()

        elif cmd == "/agents":
            self.list_agents()

        elif cmd == "/active":
            if self.session.active_agents:
                print(f"\n🎯 Active Agents ({len(self.session.active_agents)}):")
                for agent in sorted(self.session.active_agents):
                    emoji = self.agent_emoji.get(agent, "🤖")
                    print(f"  {emoji} {agent.replace('_', ' ').title()}")
            else:
                print("\n💤 No agents currently active")

        elif cmd == "/invoke":
            if arg:
                self.invoke_agent_interactive(arg)
            else:
                print("\n❌ Usage: /invoke <agent_name>")

        elif cmd == "/dismiss":
            if arg:
                agent = arg.lower().strip()
                if agent in self.session.active_agents:
                    self.session.dismiss_agent(agent)
                    emoji = self.agent_emoji.get(agent, "🤖")
                    print(
                        f"\n{emoji} {agent.replace('_', ' ').title()} agent left the conversation"
                    )
                else:
                    print(f"\n❌ Agent '{agent}' is not active")
            else:
                print("\n❌ Usage: /dismiss <agent_name>")

        elif cmd == "/all":
            print("\n🚀 Invoking all agents for roundtable discussion...")
            for agent in self.agent_info.keys():
                if agent not in self.session.active_agents:
                    self.invoke_agent_interactive(agent)

        elif cmd == "/clear":
            self.session.clear_agents()
            print("\n🧹 All agents dismissed")

        elif cmd == "/history":
            self.show_history()

        elif cmd == "/context":
            self.show_context()

        elif cmd == "/reset":
            confirm = input("\n⚠️  Reset the entire session? (y/n): ").lower()
            if confirm == "y":
                self.session = ChatSession()
                print("\n✅ Session reset")
            else:
                print("\n❌ Reset cancelled")

        else:
            print(f"\n❌ Unknown command: {cmd}")
            print("Type /help for available commands")

        return True

    def setup_context(self):
        """Initial context setup with user"""
        print("\n🎯 Let's set up your session context (optional, press Enter to skip)\n")

        company = input("Company name: ").strip()
        if company:
            self.session.context["company_name"] = company

        industry = input("Industry: ").strip()
        if industry:
            self.session.context["industry"] = industry

        location = input("Location: ").strip()
        if location:
            self.session.context["location"] = location

        budget = input("Total budget ($): ").strip()
        if budget:
            try:
                self.session.context["budget"] = float(budget.replace("$", "").replace(",", ""))
            except:
                pass

        print("\n✅ Context saved! You can update anytime with /context")

    def run(self):
        """Main chat loop"""
        self.print_header()

        print("\n👋 Welcome to the Multi-Agent Interactive Chat System!")
        print("\nI can connect you with expert AI agents for:")
        print("  • Strategic planning (CFO)")
        print("  • Branding & design")
        print("  • Web development & AR")
        print("  • Legal compliance")
        print("  • Marketing technology")
        print("  • Content creation")
        print("  • Campaign management")

        # Optional context setup
        setup = input("\nWould you like to set up session context? (y/n): ").lower()
        if setup == "y":
            self.setup_context()

        print("\n💡 Type /help for commands or start chatting!")
        print("💡 Use @agent to invoke specific agents (e.g., '@branding help me with logo')")
        print("💡 Type /all to start a roundtable with all agents")
        print("\n" + "=" * 80)

        # Main chat loop
        while self.running:
            try:
                # Get user input
                user_input = input("\n👤 You: ").strip()

                if not user_input:
                    continue

                # Process message
                continue_chat = self.process_user_message(user_input)

                if not continue_chat:
                    self.running = False

            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Type /exit to quit or press Enter to continue...")
                try:
                    cont = input().strip()
                    if cont.lower() in ["/exit", "/quit", "exit", "quit"]:
                        self.running = False
                except:
                    self.running = False

            except EOFError:
                self.running = False

        # Session summary
        print("\n" + "=" * 80)
        print("📊 SESSION SUMMARY")
        print("=" * 80)
        print(f"Duration: {(datetime.now() - self.session.session_start).seconds // 60} minutes")
        print(f"Messages: {len(self.session.messages)}")
        print(
            f"Agents consulted: {len(set(msg.agent_type for msg in self.session.messages if msg.agent_type))}"
        )
        print("\nThank you for using the Multi-Agent Chat System! 🚀")
        print("=" * 80 + "\n")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main():
    """Main entry point for interactive chat"""
    chat = InteractiveChatInterface()
    chat.run()


if __name__ == "__main__":
    main()
