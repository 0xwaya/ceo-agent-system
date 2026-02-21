// CEO Agent Admin Dashboard JavaScript

// Global state
const state = {
    socket: null,
    agents: [],
    approvals: [],
    activities: [],
    uptime: 0,
    uptimeInterval: null,
    currentSection: 'dashboard',
    currentScenario: null
};

const SCENARIO_STORAGE_KEY = 'ceo_agent_scenario';
const ADMIN_DASHBOARD_CONFIG = window.ADMIN_DASHBOARD_CONFIG || {};
const SCENARIO_STORAGE_SCHEMA_VERSION = ADMIN_DASHBOARD_CONFIG.defaults?.scenario_schema_version || 1;
const SCENARIO_DEFAULTS_VERSION = ADMIN_DASHBOARD_CONFIG.defaults?.scenario_defaults_version || (ADMIN_DASHBOARD_CONFIG.isProduction ? 'production' : 'development');

const DEFAULT_DEV_OBJECTIVES = [
    'Launch AR platform showroom',
    'Relaunch the company brand as SurfaceCraft Studio',
    'Create a brand kit to be use across platforms',
    'Create and maintain social media accounts and content creation',
    'Possition the company in the highend exclusive market',
    'Create all necessary agent to execute and manage customer caption and retention',
    'Create sales agent to target residential and commercial contracts',
    'Register as a minority business with the city of Cincinnati',
    'Automate most processes that deals with outside sales'
];

function getDefaultScenarioContext() {
    const configDefaults = ADMIN_DASHBOARD_CONFIG.defaults || {};

    if (ADMIN_DASHBOARD_CONFIG.isProduction) {
        return {
            company_name: '',
            dba_name: '',
            industry: '',
            location: '',
            budget: 0,
            timeline: 0,
            objectives: []
        };
    }

    return {
        company_name: configDefaults.company_name || '',
        dba_name: configDefaults.dba_name || '',
        industry: configDefaults.industry || '',
        location: configDefaults.location || '',
        budget: Number.parseFloat(configDefaults.budget) || 1000,
        timeline: Number.parseInt(configDefaults.timeline, 10) || 30,
        objectives: Array.isArray(configDefaults.objectives) && configDefaults.objectives.length > 0
            ? configDefaults.objectives
            : DEFAULT_DEV_OBJECTIVES
    };
}

function buildScenarioEnvelope(scenario, options = {}) {
    return {
        meta: {
            schema_version: SCENARIO_STORAGE_SCHEMA_VERSION,
            defaults_version: SCENARIO_DEFAULTS_VERSION,
            environment: ADMIN_DASHBOARD_CONFIG.isProduction ? 'production' : 'development',
            source: options.source || 'admin_dashboard',
            user_modified: Boolean(options.userModified),
            saved_at: new Date().toISOString()
        },
        scenario
    };
}

function parseScenarioEnvelope(rawValue) {
    if (!rawValue) return null;

    try {
        const parsed = JSON.parse(rawValue);
        if (!parsed || typeof parsed !== 'object') {
            return null;
        }

        if (parsed.scenario && typeof parsed.scenario === 'object') {
            return parsed.scenario;
        }

        if (parsed.company_name || parsed.industry || parsed.location) {
            return parsed;
        }
    } catch (error) {
        console.warn('Failed to parse admin scenario storage envelope:', error);
    }

    return null;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeSocket();
    initializeNavigation();
    loadAgents();
    startUptimeCounter();
    setupEventListeners();
    loadSharedScenario();
    renderActiveScenarioPanel();

    const initialSection = document.body?.dataset?.initialSection;
    if (initialSection === 'reports' || window.location.pathname === '/reports') {
        switchSection('reports');
    }
});

// Socket.IO Connection
function initializeSocket() {
    state.socket = io();

    state.socket.on('connect', () => {
        updateConnectionStatus('connected');
        showToast('Connected to CEO Agent system', 'success');
    });

    state.socket.on('disconnect', () => {
        updateConnectionStatus('disconnected');
        showToast('Disconnected from server', 'error');
    });

    state.socket.on('agent_update', (data) => {
        handleAgentUpdate(data);
    });

    state.socket.on('activity', (data) => {
        addActivity(data);
    });

    state.socket.on('approval_request', (data) => {
        handleApprovalRequest(data);
    });

    state.socket.on('research_update', (data) => {
        handleResearchUpdate(data);
    });

    state.socket.on('scenario_updated', (data) => {
        if (!data || !data.scenario) {
            return;
        }

        state.currentScenario = data.scenario;
        localStorage.setItem(
            SCENARIO_STORAGE_KEY,
            JSON.stringify(buildScenarioEnvelope(data.scenario, { source: 'socket_sync', userModified: false }))
        );
        renderActiveScenarioPanel();

        addActivity({
            icon: '🧭',
            message: `Scenario synchronized from ${data.source || 'system'}`,
            time: new Date().toISOString()
        });
    });

    state.socket.on('orchestration_complete', (data) => {
        const tasksMetric = document.getElementById('metric-tasks-completed');
        if (tasksMetric) {
            tasksMetric.textContent = String(data.completed_tasks || 0);
        }

        const budgetMetric = document.getElementById('metric-budget');
        if (budgetMetric) {
            const remaining = Number(data.budget_remaining || 0);
            budgetMetric.textContent = `$${remaining.toLocaleString()}`;
        }

        addActivity({
            icon: '🎉',
            message: `Orchestration completed for ${data.company_name || 'scenario'} (${data.completed_tasks || 0}/${data.total_tasks || 0} tasks)`,
            time: new Date().toISOString()
        });
    });

    state.socket.on('report_generated', (data) => {
        addActivity({
            icon: '📄',
            message: `Report generated: ${data.report_type || 'unknown'} (${data.report_id || 'n/a'})`,
            time: new Date().toISOString()
        });
    });
}

function loadSharedScenario() {
    fetch('/api/scenario/current')
        .then(response => response.json())
        .then(data => {
            if (data && data.success && data.scenario) {
                state.currentScenario = data.scenario;
                localStorage.setItem(
                    SCENARIO_STORAGE_KEY,
                    JSON.stringify(buildScenarioEnvelope(data.scenario, { source: 'api_sync', userModified: false }))
                );
                renderActiveScenarioPanel();
            }
        })
        .catch((error) => {
            console.warn('Could not load shared scenario from backend:', error);
        });
}

// Navigation
function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.getAttribute('data-section');
            switchSection(section);
        });
    });
}

function switchSection(sectionName) {
    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

    // Update active content section
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(`section-${sectionName}`).classList.add('active');

    // Update breadcrumb
    document.getElementById('current-section').textContent =
        sectionName.charAt(0).toUpperCase() + sectionName.slice(1);

    state.currentSection = sectionName;

    // Load section-specific data
    loadSectionData(sectionName);
}

function loadSectionData(section) {
    switch (section) {
        case 'agents':
            loadAgents();
            break;
        case 'approvals':
            loadApprovals();
            break;
        case 'reports':
            // Reports are generated on demand
            break;
        case 'research':
            loadResearchResults();
            break;
    }
}

// Agent Management
function loadAgents() {
    fetch('/api/agents/available')
        .then(response => response.json())
        .then(data => {
            const agents = Array.isArray(data.agents) ? data.agents : [];
            state.agents = agents.map((agent) => ({
                id: agent.type,
                name: agent.name,
                icon: getAgentIcon(agent.type),
                status: agent.status === 'available' ? 'active' : (agent.status || 'active'),
                description: Array.isArray(agent.capabilities) && agent.capabilities.length > 0
                    ? agent.capabilities[0]
                    : 'Specialized AI agent',
                tasksCompleted: 0,
                successRate: 0,
                budget: Number(agent.budget || 0)
            }));

            updateAgentCounts();
            renderAgents();
        })
        .catch((error) => {
            console.error('Failed to load agents:', error);
            showToast('Could not load agents from API', 'warning');
            state.agents = [];
            updateAgentCounts();
            renderAgents();
        });
}

function getAgentIcon(agentType) {
    const iconMap = {
        ceo: '👔',
        cfo: '💰',
        branding: '🎨',
        designer: '🎨',
        web_development: '💻',
        legal: '⚖️',
        martech: '📱',
        content: '📸',
        campaigns: '🚀',
        social_media: '📣',
        ux_ui: '✨',
        software_engineering: '🛠️',
        security: '🛡️'
    };
    return iconMap[agentType] || '🤖';
}

function updateAgentCounts() {
    const totalAgents = state.agents.length;
    const activeMetric = document.getElementById('metric-active-agents');
    if (activeMetric) {
        activeMetric.textContent = totalAgents;
    }

    const navCount = document.getElementById('agents-nav-count');
    if (navCount) {
        navCount.textContent = totalAgents;
    }
}

function renderAgents() {
    const grid = document.getElementById('agents-grid');
    if (!grid) return;

    grid.innerHTML = state.agents.map(agent => `
        <div class="agent-card">
            <div class="agent-header">
                <div class="agent-avatar">${agent.icon}</div>
                <div class="agent-info">
                    <h3>${agent.name}</h3>
                    <span class="agent-status ${agent.status}">${agent.status.toUpperCase()}</span>
                </div>
            </div>
            <div class="agent-description">${agent.description}</div>
            <div class="agent-stats">
                <div class="agent-stat">
                    <span class="agent-stat-value">${agent.tasksCompleted}</span>
                    <span class="agent-stat-label">Tasks</span>
                </div>
                <div class="agent-stat">
                    <span class="agent-stat-value">${agent.successRate}%</span>
                    <span class="agent-stat-label">Success</span>
                </div>
                <div class="agent-stat">
                    <span class="agent-stat-value">$${(agent.budget).toLocaleString()}</span>
                    <span class="agent-stat-label">Budget</span>
                </div>
            </div>
            <div class="agent-actions">
                <button class="agent-btn" onclick="viewAgentDetails('${agent.id}')">Details</button>
                <button class="agent-btn primary" onclick="interactWithAgent('${agent.id}')">Run & View Output</button>
            </div>
        </div>
    `).join('');
}

