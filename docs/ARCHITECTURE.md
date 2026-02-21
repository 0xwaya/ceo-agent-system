# Architecture Documentation — Multi-Agent System v0.5

## Table of Contents

1. [Overview](#overview)
2. [Architecture Principles](#architecture-principles)
3. [System Components](#system-components)
4. [Design Patterns](#design-patterns)
5. [Data Flow](#data-flow)
6. [API Reference](#api-reference)
7. [Deployment](#deployment)

---

## Overview

The Multi-Agent System is a professional-grade, enterprise-ready platform for orchestrating AI agents to execute complex business workflows. **Version 0.5** extends v0.4 with a fully dynamic artifact pipeline, security/social domain artifacts, brand palette generation from live agent output, and scenario defaults versioning:

- **Prompt Expert Agent**: Parses raw user commands into structured routing signals before the CEO sees them
- **CTO Agent (Tier 1)**: `cto_llm_architecture_node` — architecture review, tech-stack decisions, `TIER1_NODE_MAP` registry
- **LLM-driven dispatch**: CEO builds a `dispatch_plan` from Prompt Expert output — only required agents run
- **6 Tier-2 domain directors**: CFO, Engineer, Researcher, Legal, Martech, Security
- **7 Tier-3 execution specialists**: UX/UI, WebDev, SoftEng, Branding, Content, Campaign, SocialMedia
- **Centralised LLM nodes**: `llm_nodes.py` owns all LLM calls with per-role prompts and fallbacks
- **Role-gated tool registry**: `tools.py` enforces domain permissions before any tool executes
- **Real-time LLM chat**: Per-agent conversational memory, SocketIO `ai_chat_request/response`, REST `/api/chat/message`
- **3-Panel dashboard**: Fixed header · 240 px sidebar · flex centre · 340 px chat panel
- **Artifact pipeline (v0.5)**: Every agent run saves domain-specific files; artifacts are rendered in report UI

### Key Improvements

| Aspect | v0.1 | v0.2 | v0.3 | v0.4 | v0.5 |
| --- | --- | --- | --- | --- | --- |
| State Management | Mutable dicts | Immutable Pydantic models | TypedDicts + `dispatch_plan` | Same + `chat_history`, `cto_*` | Same |
| Agent Coverage | 1 agent | CFO + Engineer + Researcher | 6 Tier-2 + 7 Tier-3 agents | + CTO (Tier 1) | Same |
| Routing | Hard-coded | Phase-based | LLM `dispatch_plan` loop | Same + tab UI | Same |
| Intent Parsing | None | None | **Prompt Expert** (Node 0) | Same | Same |
| LLM Architecture | Inline | Inline | Centralised `llm_nodes.py` | + `cto_llm_architecture_node` | Same |
| Tool Calling | Ad-hoc | Ad-hoc | Role-gated `tools.py` | Same | Same |
| Security Domain | None | None | Full Tier-2 subgraph | Same + audit | + security artifacts |
| Social Media | None | None | Tier-3 node | Same | + social artifacts |
| Chat | None | None | Keyword fallback only | **LLM chat** — SocketIO + REST | Same |
| UI Layout | Single scroll | Single scroll | Single scroll | **3-panel** | + 📎 artifact panels |
| Artifacts | None | None | Generic JSON/MD only | Generic + branding SVGs | **Full domain artifacts** for all 9 types |
| Brand Palette | None | None | None | Hardcoded | **Dynamic from live agent colors** |
| Validation | None | None | Basic | Allowlist v1 | Allowlist v2 + null guard |
| Testing | Manual only | Test-ready | 33 tests | 33 + v0.4 feature tests | 56 tests |

---

## Architecture Principles

### SOLID Principles

1. **Single Responsibility**: Each class has one reason to change
   - Services handle business logic
   - Models handle data validation
   - Agents handle execution

2. **Open/Closed**: Open for extension, closed for modification
   - BaseAgent provides extensibility through abstract methods
   - New agents extend base class without modifying it

3. **Liskov Substitution**: All agents are substitutable
   - Any BaseAgent subclass can be used wherever BaseAgent is expected

4. **Interface Segregation**: Focused interfaces
   - Services expose only necessary methods
   - Agents implement specific capabilities

5. **Dependency Inversion**: Depend on abstractions
   - Agents receive dependencies via constructor
   - Services injected, not instantiated internally

### Clean Architecture

```text
┌─────────────────────────────────────────────┐
│          Presentation Layer                 │
│  (app.py, API routes, WebSocket handlers)   │
└─────────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────┐
│          Service Layer                      │
│  (AgentService, StateService,               │
│   OrchestrationService, ValidationService)  │
└─────────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────┐
│          Domain Layer                       │
│  (BaseAgent, Specialized Agents,            │
│   Guard Rails, Business Logic)              │
└─────────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────┐
│          Data Layer                         │
│  (Pydantic Models, State Management,        │
│   Configuration, Exceptions)                │
└─────────────────────────────────────────────┘
```

---

## System Components

### Core Modules

#### 1. config.py

**Purpose**: Centralized configuration management

**Classes**:

- `BudgetConfig`: Budget allocations and thresholds
- `AgentConfig`: Agent behavior settings
- `GuardRailConfig`: Enforcement settings
- `LogConfig`: Logging configuration
- `SecurityConfig`: Security settings
- `PerformanceConfig`: Caching and optimization
- `FeatureFlags`: Feature toggles

**Usage**:

```python
from config import BudgetConfig, AgentConfig

budget = BudgetConfig.get_agent_budget('legal')
timeout = AgentConfig.DEFAULT_TIMEOUT
```

#### 2. models.py

**Purpose**: Type-safe, validated data models

**Key Models**:

- `AgentType`: Enum of valid agent types
- `Task`: Individual task representation
- `TaskBreakdown`: Collection of tasks
- `BudgetAllocation`: Agent budget tracking
- `BudgetTracker`: Overall budget management
- `CompanyInfo`: Client company information
- `AgentExecutionResult`: Execution outcome
- `OrchestrationState`: Complete workflow state

**Features**:

- Immutable by default (frozen=True configurable)
- Automatic validation via Pydantic
- Type safety with mypy
- Serialization support

**Usage**:

```python
from models import CompanyInfo, Task, TaskPriority

company = CompanyInfo(
    name="TechCorp",
    industry="Software",
    target_audience="Enterprise",
    objectives="Launch product"
)

task = Task(
    id="task_1",
    description="Create branding",
    priority=TaskPriority.HIGH,
    agent_type=AgentType.BRANDING,
    estimated_cost=150.0
)
```

#### 3. exceptions.py

**Purpose**: Structured error handling

**Exception Hierarchy**:

```text
AgentSystemError (base)
├── ValidationError
│   ├── InvalidInputError
│   ├── InvalidAgentTypeError
│   └── SchemaValidationError
├── BudgetError
│   ├── InsufficientBudgetError
│   └── BudgetExceededError
├── AgentExecutionError
│   ├── AgentNotFoundError
│   ├── AgentTimeoutError
│   └── TaskExecutionError
├── GuardRailError
│   ├── GuardRailViolationError
│   └── VendorRecommendationError
├── StateError
│   ├── StateNotFoundError
│   └── StateTransitionError
├── OrchestrationError
│   ├── PhaseExecutionError
│   └── DependencyError
└── SecurityError
    ├── AuthenticationError
    ├── AuthorizationError
    └── RateLimitExceededError
```

**Usage**:

```python
from exceptions import InsufficientBudgetError, handle_exception

try:
    # operation
    pass
except Exception as e:
    error_dict = handle_exception(e, context="agent_execution")
```

#### 4. logger.py

**Purpose**: Professional logging system

**Logger Types**:

- `AgentLogger`: Agent-specific logging
- `OrchestrationLogger`: Workflow logging
- `APILogger`: HTTP request/response logging
- `SecurityLogger`: Security events
- `PerformanceLogger`: Performance metrics

**Features**:

- Multiple handlers (console, file)
- Rotating file handler (10MB, 5 backups)
- Configurable log levels
- Structured logging with context

**Usage**:

```python
from logger import get_agent_logger, app_logger

agent_logger = get_agent_logger("branding")
agent_logger.log_execution_start("Creating brand identity")

app_logger.info("Application started")
```

#### 5. base_agent.py

**Purpose**: Abstract base class for all agents

**Key Features**:

- Dependency injection (budget, logger, guard rails)
- Template method pattern (execute flow)
- Budget management
- Guard rail validation
- Automatic logging

**Abstract Methods** (must implement):

- `get_capabilities()`: Return agent capabilities
- `get_domain()`: Return operating domain
- `execute_task()`: Execute specific task
- `validate_context()`: Validate execution context

**Usage**:

```python
from base_agent import BaseAgent
from models import AgentType, Task

class BrandingAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(agent_type=AgentType.BRANDING, **kwargs)

    def get_capabilities(self) -> List[str]:
        return ["Logo design", "Brand guidelines"]

    def get_domain(self) -> str:
        return "branding"

    def execute_task(self, task: Task, context: Dict) -> Dict:
        # Implementation
        return {'deliverables': [...], 'cost': 150.0}

    def validate_context(self, context: Dict) -> bool:
        return 'company_info' in context
```

#### 6. services.py

**Purpose**: Business logic separation

**Services**:

**AgentService**:

- Manages agent lifecycle
- Agent registry
- Agent instantiation with DI
- Execution orchestration

**StateService**:

- State creation and management
- State persistence (in-memory currently)
- State transitions
- State validation

**ValidationService**:

- Input sanitization
- Company info validation
- Budget validation
- Request validation

**OrchestrationService**:

- Multi-agent workflow coordination
- Task breakdown creation
- Sequential execution
- Progress tracking

**Usage**:

```python
from services import AgentService, StateService, OrchestrationService

agent_service = AgentService()
state_service = StateService()
orchestration = OrchestrationService(agent_service, state_service)

state = orchestration.execute_orchestration(company_info)
```

---

## Design Patterns

### 1. Dependency Injection

**Purpose**: Decouple dependencies, enable testing

**Implementation**:

```python
class BaseAgent:
    def __init__(
        self,
        agent_type: AgentType,
        budget_allocation: Optional[BudgetAllocation] = None,
        logger: Optional[AgentLogger] = None,
        guard_rail_validator: Optional[Any] = None
    ):
        self.budget_allocation = budget_allocation
        self.logger = logger or AgentLogger(agent_type.value)
        self.guard_rail_validator = guard_rail_validator
```

**Benefits**:

- Easy to mock dependencies in tests
- Flexible configuration
- Clear dependencies

### 2. Factory Pattern

**Purpose**: Create agents dynamically

**Implementation**:

```python
class AgentService:
    def __init__(self):
        self.agent_registry = {}

    def register_agent(self, agent_type, agent_class):
        self.agent_registry[agent_type] = agent_class

    def get_agent(self, agent_type, budget_allocation=None):
        agent_class = self.agent_registry[agent_type]
        return agent_class(
            agent_type=agent_type,
            budget_allocation=budget_allocation
        )
```

### 3. Template Method Pattern

**Purpose**: Define execution skeleton, allow customization

**Implementation**:

```python
class BaseAgent:
    def execute(self, company_info, tasks=None, context=None):
        # Template method
        self._prepare_context(company_info, context)
        self.validate_context(exec_context)

        if tasks:
            for task in tasks:
                self._execute_single_task(task, exec_context)
        else:
            self._execute_default(exec_context)  # Hook method

        return self._create_result()
```

### 4. Strategy Pattern

**Purpose**: Encapsulate guard rail validation algorithms

**Implementation**: Guard rail validators can be swapped at runtime

### 5. Observer Pattern

**Purpose**: Real-time updates via WebSocket

**Implementation**:

```python
# Callback for progress updates
def on_progress(event_type, data):
    socketio.emit(event_type, data)

orchestration.execute_orchestration(company_info, callback=on_progress)
```

### 6. Service Layer Pattern

**Purpose**: Separate business logic from presentation

**Benefits**:

- Reusable business logic
- Easier testing
- Clear separation of concerns

---

## Data Flow

### 1. Agent Execution Flow

```text
┌─────────────────┐
│ API Request     │
│ (CompanyInfo)   │
└────────┬────────┘
         ▼
┌─────────────────────────────────────┐
│ ValidationService                   │
│ - Validate input                    │
│ - Sanitize data                     │
└────────┬────────────────────────────┘
         ▼
┌─────────────────────────────────────┐
│ AgentService                        │
│ - Get agent from registry           │
│ - Inject dependencies               │
└────────┬────────────────────────────┘
         ▼
┌─────────────────────────────────────┐
│ BaseAgent.execute()                 │
│ - Prepare context                   │
│ - Validate context                  │
│ - Execute tasks                     │
│ - Check budget                      │
│ - Validate guard rails              │
└────────┬────────────────────────────┘
         ▼
┌─────────────────────────────────────┐
│ Specialized Agent (e.g., Branding)  │
│ - execute_task()                    │
│ - Generate deliverables             │
└────────┬────────────────────────────┘
         ▼
┌─────────────────────────────────────┐
│ AgentExecutionResult                │
│ - success: bool                     │
│ - deliverables: List[str]           │
│ - cost: float                       │
│ - execution_time: float             │
└─────────────────────────────────────┘
```

### 2. Full Orchestration Flow

```text
┌─────────────────┐
│ API Request     │
└────────┬────────┘
         ▼
┌──────────────────────────────────────┐
│ OrchestrationService                 │
│ - Create state                       │
│ - Transition: ANALYSIS phase         │
└────────┬─────────────────────────────┘
         ▼
┌──────────────────────────────────────┐
│ PLANNING Phase                       │
│ - Create task breakdown              │
│ - Assign budgets                     │
│ - Identify dependencies              │
└────────┬─────────────────────────────┘
         ▼
┌──────────────────────────────────────┐
│ EXECUTION Phase                      │
│ - Execute agents sequentially:       │
│   1. Legal                           │
│   2. Branding                        │
│   3. Web Development                 │
│   4. MarTech                         │
│   5. Content                         │
│   6. Campaigns                       │
│ - Update state after each            │
│ - Track budget usage                 │
└────────┬─────────────────────────────┘
         ▼
┌──────────────────────────────────────┐
│ REVIEW Phase                         │
│ - Validate all deliverables          │
│ - Check quality standards            │
└────────┬─────────────────────────────┘
         ▼
┌──────────────────────────────────────┐
│ COMPLETION Phase                     │
│ - Final state                        │
│ - Success/failure summary            │
│ - Budget report                      │
└──────────────────────────────────────┘
```

---

## API Reference

### REST Endpoints

#### GET /api/agents/available

Returns list of available agents.

**Response**:

```json
{
  "agents": [
    {
      "type": "branding",
      "capabilities": ["Logo design", "Brand guidelines"],
      "domain": "branding",
      "budget": 150.0
    }
  ]
}
```

#### POST /api/ceo/analyze

Analyze objectives and return CEO strategic execution output.

**Request**:

```json
{
    "company_name": "TechCorp",
    "industry": "Software",
    "location": "Cincinnati, OH",
    "objectives": ["Launch new product"],
    "budget": 5000,
    "timeline": 90
}
```

**Response**:

```json
{
    "success": true,
    "tasks": [...],
    "budget_allocation": {...},
    "risks": [...],
    "top_priorities": [...],
    "immediate_actions": [...],
    "approval_actions": [...],
    "executive_summary": "...",
    "artifacts": [
        {
            "title": "Execution Result",
            "type": "json",
            "url": "/static/generated_outputs/ceo/.../result.json"
        }
    ],
    "artifact_run_id": "20260216-...",
    "artifact_directory": "generated_outputs/ceo/..."
}
```

#### POST /api/agent/execute/<agent_type>

Execute specific agent.

**Request**:

```json
{
    "task": "Generate deliverables for branding",
    "company_info": {
        "company_name": "TechCorp",
        "industry": "Software",
        "location": "Cincinnati, OH"
    }
}
```

**Response**:

```json
{
  "success": true,
    "result": {
        "agent_type": "branding",
        "deliverables": [...],
        "budget_used": 150.0,
        "artifacts": [...],
        "artifact_run_id": "20260216-...",
        "artifact_directory": "generated_outputs/branding/..."
    }
}
```

#### GET /api/cfo/report

Returns CFO financial report plus persisted artifact metadata for dashboard review.

#### GET /api/artifacts/runs

Lists latest artifact runs across all agents.

#### GET /api/artifacts/runs/<agent_type>

Lists artifact runs scoped to one agent type.

### Artifact Persistence

All supported execution endpoints persist reviewable files under:

```text
static/generated_outputs/<agent_type>/<run_id>_<company_slug>/
```

Each run includes a normalized bundle (`bundle.json`) and typed artifact entries consumable by the admin UI.

### WebSocket Events

#### Client → Server

**full_orchestration**:

```json
{
  "company_name": "TechCorp",
  "industry": "Software",
  "target_audience": "Enterprise",
  "objectives": "Launch product"
}
```

#### Server → Client

**orchestration_started**: Orchestration begun
**phase**: Phase update
**agent_deploying**: Agent about to execute
**agent_deployed**: Agent completed
**orchestration_complete**: Workflow finished

---

## Deployment

### Environment Setup

1. **Copy environment template**:

   ```bash
   cp .env.example .env
   ```

1. **Update .env with production values**:

   ```bash
   APP_ENV=production
   DEBUG=False
   SECRET_KEY=your-secure-random-string
   ENABLE_AUTH=True
   ENABLE_RATE_LIMITING=True
   ```

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

1. **Run application**:

   ```bash
    python3 app.py
   ```

### Production Checklist

- [ ] Set strong SECRET_KEY
- [ ] Disable DEBUG mode
- [ ] Enable authentication
- [ ] Configure rate limiting
- [ ] Set up HTTPS/SSL
- [ ] Configure logging to files
- [ ] Set up monitoring
- [ ] Configure backup strategy
- [ ] Set up CI/CD pipeline
- [ ] Run security audit
- [ ] Load testing completed
- [ ] Documentation updated

### Security Hardening

1. **Enable authentication**:

   ```python
   ENABLE_AUTH=True
   JWT_SECRET_KEY=strong-secret-key
   ```

1. **Configure rate limiting**:

   ```python
   ENABLE_RATE_LIMITING=True
   RATE_LIMIT_PER_MINUTE=60
   ```

1. **Add security headers** (future):

   ```python
   from flask_talisman import Talisman
   Talisman(app, force_https=True)
   ```

### Monitoring

Log files location: `logs/agent_system.log`

Monitor:

- Error rates
- Response times
- Budget utilization
- Agent success rates
- Resource usage

---

## Next Steps

1. Implement authentication (Flask-Login or JWT)
2. Add database persistence (SQLAlchemy)
3. Implement async agent execution
4. Add comprehensive test suite
5. Set up CI/CD with GitHub Actions
6. Create admin dashboard
7. Implement metrics and monitoring
8. Add API documentation (Swagger/OpenAPI)