function getAgentExecutionCompanyInfo() {
    const scenario = getScenarioContext();
    return {
        company_name: scenario.company_name,
        name: scenario.company_name,
        dba_name: scenario.dba_name,
        industry: scenario.industry,
        location: scenario.location,
        budget: scenario.budget,
        timeline: scenario.timeline
    };
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function normalizeToList(value) {
    if (Array.isArray(value)) {
        return value.filter(Boolean);
    }
    if (typeof value === 'string' && value.trim().length > 0) {
        return [value.trim()];
    }
    return [];
}

function formatListSection(title, items, emptyState = 'No items available.') {
    return `
        <div class="agent-output-section">
            <h4>${title}</h4>
            ${items.length > 0
            ? `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`
            : `<p style="color: var(--text-secondary);">${emptyState}</p>`
        }
        </div>
    `;
}

function normalizeArtifacts(value) {
    if (!Array.isArray(value)) {
        return [];
    }

    return value
        .filter((item) => item && typeof item === 'object' && item.url)
        .map((item) => ({
            title: item.title || item.path || 'Generated Artifact',
            type: item.type || 'file',
            extension: item.extension || '',
            mime_type: item.mime_type || '',
            url: safeArtifactUrl(item.url)
        }))
        .filter((item) => Boolean(item.url));
}

function safeArtifactUrl(url) {
    if (typeof url !== 'string') {
        return '';
    }
    const trimmed = url.trim();
    if (!trimmed.startsWith('/static/')) {
        return '';
    }
    return trimmed;
}

function isImageArtifact(item) {
    const imageExt = ['svg', 'png', 'jpg', 'jpeg', 'webp', 'gif'];
    return item.type === 'image'
        || (item.mime_type && item.mime_type.startsWith('image/'))
        || imageExt.includes(String(item.extension || '').toLowerCase());
}

function formatArtifactSection(title, artifacts, emptyState = 'No generated artifacts available yet.') {
    const normalized = normalizeArtifacts(artifacts);

    return `
        <div class="agent-output-section">
            <h4>${escapeHtml(title)}</h4>
            ${normalized.length > 0
            ? `<div class="artifact-grid">${normalized.map((item) => {
                const imageArtifact = isImageArtifact(item);
                return `
                        <article class="artifact-card">
                            ${imageArtifact
                        ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">
                                        <img src="${escapeHtml(item.url)}" alt="${escapeHtml(item.title)}" class="artifact-preview" loading="lazy" />
                                   </a>`
                        : `<div class="artifact-file">📄 ${escapeHtml((item.extension || 'file').toUpperCase())}</div>`}
                            <div class="artifact-meta">
                                <div class="artifact-title">${escapeHtml(item.title)}</div>
                                <a class="artifact-link" href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">Open</a>
                            </div>
                        </article>
                    `;
            }).join('')}</div>`
            : `<p style="color: var(--text-secondary);">${escapeHtml(emptyState)}</p>`
        }
        </div>
    `;
}

function formatKeyValueSection(title, values) {
    const rows = Object.entries(values || {}).filter(([, value]) => value !== undefined && value !== null && String(value).trim() !== '');
    return `
        <div class="agent-output-section">
            <h4>${title}</h4>
            ${rows.length > 0
            ? `<div class="agent-output-kv">
                    ${rows.map(([label, value]) => `
                        <div class="agent-output-kv-item">
                            <span class="label">${escapeHtml(label)}</span>
                            <span class="value">${escapeHtml(value)}</span>
                        </div>
                    `).join('')}
                </div>`
            : '<p style="color: var(--text-secondary);">No report metrics available.</p>'
        }
        </div>
    `;
}

function formatParagraphSection(title, value, emptyState = 'No narrative provided.') {
    const text = typeof value === 'string' ? value.trim() : '';
    return `
        <div class="agent-output-section">
            <h4>${escapeHtml(title)}</h4>
            <p class="agent-output-paragraph">${text ? escapeHtml(text) : escapeHtml(emptyState)}</p>
        </div>
    `;
}

function openAgentWorkspace(title, subtitle, contentHtml) {
    const workspace = document.getElementById('agent-workspace');
    const titleEl = document.getElementById('agent-workspace-title');
    const subtitleEl = document.getElementById('agent-workspace-subtitle');
    const contentEl = document.getElementById('agent-workspace-content');

    if (!workspace || !titleEl || !subtitleEl || !contentEl) {
        return;
    }

    titleEl.textContent = title;
    subtitleEl.textContent = subtitle;
    contentEl.innerHTML = contentHtml;
    workspace.style.display = 'block';
    workspace.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function closeAgentWorkspace() {
    const workspace = document.getElementById('agent-workspace');
    const contentEl = document.getElementById('agent-workspace-content');
    if (!workspace || !contentEl) return;

    contentEl.innerHTML = '';
    workspace.style.display = 'none';
}

function showAgentWorkspaceLoading(agentName, actionText) {
    openAgentWorkspace(
        `${agentName} Workspace`,
        actionText,
        `<div class="agent-workspace-loading">⏳ ${escapeHtml(actionText)}...</div>`
    );
}

function renderSpecializedAgentOutput(agent, result) {
    const deliverables = normalizeToList(result?.deliverables);
    const recommendations = normalizeToList(result?.recommendations);
    const artifacts = normalizeArtifacts(result?.artifacts);

    const proposals = [];
    if (Array.isArray(result?.design_concepts)) {
        result.design_concepts.forEach((concept) => {
            proposals.push(`${concept.concept_name || 'Concept'} — ${concept.description || 'No description provided'}`);
        });
    }
    if (Array.isArray(result?.timeline)) {
        result.timeline.forEach((step) => {
            if (typeof step === 'string') {
                proposals.push(step);
            } else if (step && typeof step === 'object') {
                proposals.push(`${step.phase || step.week || 'Phase'} — ${step.description || step.deliverable || 'Timeline item'}`);
            }
        });
    }
    if (Array.isArray(result?.tech_stack)) {
        result.tech_stack.forEach((tool) => {
            proposals.push(`Technology: ${typeof tool === 'string' ? tool : JSON.stringify(tool)}`);
        });
    }

    const reportMetrics = {
        Status: result?.status || 'executed',
        'Budget Used': `$${Number(result?.budget_used || 0).toLocaleString()}`,
        'Execution Mode': result?.execution_mode || 'AI_PERFORMED',
        'Timeline Days': result?.timeline_days || '',
        'Artifact Run ID': result?.artifact_run_id || '',
        Timestamp: result?.timestamp || new Date().toISOString()
    };

    return `
        ${formatKeyValueSection('Report', reportMetrics)}
        ${formatArtifactSection('Generated Files', artifacts, 'This run did not generate files. Execute again to create artifacts.')}
        ${formatListSection('Deliverables', deliverables, 'No deliverables returned for this run.')}
        ${formatListSection('Proposals', proposals, 'No proposal artifacts were returned for this agent.')}
        ${formatListSection('Recommendations', recommendations, 'No recommendations were returned for this run.')}
    `;
}

function renderCEOOutput(data) {
    const tasks = Array.isArray(data?.tasks) ? data.tasks : [];
    const artifacts = normalizeArtifacts(data?.artifacts);
    const deliverables = tasks.map((task) => task.description || task.task_name || task.task_description || 'Task generated');
    const topPriorities = normalizeToList(data?.top_priorities);
    const immediateActions = normalizeToList(data?.immediate_actions);
    const approvalActions = normalizeToList(data?.approval_actions);
    const riskSummary = normalizeToList(data?.risk_summary);
    const risks = Array.isArray(data?.risks) ? data.risks : [];
    const recommendations = risks.length > 0
        ? risks.map((risk) => {
            if (risk && typeof risk === 'object') {
                const description = risk.description || risk.risk || 'Risk identified';
                const mitigation = risk.mitigation || risk.action || '';
                return mitigation
                    ? `Mitigate risk: ${description} → ${mitigation}`
                    : `Mitigate risk: ${description}`;
            }
            return `Mitigate risk: ${risk}`;
        })
        : ['Prioritize top 3 strategic tasks and launch weekly review cadence.'];

    const metrics = {
        'Generated Tasks': tasks.length,
        'Timeline (days)': data?.timeline || 'N/A',
        'Budget Domains': Object.keys(data?.budget_allocation || {}).length,
        'Risk Flags': risks.length,
        'Pending Approvals': Array.isArray(data?.pending_approvals) ? data.pending_approvals.length : 0,
        'Execution Mode': data?.execution_mode || 'AI_PERFORMED'
    };

    const budgetLines = Object.entries(data?.budget_allocation || {}).map(([domain, amount]) => `${domain}: $${Number(amount || 0).toLocaleString()}`);

    return `
        ${formatKeyValueSection('Report', metrics)}
        ${formatParagraphSection('Executive Summary', data?.executive_summary, 'No executive summary returned.')}
        ${formatArtifactSection('Generated Files', artifacts, 'No files persisted for this CEO run yet.')}
        ${formatListSection('Top Priorities', topPriorities, 'No top priorities returned.')}
        ${formatListSection('Immediate Actions', immediateActions, 'No immediate actions returned.')}
        ${formatListSection('Approval Queue', approvalActions, 'No approval actions returned.')}
        ${formatListSection('Risk Snapshot', riskSummary, 'No risk summary returned.')}
        ${formatListSection('Deliverables', deliverables, 'No strategic tasks were returned.')}
        ${formatListSection('Proposals', budgetLines, 'No budget proposal data was returned.')}
        ${formatListSection('Recommendations', recommendations, 'No recommendations returned.')}
    `;
}

function renderCFOOutput(data) {
    const report = data?.report || {};
    const recommendations = normalizeToList(report?.cfo_recommendations);
    const artifacts = normalizeArtifacts(data?.artifacts);
    const deliverables = [
        `Pending approvals tracked: ${Number(report?.pending_approvals || 0)}`,
        `CFO managed budget: $${Number(report?.cfo_managed || report?.allocated_to_api_fees || 0).toLocaleString()}`,
        `User approval required: $${Number(report?.user_approval_required || 0).toLocaleString()}`
    ];

    const metrics = {
        'Total Budget': `$${Number(report?.total_budget || 0).toLocaleString()}`,
        'CFO Managed': `$${Number(report?.cfo_managed || report?.allocated_to_api_fees || 0).toLocaleString()}`,
        'User Approval Required': `$${Number(report?.user_approval_required || 0).toLocaleString()}`,
        'Pending Approvals': Number(report?.pending_approvals || 0)
    };

    return `
        ${formatKeyValueSection('Report', metrics)}
        ${formatArtifactSection('Generated Files', artifacts, 'No files persisted for this CFO run yet.')}
        ${formatListSection('Deliverables', deliverables, 'No CFO deliverables returned.')}
        ${formatListSection('Proposals', [], 'CFO does not produce design proposals.')}
        ${formatListSection('Recommendations', recommendations, 'No financial recommendations returned.')}
    `;
}

function viewAgentDetails(agentId) {
    const agent = state.agents.find(a => a.id === agentId);
    if (!agent) return;

    const normalized = agentId === 'designer' ? 'branding' : agentId;

    if (normalized === 'ceo' || normalized === 'cfo') {
        const summary = normalized === 'ceo'
            ? [
                'Orchestrates all agents and strategic objectives.',
                'Produces strategic tasks, risk flags, and budget allocation direction.',
                'Use Run & View Output to generate live strategic deliverables.'
            ]
            : [
                'Monitors financial controls and approval constraints.',
                'Produces budget reports and financial risk checks.',
                'Use Run & View Output to generate the latest CFO report.'
            ];

        openAgentWorkspace(
            `${agent.name} Details`,
            'Agent scope and interaction hints',
            formatListSection('Recommendations', summary, 'No details available.')
        );
        return;
    }

    showAgentWorkspaceLoading(agent.name, `Loading ${agent.name} guard rails`);
    fetch(`/api/guard-rails/${normalized}`)
        .then(response => response.json())
        .then(data => {
            if (!data.success || !data.guard_rail) {
                throw new Error(data.error || 'Unable to load guard rails');
            }

            const guardRail = data.guard_rail;
            const permittedTasks = normalizeToList(guardRail.permitted_tasks);
            const allowedCategories = normalizeToList(guardRail.allowed_categories);

            openAgentWorkspace(
                `${agent.name} Details`,
                'Guard rails and scope',
                `
                    ${formatKeyValueSection('Report', {
                    'Max Budget': `$${Number(guardRail.max_budget || 0).toLocaleString()}`,
                    'Quality Metrics': Object.keys(guardRail.quality_standards || {}).length
                })}
                    ${formatListSection('Deliverables', permittedTasks, 'No permitted tasks provided.')}
                    ${formatListSection('Proposals', allowedCategories, 'No spending categories provided.')}
                    ${formatListSection('Recommendations', ['Run & View Output to generate real execution deliverables for this agent.'])}
                `
            );
        })
        .catch((error) => {
            openAgentWorkspace(
                `${agent.name} Details`,
                'Unable to load details',
                `<p style="color: var(--danger-color);">${escapeHtml(error.message)}</p>`
            );
        });
}

function interactWithAgent(agentId) {
    const agent = state.agents.find(a => a.id === agentId);
    if (!agent) return;

    const normalized = agentId === 'designer' ? 'branding' : agentId;
    const scenario = getScenarioContext();
    const companyInfo = getAgentExecutionCompanyInfo();

    showAgentWorkspaceLoading(agent.name, `Executing ${agent.name}`);

    if (normalized === 'ceo') {
        fetch('/api/ceo/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                company_name: scenario.company_name,
                industry: scenario.industry,
                location: scenario.location,
                objectives: scenario.objectives,
                budget: scenario.budget,
                timeline: scenario.timeline
            })
        })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    throw new Error(data.error || 'CEO execution failed');
                }
                openAgentWorkspace(`${agent.name} Output`, 'Live strategic output', renderCEOOutput(data));
                addActivity({
                    icon: '👔',
                    message: `${agent.name} generated strategic deliverables`,
                    time: new Date().toISOString()
                });
            })
            .catch((error) => {
                openAgentWorkspace(`${agent.name} Output`, 'Execution failed', `<p style="color: var(--danger-color);">${escapeHtml(error.message)}</p>`);
                showToast(`${agent.name} failed: ${error.message}`, 'error');
            });
        return;
    }

    if (normalized === 'cfo') {
        fetch('/api/cfo/report')
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    throw new Error(data.error || 'CFO execution failed');
                }
                openAgentWorkspace(`${agent.name} Output`, 'Live financial output', renderCFOOutput(data));
                addActivity({
                    icon: '💰',
                    message: `${agent.name} generated financial deliverables`,
                    time: new Date().toISOString()
                });
            })
            .catch((error) => {
                openAgentWorkspace(`${agent.name} Output`, 'Execution failed', `<p style="color: var(--danger-color);">${escapeHtml(error.message)}</p>`);
                showToast(`${agent.name} failed: ${error.message}`, 'error');
            });
        return;
    }

    fetch(`/api/agent/execute/${normalized}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            task: `Generate report, proposals, recommendations, and deliverables for ${agent.name}`,
            company_info: {
                company_name: companyInfo.company_name,
                name: companyInfo.company_name,
                dba_name: companyInfo.dba_name,
                industry: companyInfo.industry,
                location: companyInfo.location,
                budget: companyInfo.budget,
                timeline: companyInfo.timeline
            }
        })
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                throw new Error(data.error || `${agent.name} execution failed`);
            }

            openAgentWorkspace(
                `${agent.name} Output`,
                'Live execution artifacts',
                renderSpecializedAgentOutput(agent, data.result || {})
            );

            addActivity({
                icon: agent.icon || '🤖',
                message: `${agent.name} generated deliverables and recommendations`,
                time: new Date().toISOString()
            });
            showToast(`${agent.name} output generated`, 'success');
        })
        .catch((error) => {
            openAgentWorkspace(`${agent.name} Output`, 'Execution failed', `<p style="color: var(--danger-color);">${escapeHtml(error.message)}</p>`);
            showToast(`${agent.name} failed: ${error.message}`, 'error');
        });
}

// CEO Strategic Analysis
function startCEOAnalysis() {
    const scenario = getScenarioContext();

    addActivity({
        icon: '🎯',
        message: `Starting CEO strategic analysis for ${scenario.company_name}...`,
        time: new Date().toISOString()
    });

    showToast(`CEO Agent analyzing strategic objectives for ${scenario.company_name}`, 'info');

    // Send analysis request to backend
    fetch('/api/ceo/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            company_name: scenario.company_name,
            industry: scenario.industry,
            location: scenario.location,
            objectives: scenario.objectives,
            budget: scenario.budget,
            timeline: scenario.timeline
        })
    })
        .then(response => response.json())
        .then(data => {
            handleCEOAnalysisResult(data);
        })
        .catch(error => {
            showToast('Analysis failed: ' + error.message, 'error');
        });
}

function handleCEOAnalysisResult(data) {
    if (data.error) {
        showToast('CEO Analysis Error: ' + data.error, 'error');
        return;
    }

    const ceoAgent = state.agents.find((item) => item.id === 'ceo') || { name: 'CEO Agent', icon: '👔' };

    openAgentWorkspace(
        `${ceoAgent.name} Output`,
        'Live strategic output',
        renderCEOOutput(data)
    );

    addActivity({
        icon: '✅',
        message: `CEO identified ${data.tasks?.length || 0} strategic tasks`,
        time: new Date().toISOString()
    });

    // Update metrics
    if (data.tasks) {
        document.getElementById('metric-tasks-completed').textContent = data.tasks.length;
    }

    // Check for pending approvals
    if (data.pending_approvals && data.pending_approvals.length > 0) {
        state.approvals = data.pending_approvals;
        updateApprovalsBadge();
        showToast(`${data.pending_approvals.length} payment approvals required`, 'warning');
    }

    showToast('CEO Strategic Analysis Complete — detailed report ready', 'success');
}

// Training Module
function openTrainingModule() {
    switchSection('training');
}

function loadTrainingModule(moduleName) {
    const titles = {
        'communication': 'Communication Skills Training',
        'decision-making': 'Decision Making Framework',
        'risk-assessment': 'Risk Assessment Protocol',
        'budget-management': 'Budget Management Training',
        'collaboration': 'Agent Collaboration Best Practices'
    };

    document.getElementById('training-module-title').textContent = titles[moduleName] || 'Training Module';

    const content = document.getElementById('training-content');
    content.innerHTML = `
        <div style="padding: 20px;">
            <h3 style="margin-bottom: 16px;">Training: ${titles[moduleName]}</h3>
            <p style="color: var(--text-secondary); margin-bottom: 24px;">
                Interactive training environment for ${moduleName.replace('-', ' ')} skills.
            </p>

            <div style="background: rgba(37, 99, 235, 0.1); padding: 16px; border-radius: 12px; margin-bottom: 16px;">
                <strong>Training Scenario:</strong>
                <p style="margin-top: 8px; color: var(--text-secondary);">
                    This module helps agents learn ${moduleName.replace('-', ' ')} through interactive scenarios.
                    Provide instructions or run automated training scenarios.
                </p>
            </div>

            <button class="training-btn primary" onclick="runTrainingScenario()" style="width: 100%;">
                ▶️ Start Training Scenario
            </button>
        </div>
    `;

    addTrainingMessage(`Loaded ${titles[moduleName]} module. Ready for training.`, 'system');
}

function runTrainingScenario() {
    addTrainingMessage('Running training scenario...', 'system');

    setTimeout(() => {
        addTrainingMessage('Scenario complete. Agent performance improved.', 'system');
        showToast('Training scenario completed successfully', 'success');
    }, 2000);
}

function saveTrainingProgress() {
    showToast('Training progress saved', 'success');
    addTrainingMessage('Progress checkpoint saved.', 'system');
}

function sendTrainingMessage() {
    const input = document.getElementById('training-chat-input');
    const message = input.value.trim();

    if (!message) return;

    addTrainingMessage(message, 'user');
    input.value = '';

    // Simulate agent response
    setTimeout(() => {
        addTrainingMessage('Acknowledged. Processing your instruction...', 'agent');
    }, 500);
}

function addTrainingMessage(message, type = 'system') {
    const messagesContainer = document.getElementById('training-chat-messages');
    const messageEl = document.createElement('div');
    messageEl.className = `chat-message ${type}`;

    const prefix = {
        'system': '<strong>Training System:</strong> ',
        'user': '<strong>You:</strong> ',
        'agent': '<strong>Agent:</strong> '
    }[type] || '';

    // ✅ SECURITY: Create text node to prevent XSS
    const prefixSpan = document.createElement('span');
    prefixSpan.innerHTML = prefix;  // Safe - prefix is from trusted source
    const messageText = document.createTextNode(message);  // Safe - escapes HTML

    messageEl.appendChild(prefixSpan);
    messageEl.appendChild(messageText);
    messagesContainer.appendChild(messageEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Research Functions
function startResearch() {
    switchSection('research');
    startManualResearch();
}

function startManualResearch() {
    const schedule = document.getElementById('research-schedule')?.value || 'manual';
    const depth = document.getElementById('research-depth')?.value || 3;

    addActivity({
        icon: '🔬',
        message: `Starting research session (depth: ${depth}/5)`,
        time: new Date().toISOString()
    });

    showToast('Research session started', 'info');

    // Simulate research process
    setTimeout(() => {
        addResearchFinding({
            title: 'New AI Tool Discovery: Claude 3.5 Sonnet',
            description: 'Latest LLM with improved reasoning capabilities. Cost: $15/1M tokens.',
            tags: ['LLM', 'API', 'Cost Optimization'],
            timestamp: new Date().toISOString()
        });
    }, 2000);

    setTimeout(() => {
        addResearchFinding({
            title: 'Best Practice: Agent Collaboration Patterns',
            description: 'Industry research shows multi-agent systems with clear role separation perform 34% better.',
            tags: ['Best Practices', 'Architecture'],
            timestamp: new Date().toISOString()
        });
    }, 4000);
}

function addResearchFinding(finding) {
    const feed = document.getElementById('research-feed');

    // Remove placeholder if exists
    const placeholder = feed.querySelector('.research-placeholder');
    if (placeholder) {
        placeholder.remove();
    }

    const item = document.createElement('div');
    item.className = 'research-item';
    item.innerHTML = `
        <h4>${finding.title}</h4>
        <p>${finding.description}</p>
        <div class="research-tags">
            ${finding.tags.map(tag => `<span class="research-tag">${tag}</span>`).join('')}
        </div>
    `;

    feed.insertBefore(item, feed.firstChild);

    // Update last update time
    document.querySelector('.last-update').textContent = `Last updated: ${new Date().toLocaleTimeString()}`;

    addActivity({
        icon: '📚',
        message: `Research finding: ${finding.title}`,
        time: finding.timestamp
    });
}

function loadResearchResults() {
    // Research results are added dynamically through startManualResearch
}

// Approvals Management
function viewApprovals() {
    switchSection('approvals');
}

function loadApprovals() {
    const container = document.getElementById('approvals-container');
    if (!container) return;

    if (state.approvals.length === 0) {
        container.innerHTML = `
            <div class="approvals-placeholder">
                <div class="placeholder-icon">✅</div>
                <h3>No Pending Approvals</h3>
                <p>When agents request payments for services or tools, they'll appear here for your approval.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = state.approvals.map(approval => `
        <div class="approval-card">
            <div class="approval-icon">💳</div>
            <div class="approval-content">
                <div class="approval-header">
                    <h3>${approval.title || approval.payment_type}</h3>
                    <div class="approval-amount">$${approval.amount}</div>
                </div>
                <div class="approval-description">
                    ${approval.description || approval.justification}
                </div>
                <div class="approval-details">
                    <div class="approval-detail">
                        <strong>Payment Type</strong>
                        ${approval.payment_type}
                    </div>
                    <div class="approval-detail">
                        <strong>Requested By</strong>
                        ${approval.agent || 'CEO Agent'}
                    </div>
                    <div class="approval-detail">
                        <strong>Risk Level</strong>
                        ${approval.risk_level || 'Medium'}
                    </div>
                </div>
                <div class="approval-actions">
                    <button class="approval-btn approve" onclick="approvePayment('${approval.id}')">
                        ✓ Approve
                    </button>
                    <button class="approval-btn reject" onclick="rejectPayment('${approval.id}')">
                        ✗ Reject
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function handleApprovalRequest(data) {
    state.approvals.push(data);
    updateApprovalsBadge();

    if (state.currentSection === 'approvals') {
        loadApprovals();
    }

    showToast(`New approval request: ${data.title || data.payment_type}`, 'warning');

    addActivity({
        icon: '💳',
        message: `Approval required: ${data.title || data.payment_type} - $${data.amount}`,
        time: new Date().toISOString()
    });
}

function approvePayment(approvalId) {
    const approval = state.approvals.find(a => a.id === approvalId);
    if (!approval) return;

    // Send approval to backend
    fetch(`/api/approval/${approvalId}/approve`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            state.approvals = state.approvals.filter(a => a.id !== approvalId);
            updateApprovalsBadge();
            loadApprovals();

            showToast(`Approved: ${approval.title || approval.payment_type}`, 'success');

            addActivity({
                icon: '✅',
                message: `Approved payment: ${approval.title || approval.payment_type} - $${approval.amount}`,
                time: new Date().toISOString()
            });
        })
        .catch(error => {
            showToast('Approval failed: ' + error.message, 'error');
        });
}

function rejectPayment(approvalId) {
    const approval = state.approvals.find(a => a.id === approvalId);
    if (!approval) return;

    // Send rejection to backend
    fetch(`/api/approval/${approvalId}/reject`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            state.approvals = state.approvals.filter(a => a.id !== approvalId);
            updateApprovalsBadge();
            loadApprovals();

            showToast(`Rejected: ${approval.title || approval.payment_type}`, 'info');

            addActivity({
                icon: '❌',
                message: `Rejected payment: ${approval.title || approval.payment_type} - $${approval.amount}`,
                time: new Date().toISOString()
            });
        })
        .catch(error => {
            showToast('Rejection failed: ' + error.message, 'error');
        });
}

function updateApprovalsBadge() {
    const count = state.approvals.length;
    document.getElementById('pending-approvals-count').textContent = count;
    document.getElementById('approvals-summary').textContent =
        count > 0 ? `${count} item${count !== 1 ? 's' : ''} pending` : 'No pending items';
}

// Reports - Comprehensive with 30/60/90 Day Plans
function generateReport(reportType) {
    showToast(reportType === 'designer-deliverables' ? 'Generating designer deliverables...' : `Generating ${reportType} report...`, 'info');

    const viewer = document.getElementById('report-viewer');
    const title = document.getElementById('report-title');
    const content = document.getElementById('report-content');

    // Map report types to API endpoints
    const reportEndpoints = {
        'ceo': { endpoint: '/api/reports/strategic', method: 'POST', title: 'CEO Strategic Report' },
        'cfo': { endpoint: '/api/reports/financial', method: 'POST', title: 'CFO Financial Report' },
        'agent-performance': { endpoint: '/api/reports/training', method: 'GET', title: 'Agent Performance Report' },
        'training-progress': { endpoint: '/api/reports/research', method: 'GET', title: 'Training & Research Report' },
        'designer-deliverables': { endpoint: '/api/agent/execute/branding', method: 'POST', title: 'Designer Deliverables', mode: 'agent_execution' }
    };

    const reportConfig = reportEndpoints[reportType];
    if (!reportConfig) {
        showToast('Unknown report type', 'error');
        return;
    }

    const scenario = getScenarioContext();

    // Prepare allowlist-compatible company info for POST requests
    const companyInfo = {
        company_name: scenario.company_name,
        name: scenario.company_name,
        dba_name: scenario.dba_name,
        industry: scenario.industry,
        location: scenario.location,
        budget: scenario.budget,
        timeline: scenario.timeline
    };

    // Make API call
    const fetchOptions = {
        method: reportConfig.method,
        headers: { 'Content-Type': 'application/json' }
    };

    if (reportConfig.method === 'POST') {
        if (reportConfig.mode === 'agent_execution') {
            fetchOptions.body = JSON.stringify({
                task: `Generate complete branding proposals and deliverables for ${scenario.company_name}`,
                company_info: companyInfo
            });
        } else {
            fetchOptions.body = JSON.stringify(companyInfo);
        }
    }

    title.textContent = reportConfig.title;
    content.innerHTML = renderReportLoading(reportConfig.title);
    viewer.style.display = 'flex';

    const progressState = { value: 12 };
    const progressInterval = setInterval(() => {
        progressState.value = Math.min(progressState.value + 11, 92);
        updateReportLoadingProgress(progressState.value, reportType === 'designer-deliverables'
            ? 'Designer agent is generating logo directions and brand assets...'
            : 'Compiling report data...');
    }, 500);

    fetch(reportConfig.endpoint, fetchOptions)
        .then(response => response.json())
        .then(data => {
            clearInterval(progressInterval);
            updateReportLoadingProgress(100, 'Complete');

            if (data.success) {
                title.textContent = reportConfig.title;
                if (reportConfig.mode === 'agent_execution') {
                    content.innerHTML = renderDesignerDeliverables(data.result, scenario);
                } else {
                    content.innerHTML = renderComprehensiveReport(data.report, reportType);
                }
                viewer.style.display = 'flex';

                addActivity({
                    icon: reportConfig.mode === 'agent_execution' ? '🎨' : '📊',
                    message: reportConfig.mode === 'agent_execution'
                        ? `Generated ${reportConfig.title} for ${scenario.company_name}`
                        : `Generated ${reportConfig.title} for ${scenario.company_name} - ${data.report.report_id}`,
                    time: new Date().toISOString()
                });
            } else {
                showToast('Error generating report: ' + data.error, 'error');
            }
        })
        .catch(error => {
            clearInterval(progressInterval);
            console.error('Report generation error:', error);
            showToast('Failed to generate report', 'error');
            // Fallback to static reports
            const reports = {
                'ceo': { title: 'CEO Strategic Report', content: generateCEOReport() },
                'cfo': { title: 'CFO Financial Report', content: generateCFOReport() },
                'agent-performance': { title: 'Agent Performance Report', content: generatePerformanceReport() },
                'training-progress': { title: 'Training Progress Report', content: generateTrainingReport() }
            };
            const report = reports[reportType];
            if (report) {
                title.textContent = report.title;
                content.innerHTML = report.content;
                viewer.style.display = 'flex';
            } else {
                content.innerHTML = '<p style="color: var(--danger);">Failed to load this report type.</p>';
                viewer.style.display = 'flex';
            }
        });
}

function renderReportLoading(title) {
    return `
        <div style="padding: 1rem 0;">
            <h4 style="margin-bottom: 0.75rem;">${title}</h4>
            <div style="background: var(--bg-secondary); border-radius: 8px; height: 10px; overflow: hidden; margin-bottom: 0.75rem;">
                <div id="report-loading-fill" style="width: 12%; height: 100%; background: var(--primary); transition: width 0.3s ease;"></div>
            </div>
            <div id="report-loading-text" style="color: var(--text-secondary); font-size: 0.9rem;">Preparing execution...</div>
        </div>
    `;
}

function updateReportLoadingProgress(percent, message) {
    const fill = document.getElementById('report-loading-fill');
    const text = document.getElementById('report-loading-text');
    if (fill) {
        fill.style.width = `${Math.max(0, Math.min(100, percent))}%`;
    }
    if (text && message) {
        text.textContent = message;
    }
}

function renderDesignerDeliverables(result, scenario) {
    const deliverables = Array.isArray(result?.deliverables) ? result.deliverables : [];
    const proposals = Array.isArray(result?.design_concepts) ? result.design_concepts : [];
    const recommendations = Array.isArray(result?.recommendations)
        ? result.recommendations
        : (result?.recommendations ? [result.recommendations] : []);
    const brandKit = result?.brand_kit_reference || {};

    return `
        <div class="comprehensive-report">
            <div class="report-header">
                <h2>Designer Deliverables</h2>
                <p class="report-date">Generated: ${new Date().toLocaleString()}</p>
            </div>

            <div class="report-section">
                <h3>🏢 Brand Context</h3>
                <div class="summary-grid">
                    <div class="summary-card"><span class="label">Company:</span><span class="value">${scenario.company_name || '-'}</span></div>
                    <div class="summary-card"><span class="label">DBA:</span><span class="value">${brandKit.brand_name || scenario.dba_name || '-'}</span></div>
                    <div class="summary-card"><span class="label">Industry:</span><span class="value">${scenario.industry || '-'}</span></div>
                    <div class="summary-card"><span class="label">Budget Used:</span><span class="value">$${Number(result?.budget_used || 0).toLocaleString()}</span></div>
                </div>
            </div>

            <div class="report-section">
                <h3>📦 Final Deliverables</h3>
                <ul>
                    ${deliverables.length > 0 ? deliverables.map(item => `<li>${item}</li>`).join('') : '<li>No deliverables were returned.</li>'}
                </ul>
            </div>

            <div class="report-section">
                <h3>🎨 Logo Proposals</h3>
                ${proposals.length > 0 ? proposals.map((concept, index) => `
                    <div class="action-item" style="margin-bottom: 0.75rem;">
                        <div class="action-content">
                            <strong>${index + 1}. ${concept.concept_name || 'Concept'}</strong>
                            <p>${concept.description || ''}</p>
                            <p><strong>Applications:</strong> ${concept.applications || 'N/A'}</p>
                            <p><strong>Scalability:</strong> ${concept.scalability || 'N/A'}</p>
                        </div>
                    </div>
                `).join('') : '<p>No design concepts were returned.</p>'}
            </div>

            <div class="report-section">
                <h3>💡 Recommendations</h3>
                <ul>
                    ${recommendations.length > 0 ? recommendations.map(item => `<li>${item}</li>`).join('') : '<li>No recommendations provided.</li>'}
                </ul>
            </div>
        </div>
    `;
}

function getScenarioContext() {
    const fallback = getDefaultScenarioContext();

    if (state.currentScenario && typeof state.currentScenario === 'object') {
        const current = state.currentScenario;
        return {
            company_name: current.company_name || fallback.company_name,
            dba_name: current.dba_name || current.company_name || fallback.dba_name,
            industry: current.industry || fallback.industry,
            location: current.location || fallback.location,
            budget: Number.parseFloat(current.budget) || fallback.budget,
            timeline: Number.parseInt(current.timeline, 10) || fallback.timeline,
            objectives: Array.isArray(current.objectives) && current.objectives.length > 0
                ? current.objectives
                : fallback.objectives
        };
    }

    if (ADMIN_DASHBOARD_CONFIG.isProduction) {
        return fallback;
    }

    const raw = localStorage.getItem(SCENARIO_STORAGE_KEY);
    if (!raw) {
        return fallback;
    }

    const parsed = parseScenarioEnvelope(raw);
    if (!parsed || typeof parsed !== 'object') {
        return fallback;
    }

    return {
        company_name: parsed.company_name || fallback.company_name,
        dba_name: parsed.dba_name || parsed.company_name || fallback.dba_name,
        industry: parsed.industry || fallback.industry,
        location: parsed.location || fallback.location,
        budget: Number.parseFloat(parsed.budget) || fallback.budget,
        timeline: Number.parseInt(parsed.timeline, 10) || fallback.timeline,
        objectives: Array.isArray(parsed.objectives) && parsed.objectives.length > 0
            ? parsed.objectives
            : fallback.objectives
    };
}

function renderActiveScenarioPanel() {
    const scenario = getScenarioContext();
    const objectiveText = Array.isArray(scenario.objectives) && scenario.objectives.length > 0
        ? scenario.objectives.join(' • ')
        : '-';

    const safeSet = (id, value) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    };

    const syncTargets = ['', '-reports'];
    syncTargets.forEach((suffix) => {
        safeSet(`scenario-company${suffix}`, scenario.company_name || '-');
        safeSet(`scenario-dba${suffix}`, scenario.dba_name || '-');
        safeSet(`scenario-industry${suffix}`, scenario.industry || '-');
        safeSet(`scenario-location${suffix}`, scenario.location || '-');
        safeSet(`scenario-budget${suffix}`, Number(scenario.budget) > 0 ? `$${Number(scenario.budget).toLocaleString()}` : '-');
        safeSet(`scenario-timeline${suffix}`, Number(scenario.timeline) > 0 ? `${Number(scenario.timeline)} days` : '-');
        safeSet(`scenario-objectives${suffix}`, objectiveText);
    });

    let updatedAt = '-';
    try {
        const raw = localStorage.getItem(SCENARIO_STORAGE_KEY);
        if (raw) {
            const parsed = parseScenarioEnvelope(raw);
            if (parsed?.updated_at) {
                updatedAt = new Date(parsed.updated_at).toLocaleString();
            }
        }
    } catch (error) {
        console.warn('Failed to parse scenario updated timestamp:', error);
    }
    syncTargets.forEach((suffix) => {
        safeSet(`scenario-updated${suffix}`, updatedAt);
    });
}

// Render comprehensive report with 30/60/90 day plans
function renderComprehensiveReport(report, reportType) {
    if (reportType === 'ceo') {
        return renderStrategicReport(report);
    } else if (reportType === 'cfo') {
        return renderFinancialReport(report);
    } else if (reportType === 'agent-performance') {
        return renderTrainingReportNew(report);
    } else if (reportType === 'training-progress') {
        return renderResearchReport(report);
    }
    return '<p>Report format not supported</p>';
}

// Strategic Report Renderer
function renderStrategicReport(report) {
    let html = `
        <div class="comprehensive-report">
            <div class="report-header">
                <h2>Strategic Report - ${report.report_id}</h2>
                <p class="report-date">Generated: ${new Date(report.generated_at).toLocaleDateString()}</p>
            </div>

            <!-- Executive Summary -->
            <div class="report-section">
                <h3>📋 Executive Summary</h3>
                <div class="summary-grid">
                    <div class="summary-card">
                        <span class="label">Company:</span>
                        <span class="value">${report.company_overview.company_name}</span>
                    </div>
                    <div class="summary-card">
                        <span class="label">Industry:</span>
                        <span class="value">${report.company_overview.industry}</span>
                    </div>
                    <div class="summary-card">
                        <span class="label">Stage:</span>
                        <span class="value">${report.company_overview.stage}</span>
                    </div>
                    <div class="summary-card">
                        <span class="label">Runway:</span>
                        <span class="value">${report.company_overview.runway_months} months</span>
                    </div>
                </div>
            </div>

            <!-- Current State -->
            <div class="report-section">
                <h3>📊 Current State Analysis</h3>
                <div class="state-grid">
                    <div class="state-item">
                        <strong>Operations:</strong> ${report.current_state.operational_health}
                    </div>
                    <div class="state-item">
                        <strong>Market Position:</strong> ${report.current_state.market_position}
                    </div>
                    <div class="state-item">
                        <strong>Product Maturity:</strong> ${report.current_state.product_maturity}
                    </div>
                </div>
            </div>

            <!-- 30/60/90 Day Consolidated Plan -->
            <div class="report-section consolidated-plan">
                <h3>🎯 Consolidated 30/60/90 Day Strategic Plan</h3>

                ${render30DayPlan(report.consolidated_plan['30_day_plan'])}
                ${render60DayPlan(report.consolidated_plan['60_day_plan'])}
                ${render90DayPlan(report.consolidated_plan['90_day_plan'])}
            </div>

            <!-- Individual Agent Plans -->
            <div class="report-section agent-plans">
                <h3>👥 Agent-Specific 30/60/90 Day Plans</h3>
                ${report.agent_analyses.map(agent => renderAgentPlan(agent)).join('')}
            </div>

            <!-- Immediate Actions -->
            <div class="report-section">
                <h3>⚡ Immediate Actions (Next 7 Days)</h3>
                <div class="actions-list">
                    ${report.next_actions.map(action => `
                        <div class="action-item priority-${action.priority.toLowerCase()}">
                            <div class="action-header">
                                <span class="priority-badge">${action.priority}</span>
                                <span class="owner">${action.owner}</span>
                                <span class="deadline">Due: ${new Date(action.deadline).toLocaleDateString()}</span>
                            </div>
                            <div class="action-content">
                                <strong>${action.action}</strong>
                                <p>${action.impact}</p>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- Success Metrics -->
            <div class="report-section">
                <h3>📈 Success Metrics & KPIs</h3>
                ${renderSuccessMetrics(report.success_metrics)}
            </div>
        </div>
    `;
    return html;
}

function render30DayPlan(plan) {
    return `
        <div class="plan-period day-30">
            <div class="plan-header">
                <h4>30-Day Plan: ${plan.theme}</h4>
                <span class="period">${plan.period}</span>
            </div>
            <div class="plan-content">
                <div class="plan-priorities">
                    <strong>Key Priorities:</strong>
                    <ul>
                        ${plan.priorities.map(p => `<li>${p}</li>`).join('')}
                    </ul>
                </div>
                <div class="plan-deliverables">
                    <strong>Deliverables:</strong>
                    <ul>
                        ${plan.deliverables.map(d => `<li>${d}</li>`).join('')}
                    </ul>
                </div>
                <div class="plan-budget">
                    <strong>Budget Required:</strong> ${plan.budget_required}
                </div>
                <div class="plan-risks">
                    <strong>Risk Factors:</strong>
                    <ul>
                        ${plan.risks.map(r => `<li>${r}</li>`).join('')}
                    </ul>
                </div>
            </div>
        </div>
    `;
}

function render60DayPlan(plan) {
    return `
        <div class="plan-period day-60">
            <div class="plan-header">
                <h4>60-Day Plan: ${plan.theme}</h4>
                <span class="period">${plan.period}</span>
            </div>
            <div class="plan-content">
                <div class="plan-priorities">
                    <strong>Key Priorities:</strong>
                    <ul>
                        ${plan.priorities.map(p => `<li>${p}</li>`).join('')}
                    </ul>
                </div>
                <div class="plan-deliverables">
                    <strong>Deliverables:</strong>
                    <ul>
                        ${plan.deliverables.map(d => `<li>${d}</li>`).join('')}
                    </ul>
                </div>
                <div class="plan-budget">
                    <strong>Budget Required:</strong> ${plan.budget_required}
                </div>
            </div>
        </div>
    `;
}

function render90DayPlan(plan) {
    return `
        <div class="plan-period day-90">
            <div class="plan-header">
                <h4>90-Day Plan: ${plan.theme}</h4>
                <span class="period">${plan.period}</span>
            </div>
            <div class="plan-content">
                <div class="plan-priorities">
                    <strong>Key Priorities:</strong>
                    <ul>
                        ${plan.priorities.map(p => `<li>${p}</li>`).join('')}
                    </ul>
                </div>
                <div class="plan-deliverables">
                    <strong>Deliverables:</strong>
                    <ul>
                        ${plan.deliverables.map(d => `<li>${d}</li>`).join('')}
                    </ul>
                </div>
                <div class="plan-budget">
                    <strong>Budget Required:</strong> ${plan.budget_required}
                </div>
            </div>
        </div>
    `;
}

function renderAgentPlan(agent) {
    return `
        <div class="agent-plan-card">
            <div class="agent-plan-header">
                <h4>${agent.agent}</h4>
                <span class="agent-domain">${agent.domain}</span>
            </div>
            <div class="agent-assessment">
                <strong>Current Assessment:</strong>
                <p>${agent.current_assessment}</p>
            </div>
            <div class="agent-timeline">
                <div class="timeline-item">
                    <h5>📅 30-Day Plan</h5>
                    <ul>
                        ${agent.plan_30_days.slice(0, 4).map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
                <div class="timeline-item">
                    <h5>📅 60-Day Plan</h5>
                    <ul>
                        ${agent.plan_60_days.slice(0, 4).map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
                <div class="timeline-item">
                    <h5>📅 90-Day Plan</h5>
                    <ul>
                        ${agent.plan_90_days.slice(0, 4).map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
            </div>
            <div class="agent-success">
                <strong>Success Criteria:</strong>
                <ul>
                    ${agent.success_criteria.map(sc => `<li>${sc}</li>`).join('')}
                </ul>
            </div>
        </div>
    `;
}

function renderSuccessMetrics(metrics) {
    return `
        <div class="metrics-timeline">
            <div class="metrics-period">
                <h4>30-Day Targets</h4>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <span class="metric-label">Revenue Target</span>
                        <span class="metric-value">$${metrics['30_day_metrics'].financial.target_revenue.toLocaleString()}</span>
                    </div>
                    <div class="metric-card">
                        <span class="metric-label">Expense Target</span>
                        <span class="metric-value">$${metrics['30_day_metrics'].financial.target_expenses.toLocaleString()}</span>
                    </div>
                    <div class="metric-card">
                        <span class="metric-label">Retention Rate</span>
                        <span class="metric-value">${metrics['30_day_metrics'].product.target_retention_rate}</span>
                    </div>
                </div>
            </div>
            <div class="metrics-period">
                <h4>60-Day Targets</h4>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <span class="metric-label">Revenue Target</span>
                        <span class="metric-value">$${metrics['60_day_metrics'].financial.target_revenue.toLocaleString()}</span>
                    </div>
                    <div class="metric-card">
                        <span class="metric-label">CAC Payback</span>
                        <span class="metric-value">${metrics['60_day_metrics'].financial.target_cac_payback}</span>
                    </div>
                    <div class="metric-card">
                        <span class="metric-label">Gross Margin</span>
                        <span class="metric-value">${metrics['60_day_metrics'].financial.target_gross_margin}</span>
                    </div>
                </div>
            </div>
            <div class="metrics-period">
                <h4>90-Day Targets</h4>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <span class="metric-label">Revenue Target</span>
                        <span class="metric-value">$${metrics['90_day_metrics'].financial.target_revenue.toLocaleString()}</span>
                    </div>
                    <div class="metric-card">
                        <span class="metric-label">Unit Economics</span>
                        <span class="metric-value">${metrics['90_day_metrics'].financial.target_unit_economics}</span>
                    </div>
                    <div class="metric-card">
                        <span class="metric-label">Market Share</span>
                        <span class="metric-value">${metrics['90_day_metrics'].product.target_market_share}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function generateCEOReport() {
    return `
        <div style="font-family: Inter, sans-serif;">
            <h2 style="margin-bottom: 24px;">Executive Summary</h2>

            <div style="background: var(--card-bg); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h3 style="font-size: 16px; margin-bottom: 12px;">System Status</h3>
                <p style="color: var(--text-secondary);">
                    CEO Agent system is operational in Training Mode. All core agents initialized and ready for deployment.
                </p>
            </div>

            <div style="background: var(--card-bg); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h3 style="font-size: 16px; margin-bottom: 12px;">Strategic Objectives</h3>
                <ul style="color: var(--text-secondary); padding-left: 20px;">
                    <li>Financial guard rails implemented with user approval workflow</li>
                    <li>6 specialized agents configured (CEO, CFO, Brand, Legal, MarTech, UX/UI)</li>
                    <li>98% of budget ($49,030) requires user approval</li>
                    <li>All contractor payments forbidden to prevent liability</li>
                </ul>
            </div>

            <div style="background: var(--card-bg); padding: 20px; border-radius: 12px;">
                <h3 style="font-size: 16px; margin-bottom: 12px;">Recommendations</h3>
                <ul style="color: var(--text-secondary); padding-left: 20px;">
                    <li>Complete agent training modules before production deployment</li>
                    <li>Configure daily research schedule for continuous improvement</li>
                    <li>Test approval workflow with sample payment requests</li>
                    <li>Review budget allocations for each specialized agent</li>
                </ul>
            </div>
        </div>
    `;
}

// Financial Report Renderer
function renderFinancialReport(report) {
    return `
        <div class="comprehensive-report">
            <div class="report-header">
                <h2>Financial Report - ${report.report_id}</h2>
                <p class="report-date">Generated: ${new Date(report.generated_at).toLocaleDateString()}</p>
            </div>

            <!-- Financial Overview -->
            <div class="report-section">
                <h3>💰 Financial Overview</h3>
                <div class="financial-grid">
                    <div class="fin-card">
                        <span class="label">Revenue Health:</span>
                        <span class="value">${report.financial_overview.revenue_health}</span>
                    </div>
                    <div class="fin-card">
                        <span class="label">Expense Efficiency:</span>
                        <span class="value">${report.financial_overview.expense_efficiency}</span>
                    </div>
                    <div class="fin-card">
                        <span class="label">Cash Position:</span>
                        <span class="value">${report.financial_overview.cash_position}</span>
                    </div>
                </div>
            </div>

            <!-- Revenue Projections -->
            <div class="report-section">
                <h3>📈 Revenue Projections</h3>
                <div class="projection-timeline">
                    <div class="projection-item">
                        <h4>30 Days</h4>
                        <p class="projection-value">${report.revenue_projections['30_day']}</p>
                    </div>
                    <div class="projection-item">
                        <h4>60 Days</h4>
                        <p class="projection-value">${report.revenue_projections['60_day']}</p>
                    </div>
                    <div class="projection-item">
                        <h4>90 Days</h4>
                        <p class="projection-value">${report.revenue_projections['90_day']}</p>
                    </div>
                </div>
                <div class="assumptions">
                    <strong>Key Assumptions:</strong>
                    <ul>
                        ${report.revenue_projections.assumptions.map(a => `<li>${a}</li>`).join('')}
                    </ul>
                </div>
            </div>

            <!-- CFO 30/60/90 Day Plan -->
            <div class="report-section">
                <h3>📋 CFO Strategic Plan</h3>
                <div class="cfo-plan-timeline">
                    <div class="cfo-plan-period">
                        <h4>30-Day Financial Plan</h4>
                        <ul>
                            ${report.cfo_30_60_90_plan['30_days'].map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="cfo-plan-period">
                        <h4>60-Day Financial Plan</h4>
                        <ul>
                            ${report.cfo_30_60_90_plan['60_days'].map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="cfo-plan-period">
                        <h4>90-Day Financial Plan</h4>
                        <ul>
                            ${report.cfo_30_60_90_plan['90_days'].map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>

            <!-- Cost Optimization -->
            <div class="report-section">
                <h3>💡 Cost Optimization Opportunities</h3>
                <div class="optimization-list">
                    ${report.cost_optimization.map(opt => `
                        <div class="optimization-item">
                            <div class="opt-header">
                                <strong>${opt.category}</strong>
                                <span class="savings">${opt.savings}</span>
                            </div>
                            <div class="opt-details">
                                <div>Current: ${opt.current_cost} → Optimized: ${opt.optimized_cost}</div>
                                <div class="opt-action">Action: ${opt.action}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- Funding Requirements -->
            <div class="report-section">
                <h3>🎯 Funding Requirements</h3>
                <div class="funding-info">
                    <div class="funding-card">
                        <span class="label">Immediate Need:</span>
                        <span class="value">${report.funding_requirements.immediate_need}</span>
                    </div>
                    <div class="funding-card">
                        <span class="label">Recommended Raise:</span>
                        <span class="value">${report.funding_requirements.recommended_raise}</span>
                    </div>
                    <div class="funding-card">
                        <span class="label">Timeline:</span>
                        <span class="value">${report.funding_requirements.fundraising_timeline}</span>
                    </div>
                </div>
                <div class="use-of-funds">
                    <strong>Use of Funds:</strong>
                    <ul>
                        ${report.funding_requirements.use_of_funds.map(uof => `<li>${uof}</li>`).join('')}
                    </ul>
                </div>
            </div>

            <!-- Financial Risks -->
            <div class="report-section">
                <h3>⚠️ Financial Risk Assessment</h3>
                <div class="risks-list">
                    ${report.financial_risks.map(risk => `
                        <div class="risk-item severity-${risk.severity.toLowerCase()}">
                            <div class="risk-header">
                                <strong>${risk.risk}</strong>
                                <span class="severity-badge">${risk.severity}</span>
                            </div>
                            <div class="risk-mitigation">Mitigation: ${risk.mitigation}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

// Training Report Renderer
function renderTrainingReportNew(report) {
    return `
        <div class="comprehensive-report">
            <div class="report-header">
                <h2>Training Progress Report - ${report.report_id}</h2>
                <p class="report-date">Generated: ${new Date(report.generated_at).toLocaleDateString()}</p>
            </div>

            <!-- Training Overview -->
            <div class="report-section">
                <h3>🎓 Training Overview</h3>
                <div class="training-stats">
                    <div class="stat-card">
                        <span class="label">Overall Status:</span>
                        <span class="value">${report.training_overview.overall_status}</span>
                    </div>
                    <div class="stat-card">
                        <span class="label">Agents Trained:</span>
                        <span class="value">${report.training_overview.agents_trained}</span>
                    </div>
                    <div class="stat-card">
                        <span class="label">Production Readiness:</span>
                        <span class="value">${report.training_overview.production_readiness}</span>
                    </div>
                    <div class="stat-card">
                        <span class="label">Training Hours:</span>
                        <span class="value">${report.training_overview.training_hours}h</span>
                    </div>
                </div>
            </div>

            <!-- Agent Readiness -->
            <div class="report-section">
                <h3>👥 Individual Agent Readiness</h3>
                <div class="readiness-list">
                    ${report.agent_readiness.map(agent => `
                        <div class="readiness-item">
                            <div class="readiness-header">
                                <strong>${agent.agent}</strong>
                                <span class="readiness-percent">${agent.readiness}</span>
                            </div>
                            <div class="readiness-bar">
                                <div class="readiness-fill" style="width: ${agent.readiness}"></div>
                            </div>
                            <div class="readiness-status">${agent.status}</div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- Training 30/60/90 Plan -->
            <div class="report-section">
                <h3>📅 Training Roadmap</h3>
                <div class="training-roadmap">
                    <div class="roadmap-period">
                        <h4>30-Day Training Plan</h4>
                        <ul>
                            ${report.training_30_60_90_plan['30_days'].map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="roadmap-period">
                        <h4>60-Day Training Plan</h4>
                        <ul>
                            ${report.training_30_60_90_plan['60_days'].map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="roadmap-period">
                        <h4>90-Day Training Plan</h4>
                        <ul>
                            ${report.training_30_60_90_plan['90_days'].map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>

            <!-- Skill Gaps -->
            <div class="report-section">
                <h3>🎯 Identified Skill Gaps</h3>
                <ul class="skill-gaps">
                    ${report.skill_gaps.map(gap => `<li>${gap}</li>`).join('')}
                </ul>
            </div>
        </div>
    `;
}

// Research Report Renderer
function renderResearchReport(report) {
    return `
        <div class="comprehensive-report">
            <div class="report-header">
                <h2>Research & Innovation Report - ${report.report_id}</h2>
                <p class="report-date">Generated: ${new Date(report.generated_at).toLocaleDateString()}</p>
            </div>

            <!-- Research Overview -->
            <div class="report-section">
                <h3>🔬 Research Overview</h3>
                <div class="research-stats">
                    <div class="stat-card">
                        <span class="label">Tools Evaluated:</span>
                        <span class="value">${report.research_overview.total_tools_evaluated}</span>
                    </div>
                    <div class="stat-card">
                        <span class="label">Best Practices:</span>
                        <span class="value">${report.research_overview.best_practices_documented}</span>
                    </div>
                    <div class="stat-card">
                        <span class="label">Reports Analyzed:</span>
                        <span class="value">${report.research_overview.industry_reports_analyzed}</span>
                    </div>
                </div>
                <div class="key-findings">
                    <strong>Key Findings:</strong>
                    <ul>
                        ${report.research_overview.key_findings.map(finding => `<li>${finding}</li>`).join('')}
                    </ul>
                </div>
            </div>

            <!-- Tools Evaluated -->
            <div class="report-section">
                <h3>🛠️ Tools Evaluation</h3>
                <div class="tools-list">
                    ${report.tools_evaluated.map(tool => `
                        <div class="tool-item">
                            <strong>${tool.tool}</strong>
                            <span class="verdict">${tool.verdict}</span>
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- Best Practices -->
            <div class="report-section">
                <h3>✨ Documented Best Practices</h3>
                <ul class="best-practices">
                    ${report.best_practices.slice(0, 10).map(practice => `<li>${practice}</li>`).join('')}
                </ul>
            </div>

            <!-- Research 30/60/90 Plan -->
            <div class="report-section">
                <h3>📋 Research Roadmap</h3>
                <div class="research-roadmap">
                    <div class="roadmap-period">
                        <h4>30-Day Research Plan</h4>
                        <ul>
                            ${report.research_30_60_90_plan['30_days'].slice(0, 5).map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="roadmap-period">
                        <h4>60-Day Research Plan</h4>
                        <ul>
                            ${report.research_30_60_90_plan['60_days'].slice(0, 5).map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="roadmap-period">
                        <h4>90-Day Research Plan</h4>
                        <ul>
                            ${report.research_30_60_90_plan['90_days'].slice(0, 5).map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function generateCFOReport() {
    return `
        <div style="font-family: Inter, sans-serif;">
            <h2 style="margin-bottom: 24px;">Financial Overview</h2>

            <div style="background: var(--card-bg); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h3 style="font-size: 16px; margin-bottom: 12px;">Budget Summary</h3>
                <table style="width: 100%; color: var(--text-primary);">
                    <tr>
                        <td>Total Budget:</td>
                        <td style="text-align: right; font-weight: 600;">$50,000</td>
                    </tr>
                    <tr>
                        <td>CFO Managed:</td>
                        <td style="text-align: right; font-weight: 600;">$970</td>
                    </tr>
                    <tr>
                        <td>User Approval Required:</td>
                        <td style="text-align: right; font-weight: 600;">$49,030</td>
                    </tr>
                    <tr>
                        <td>Spent to Date:</td>
                        <td style="text-align: right; font-weight: 600; color: var(--success-color);">$0</td>
                    </tr>
                    <tr style="border-top: 1px solid var(--border-color);">
                        <td><strong>Remaining:</strong></td>
                        <td style="text-align: right; font-weight: 700;">$50,000</td>
                    </tr>
                </table>
            </div>

            <div style="background: var(--card-bg); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h3 style="font-size: 16px; margin-bottom: 12px;">Approval Limits</h3>
                <ul style="color: var(--text-secondary); padding-left: 20px;">
                    <li>API Fees: Auto-approve up to $100</li>
                    <li>Legal Filing Fees: Auto-approve up to $500</li>
                    <li>All Other Payments: User approval required</li>
                    <li>Contractor Payments: Forbidden</li>
                </ul>
            </div>

            <div style="background: var(--card-bg); padding: 20px; border-radius: 12px;">
                <h3 style="font-size: 16px; margin-bottom: 12px;">Financial Health</h3>
                <p style="color: var(--success-color); font-weight: 600;">Excellent</p>
                <p style="color: var(--text-secondary); margin-top: 8px;">
                    No expenditures to date. All safety controls operational. Ready for production deployment.
                </p>
            </div>
        </div>
    `;
}

function generatePerformanceReport() {
    return `
        <div style="font-family: Inter, sans-serif;">
            <h2 style="margin-bottom: 24px;">Agent Performance Metrics</h2>

            ${state.agents.map(agent => `
                <div style="background: var(--card-bg); padding: 20px; border-radius: 12px; margin-bottom: 16px;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                        <span style="font-size: 32px;">${agent.icon}</span>
                        <h3 style="font-size: 16px;">${agent.name}</h3>
                        <span class="agent-status ${agent.status}" style="margin-left: auto;">${agent.status.toUpperCase()}</span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 12px;">
                        <div>
                            <div style="color: var(--text-secondary); font-size: 12px;">Tasks Completed</div>
                            <div style="font-size: 20px; font-weight: 700;">${agent.tasksCompleted}</div>
                        </div>
                        <div>
                            <div style="color: var(--text-secondary); font-size: 12px;">Success Rate</div>
                            <div style="font-size: 20px; font-weight: 700;">${agent.successRate}%</div>
                        </div>
                        <div>
                            <div style="color: var(--text-secondary); font-size: 12px;">Budget</div>
                            <div style="font-size: 20px; font-weight: 700;">$${agent.budget.toLocaleString()}</div>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function generateTrainingReport() {
    return `
        <div style="font-family: Inter, sans-serif;">
            <h2 style="margin-bottom: 24px;">Training Progress Overview</h2>

            <div style="background: var(--card-bg); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h3 style="font-size: 16px; margin-bottom: 12px;">Overall Status</h3>
                <p style="color: var(--text-secondary);">
                    System is in Training Mode. All agents require training completion before production deployment.
                </p>
            </div>

            <div style="background: var(--card-bg); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h3 style="font-size: 16px; margin-bottom: 12px;">Training Modules</h3>
                <div style="display: flex; flex-direction: column; gap: 12px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>Communication Skills</span>
                        <span style="color: var(--success-color);">✓ Completed</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Decision Making</span>
                        <span style="color: var(--warning-color);">→ In Progress</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Risk Assessment</span>
                        <span style="color: var(--text-secondary);">○ Pending</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Budget Management</span>
                        <span style="color: var(--text-secondary);">○ Pending</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Agent Collaboration</span>
                        <span style="color: var(--text-secondary);">○ Pending</span>
                    </div>
                </div>
            </div>

            <div style="background: var(--card-bg); padding: 20px; border-radius: 12px;">
                <h3 style="font-size: 16px; margin-bottom: 12px;">Next Steps</h3>
                <ul style="color: var(--text-secondary); padding-left: 20px;">
                    <li>Complete Decision Making module</li>
                    <li>Begin Risk Assessment training</li>
                    <li>Schedule agent collaboration exercises</li>
                    <li>Review and approve training progress checkpoints</li>
                </ul>
            </div>
        </div>
    `;
}

function closeReportViewer() {
    document.getElementById('report-viewer').style.display = 'none';
}

// Settings
function resetSettings() {
    if (confirm('Reset all settings to defaults?')) {
        document.getElementById('system-mode').value = 'training';
        document.getElementById('auto-approve-api').checked = true;
        document.getElementById('email-notifications').checked = false;
        document.getElementById('total-budget').value = 50000;
        document.getElementById('cfo-api-limit').value = 100;
        document.getElementById('cfo-legal-limit').value = 500;

        showToast('Settings reset to defaults', 'success');
    }
}

function saveSettings() {
    const settings = {
        systemMode: document.getElementById('system-mode').value,
        autoApproveAPI: document.getElementById('auto-approve-api').checked,
        emailNotifications: document.getElementById('email-notifications').checked,
        totalBudget: document.getElementById('total-budget').value,
        cfoAPILimit: document.getElementById('cfo-api-limit').value,
        cfoLegalLimit: document.getElementById('cfo-legal-limit').value
    };

    // Send to backend
    fetch('/api/settings/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
        .then(response => response.json())
        .then(data => {
            showToast('Settings saved successfully', 'success');

            addActivity({
                icon: '⚙️',
                message: 'System settings updated',
                time: new Date().toISOString()
            });
        })
        .catch(error => {
            showToast('Failed to save settings', 'error');
        });
}

// Activity Feed
function addActivity(activity) {
    state.activities.unshift(activity);

    const feed = document.getElementById('activity-feed');
    if (!feed) return;

    const item = document.createElement('div');
    item.className = 'activity-item';

    const time = new Date(activity.time || new Date());
    const timeStr = formatTimeAgo(time);

    item.innerHTML = `
        <div class="activity-icon">${activity.icon || '📌'}</div>
        <div class="activity-content">
            <p>${activity.message}</p>
            <span class="activity-time">${timeStr}</span>
        </div>
    `;

    // Remove welcome message if it exists
    const welcome = feed.querySelector('.activity-item.welcome');
    if (welcome && state.activities.length > 1) {
        welcome.remove();
    }

    feed.insertBefore(item, feed.firstChild);

    // Keep only last 20 activities
    while (feed.children.length > 20) {
        feed.removeChild(feed.lastChild);
    }
}

function clearActivity() {
    if (confirm('Clear all activity logs?')) {
        state.activities = [];
        const feed = document.getElementById('activity-feed');
        feed.innerHTML = `
            <div class="activity-item welcome">
                <div class="activity-icon">👋</div>
                <div class="activity-content">
                    <p><strong>Activity feed cleared</strong></p>
                    <p>New activities will appear here.</p>
                    <span class="activity-time">Just now</span>
                </div>
            </div>
        `;
        showToast('Activity feed cleared', 'info');
    }
}

// Utility Functions
function formatTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}

function startUptimeCounter() {
    state.uptime = 0;
    state.uptimeInterval = setInterval(() => {
        state.uptime++;
        updateUptimeDisplay();
    }, 1000);
}

function updateUptimeDisplay() {
    const hours = Math.floor(state.uptime / 3600);
    const minutes = Math.floor((state.uptime % 3600) / 60);
    const seconds = state.uptime % 60;

    const display = `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    document.getElementById('metric-uptime').textContent = display;
}

function updateConnectionStatus(status) {
    const statusEl = document.getElementById('connection-status');
    const dot = statusEl.querySelector('.status-dot');
    const text = statusEl.querySelector('span');

    if (status === 'connected') {
        dot.style.background = 'var(--success-color)';
        text.textContent = 'Connected';
    } else {
        dot.style.background = 'var(--danger-color)';
        text.textContent = 'Disconnected';
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <strong>${type.charAt(0).toUpperCase() + type.slice(1)}:</strong> ${message}
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            container.removeChild(toast);
        }, 300);
    }, 5000);
}

function handleAgentUpdate(data) {
    // Update agent data in state
    const agentIndex = state.agents.findIndex(a => a.id === data.agent_id);
    if (agentIndex !== -1) {
        state.agents[agentIndex] = { ...state.agents[agentIndex], ...data };
        renderAgents();
    }

    addActivity({
        icon: '🤖',
        message: `${data.agent_name || 'Agent'} updated: ${data.message}`,
        time: new Date().toISOString()
    });
}

function handleResearchUpdate(data) {
    addResearchFinding(data);
}

function setupEventListeners() {
    // Refresh button
    document.getElementById('refresh-btn')?.addEventListener('click', () => {
        location.reload();
    });

    // Enter key in training chat
    document.getElementById('training-chat-input')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendTrainingMessage();
        }
    });

    window.addEventListener('storage', (event) => {
        if (event.key === SCENARIO_STORAGE_KEY) {
            renderActiveScenarioPanel();
        }
    });

    window.addEventListener('focus', () => {
        renderActiveScenarioPanel();
    });
}

// Export functions to global scope
window.startCEOAnalysis = startCEOAnalysis;
window.openTrainingModule = openTrainingModule;
window.startResearch = startResearch;
window.viewApprovals = viewApprovals;
window.clearActivity = clearActivity;
window.viewAgentDetails = viewAgentDetails;
window.interactWithAgent = interactWithAgent;
window.loadTrainingModule = loadTrainingModule;
window.runTrainingScenario = runTrainingScenario;
window.saveTrainingProgress = saveTrainingProgress;
window.sendTrainingMessage = sendTrainingMessage;
window.startManualResearch = startManualResearch;
window.approvePayment = approvePayment;
window.rejectPayment = rejectPayment;
window.generateReport = generateReport;
window.closeReportViewer = closeReportViewer;
window.closeAgentWorkspace = closeAgentWorkspace;
window.resetSettings = resetSettings;
window.saveSettings = saveSettings;
