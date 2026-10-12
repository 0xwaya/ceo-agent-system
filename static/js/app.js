// Multi-Agent System Dashboard JavaScript

// Initialize Socket.IO connection
let socket;

const ACCOUNT_SCOPE = document.querySelector('meta[name="account-id"]').content || 'development';
const SCENARIO_STORAGE_KEY = `ceo_agent_scenario:${ACCOUNT_SCOPE}`;
const ACTIVE_JOB_STORAGE_KEY = `ceo_active_job:${ACCOUNT_SCOPE}`;
const LEGACY_DASHBOARD_CONFIG = window.LEGACY_DASHBOARD_CONFIG || {};
const SCENARIO_STORAGE_SCHEMA_VERSION = LEGACY_DASHBOARD_CONFIG.defaults?.scenario_schema_version || 1;
const SCENARIO_DEFAULTS_VERSION = LEGACY_DASHBOARD_CONFIG.defaults?.scenario_defaults_version || (LEGACY_DASHBOARD_CONFIG.isProduction ? 'production' : 'development');
const INDUSTRY_OPTIONS = new Set([
    'Technology',
    'Healthcare',
    'Financial Services',
    'Manufacturing',
    'Retail',
    'Construction',
    'Real Estate',
    'Education',
    'Transportation & Logistics',
    'Hospitality & Tourism',
    'Entertainment'
]);

// Default objectives are intentionally empty — agents operate on company-specific context
const DEFAULT_DEV_OBJECTIVES = [];

const LEGACY_OBJECTIVE_MARKERS = new Set([
    'Launch SaaS platform',
    'Build enterprise sales team',
    'Establish market presence',
    'Scale to $1M ARR'
]);

// State management
const state = {
    agents: [],
    tasks: [],
    budget: {
        total: 0,
        remaining: 0,
        allocated: {}
    },
    executionStatus: 'idle'
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Dashboard initializing...');

    // Initialize SocketIO
    try {
        socket = io({auth: {csrf: document.querySelector('meta[name="csrf-token"]').content}});
        console.log('✅ SocketIO initialized');
    } catch (error) {
        console.error('❌ SocketIO initialization failed:', error);
    }

    loadAvailableAgents();
    setupSocketListeners();
    addLogEntry('System initialized', 'success');

    // Setup button event listeners as backup
    setupButtonListeners();

    // Initialize chat interface
    initializeChat();

    // Persist and hydrate scenario data for cross-page consistency (/ -> /admin)
    initializeScenarioSync();

    console.log('✅ Dashboard initialized');
});

function buildDefaultObjectives(companyInfo) {
    void companyInfo;
    return [...DEFAULT_DEV_OBJECTIVES];
}

function getDefaultScenario() {
    const configDefaults = LEGACY_DASHBOARD_CONFIG.defaults || {};

    if (LEGACY_DASHBOARD_CONFIG.isProduction) {
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
        budget: Number.parseFloat(configDefaults.budget) || 0,
        timeline: Number.parseInt(configDefaults.timeline, 10) || 0,
        objectives: Array.isArray(configDefaults.objectives) && configDefaults.objectives.length > 0
            ? configDefaults.objectives
            : [...DEFAULT_DEV_OBJECTIVES]
    };
}

function isLegacyScenarioShape(scenario) {
    if (!scenario || typeof scenario !== 'object') return false;

    let score = 0;
    if (['Software & Technology', 'AI Technology', 'General Business'].includes((scenario.industry || '').trim())) {
        score += 1;
    }
    if (['San Francisco, CA', 'United States', 'Cincinnati, Ohio'].includes((scenario.location || '').trim())) {
        score += 1;
    }

    const budget = Number.parseFloat(scenario.budget);
    if (Number.isFinite(budget) && [5000, 100000].includes(budget)) {
        score += 1;
    }

    const timeline = Number.parseInt(scenario.timeline, 10);
    if (Number.isFinite(timeline) && timeline === 90) {
        score += 1;
    }

    const objectives = Array.isArray(scenario.objectives) ? scenario.objectives : [];
    if (objectives.some((item) => LEGACY_OBJECTIVE_MARKERS.has(item))) {
        score += 1;
    }

    return score >= 2;
}

function buildScenarioEnvelope(scenario, options = {}) {
    return {
        meta: {
            schema_version: SCENARIO_STORAGE_SCHEMA_VERSION,
            defaults_version: SCENARIO_DEFAULTS_VERSION,
            environment: LEGACY_DASHBOARD_CONFIG.isProduction ? 'production' : 'development',
            source: options.source || 'legacy_dashboard',
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
        if (!parsed || typeof parsed !== 'object') return null;

        if (parsed.scenario && typeof parsed.scenario === 'object') {
            const meta = parsed.meta || {};
            const schemaMatch = meta.schema_version === SCENARIO_STORAGE_SCHEMA_VERSION;
            const defaultsMatch = meta.defaults_version === SCENARIO_DEFAULTS_VERSION;

            if (schemaMatch && defaultsMatch) {
                return parsed.scenario;
            }

            if (!LEGACY_DASHBOARD_CONFIG.isProduction && !meta.user_modified && isLegacyScenarioShape(parsed.scenario)) {
                return getDefaultScenario();
            }

            return parsed.scenario;
        }

        if (parsed.company_name || parsed.industry || parsed.location) {
            if (!LEGACY_DASHBOARD_CONFIG.isProduction && isLegacyScenarioShape(parsed)) {
                return getDefaultScenario();
            }
            return parsed;
        }
    } catch (error) {
        console.warn('Failed to parse scenario envelope:', error);
    }

    return null;
}

function setIndustryValue(industryValue) {
    const industrySelect = document.getElementById('industry');
    const industryOtherInput = document.getElementById('industryOther');
    const industryOtherGroup = document.getElementById('industryOtherGroup');
    const normalized = (industryValue || '').trim();

    if (!industrySelect || !industryOtherInput || !industryOtherGroup) {
        return;
    }

    if (!normalized) {
        industrySelect.value = '';
        industryOtherInput.value = '';
        industryOtherGroup.style.display = 'none';
        return;
    }

    if (INDUSTRY_OPTIONS.has(normalized)) {
        industrySelect.value = normalized;
        industryOtherInput.value = '';
        industryOtherGroup.style.display = 'none';
    } else {
        industrySelect.value = 'Other';
        industryOtherInput.value = normalized;
        industryOtherGroup.style.display = 'block';
    }
}

function getIndustryValueFromForm() {
    const industrySelect = document.getElementById('industry');
    const industryOtherInput = document.getElementById('industryOther');

    if (!industrySelect) {
        return '';
    }

    if (industrySelect.value === 'Other') {
        return industryOtherInput?.value?.trim() || '';
    }

    return industrySelect.value || '';
}

function bindIndustrySelectorBehavior() {
    const industrySelect = document.getElementById('industry');
    const industryOtherInput = document.getElementById('industryOther');
    const industryOtherGroup = document.getElementById('industryOtherGroup');

    if (!industrySelect || !industryOtherInput || !industryOtherGroup) {
        return;
    }

    industrySelect.addEventListener('change', () => {
        const showOther = industrySelect.value === 'Other';
        industryOtherGroup.style.display = showOther ? 'block' : 'none';
        if (!showOther) {
            industryOtherInput.value = '';
        }
    });
}

function getScenarioFromForm() {
    const defaults = getDefaultScenario();
    const companyNameInput = document.getElementById('companyName');
    const dbaNameInput = document.getElementById('dbaName');
    const locationInput = document.getElementById('location');
    const budgetInput = document.getElementById('budget');
    const timelineInput = document.getElementById('timeline');

    const parsedBudget = Number(budgetInput?.value || '');
    const parsedTimeline = Number(timelineInput?.value || '');

    const companyInfo = {
        company_name: companyNameInput?.value || defaults.company_name,
        dba_name: dbaNameInput?.value || companyNameInput?.value || defaults.dba_name,
        industry: getIndustryValueFromForm() || defaults.industry,
        location: locationInput?.value || defaults.location,
        budget: Number.isFinite(parsedBudget) ? parsedBudget : defaults.budget,
        timeline: Number.isFinite(parsedTimeline) ? parsedTimeline : defaults.timeline
    };

    // Read strategic objectives from the textarea if present
    const objectivesInput = document.getElementById('objectives');
    const objectivesText = objectivesInput?.value?.trim() || '';
    const parsedObjectives = objectivesText
        ? objectivesText.split('\n').map(s => s.trim()).filter(Boolean)
        : (Array.isArray(defaults.objectives) ? defaults.objectives : buildDefaultObjectives(companyInfo));

    return {
        ...companyInfo,
        objectives: parsedObjectives,
        updated_at: new Date().toISOString()
    };
}

function validateScenarioForExecution(scenario) {
    const checks = [
        ['companyName', typeof scenario.company_name === 'string' && scenario.company_name.trim(), 'Enter a Company Name.'],
        ['industry', typeof scenario.industry === 'string' && scenario.industry.trim(), 'Select an Industry (and specify it when selecting Other).'],
        ['location', typeof scenario.location === 'string' && scenario.location.trim(), 'Enter a Location.'],
        ['budget', Number.isFinite(scenario.budget) && scenario.budget > 0, 'Enter a Budget ($) greater than 0. This is your scenario budget, not the model API spending limit.'],
        ['timeline', Number.isInteger(scenario.timeline) && scenario.timeline > 0, 'Enter a Timeline in whole days greater than 0.'],
        ['objectives', Array.isArray(scenario.objectives) && scenario.objectives.length > 0 &&
            scenario.objectives.every(item => typeof item === 'string' && item.trim()), 'Enter at least one Strategic Objective.']
    ];
    const invalid = checks.find(([, valid]) => !valid);
    if (!invalid) return true;
    const [field, , message] = invalid;
    updateStatus(message, 'error');
    addLogEntry(`Execution blocked: ${message}`, 'error');
    addChatMessage(`⚠️ ${message} No analysis or execution was started.`, 'system');
    document.getElementById(field)?.focus();
    return false;
}

function applyScenarioToForm(scenario) {
    if (!scenario || typeof scenario !== 'object') {
        return;
    }

    const fieldMap = {
        companyName: scenario.company_name,
        dbaName: scenario.dba_name,
        location: scenario.location,
        budget: scenario.budget,
        timeline: scenario.timeline
    };

    Object.entries(fieldMap).forEach(([elementId, value]) => {
        const input = document.getElementById(elementId);
        if (input && value !== undefined && value !== null) {
            input.value = value;
        }
    });

    setIndustryValue(scenario.industry);

    // Populate strategic objectives textarea if present
    const objectivesInput = document.getElementById('objectives');
    if (objectivesInput && Array.isArray(scenario.objectives)) {
        objectivesInput.value = scenario.objectives.join('\n');
    }
    state.budget.total = Number(scenario.budget) || 0;
    state.budget.remaining = state.budget.total;
    const totalDisplay = document.getElementById('totalBudget');
    const remainingDisplay = document.getElementById('remainingBudget');
    if (totalDisplay) totalDisplay.textContent = `$${state.budget.total.toLocaleString()}`;
    if (remainingDisplay) remainingDisplay.textContent = `$${state.budget.remaining.toLocaleString()}`;
}

async function syncScenarioToBackend(scenario) {
    try {
        // Only send fields the backend allowlist accepts — prevents stale-key 400s
        const safe = {
            company_name: scenario.company_name,
            name: scenario.name,
            dba_name: scenario.dba_name,
            industry: scenario.industry,
            location: scenario.location,
            budget: scenario.budget,
            timeline: scenario.timeline,
            objectives: scenario.objectives,
            updated_at: scenario.updated_at,
        };
        // Remove undefined keys
        Object.keys(safe).forEach(k => safe[k] === undefined && delete safe[k]);
        const response = await fetch('/api/scenario/current', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(safe)
        });
        if (!response.ok) throw new Error('Scenario synchronization failed');
    } catch (error) {
        console.warn('Scenario sync to backend failed:', error);
    }
}

function persistScenarioToStorage(options = {}) {
    const scenario = getScenarioFromForm();
    state.budget.total = Number(scenario.budget) || 0;
    const envelope = buildScenarioEnvelope(scenario, {
        source: options.source || 'legacy_form',
        userModified: Boolean(options.userModified)
    });
    localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(envelope));

    if (options.syncBackend !== false) {
        syncScenarioToBackend(scenario);
    }

    return scenario;
}

function hydrateScenarioFromStorage() {
    if (LEGACY_DASHBOARD_CONFIG.isProduction) {
        const defaults = getDefaultScenario();
        applyScenarioToForm(defaults);
        localStorage.removeItem(SCENARIO_STORAGE_KEY);
        return;
    }

    const raw = localStorage.getItem(SCENARIO_STORAGE_KEY);
    if (!raw) {
        persistScenarioToStorage({ syncBackend: false, userModified: false, source: 'init_defaults' });
        return;
    }

    const scenario = parseScenarioEnvelope(raw);
    if (!scenario || typeof scenario !== 'object') {
        persistScenarioToStorage({ syncBackend: false, userModified: false, source: 'init_reset' });
        return;
    }

    applyScenarioToForm(scenario);
    localStorage.setItem(
        SCENARIO_STORAGE_KEY,
        JSON.stringify(buildScenarioEnvelope(scenario, { source: 'init_migrated', userModified: false }))
    );
}

function initializeScenarioSync() {
    bindIndustrySelectorBehavior();
    hydrateScenarioFromStorage();

    let syncTimer;
    const handleUserChange = () => {
        persistScenarioToStorage({ syncBackend: false, userModified: true, source: 'user_change' });
        clearTimeout(syncTimer);
        syncTimer = setTimeout(() => syncScenarioToBackend(getScenarioFromForm()), 400);
    };

    ['companyName', 'dbaName', 'industry', 'industryOther', 'location', 'budget', 'timeline', 'objectives'].forEach((elementId) => {
        const input = document.getElementById(elementId);
        if (!input) {
            return;
        }

        input.addEventListener('input', handleUserChange);
        input.addEventListener('change', handleUserChange);
    });

    if (LEGACY_DASHBOARD_CONFIG.isProduction) {
        syncScenarioToBackend(getScenarioFromForm());
        return;
    }
}

// Setup button event listeners
function setupButtonListeners() {
    const launchBtn = document.getElementById('launchOrchestration');
    const analyzeBtn = document.getElementById('analyzeBtn');

    if (launchBtn) {
        launchBtn.addEventListener('click', function (e) {
            e.preventDefault();
            console.log('🚀 Launch button clicked (event listener)');
            runFullOrchestration();
        });
        console.log('✅ Launch orchestration button listener attached');
    }

    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', function (e) {
            e.preventDefault();
            console.log('🔍 Analyze button clicked (event listener)');
            analyzeObjectives();
        });
        console.log('✅ Analyze button listener attached');
    }
}

// Setup Socket.IO event listeners
function setupSocketListeners() {
    if (!socket) {
        console.error('❌ Socket not initialized');
        return;
    }

    socket.on('connect', () => {
        console.log('✅ Socket.IO connected');
        addLogEntry('Connected to server', 'success');
        addChatMessage('🌐 Connected to CEO Executive Agent server. Real-time updates enabled.', 'system');
    });

    socket.on('disconnect', () => {
        console.log('⚠️ Socket.IO disconnected');
        addLogEntry('Disconnected from server', 'warning');
        addChatMessage('⚠️ Disconnected from server. Attempting to reconnect...', 'system');
    });

    socket.on('scenario_updated', (data) => {
        if (!data || !data.scenario) {
            return;
        }

        localStorage.setItem(
            SCENARIO_STORAGE_KEY,
            JSON.stringify(buildScenarioEnvelope(data.scenario, { source: 'socket_sync', userModified: false }))
        );

        // Only update the form when the user is NOT actively editing a field.
        // This prevents the socket echo from overwriting mid-keystroke input.
        const active = document.activeElement;
        const cfgBody = document.getElementById('cfgBody');
        const userIsEditing = cfgBody && cfgBody.contains(active) && (
            active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.tagName === 'SELECT'
        );
        if (!userIsEditing) {
            applyScenarioToForm(data.scenario);
        }
        addLogEntry('Scenario context synchronized', 'success');
    });

    socket.on('phase', (data) => {
        if (data.status === 'running') {
            updateStatus(`Phase: ${data.name} - Running...`, 'running');
            addLogEntry(`Phase: ${data.name} - Starting`, 'warning');
            showProgressBar();
            updateProgress(25);
        } else if (data.status === 'complete') {
            addLogEntry(`Phase: ${data.name} - Complete ✓`, 'success');
            if (data.tasks) {
                displayTasks(data.tasks);
            }
            updateProgress(50);
        }
    });

    socket.on('agent_deploying', (data) => {
        addLogEntry(`Deploying ${data.agent.toUpperCase()} Agent for task ${data.task}...`, 'warning');
        highlightAgent(data.agent, 'deploying');

        // Chat notification - agent deploying
        const agentName = data.agent.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        addChatMessage(`🔄 Deploying ${agentName} Agent for: ${data.task}`, 'system');
    });

    socket.on('agent_deployed', (data) => {
        addLogEntry(`${data.agent.toUpperCase()} Agent deployed successfully ✓`, 'success');
        highlightAgent(data.agent, 'active');
        updateProgress(75);

        // Chat notification - agent deployed
        const agentName = data.agent.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        addChatMessage(`✅ ${agentName} Agent deployed and ready!`, 'assistant');
    });

    socket.on('orchestration_complete', (data) => {
        console.log('🎉 Orchestration complete event received:', data);

        updateStatus('Orchestration complete! All agents executed successfully.', 'success');
        addLogEntry(`Total budget used: $${data.budget_used}`, 'success');
        updateProgress(100);

        // Display comprehensive orchestration report
        const companyInfo = {
            company_name: data.company_name || 'Company',
            industry: data.industry || 'N/A',
            location: data.location || 'N/A'
        };

        const analysisData = {
            tasks: data.tasks || [],
            budget_allocation: data.budget_allocation || {},
            risks: data.risks || [],
            opportunities: data.opportunities || [],
            timeline: data.timeline ?? 0,
            deliverables: data.deliverables || [],
            agent_outputs: data.agent_outputs || [],
            completed_tasks: data.completed_tasks || 0,
            total_tasks: data.total_tasks || 0,
            budget_used: data.budget_used || 0,
            budget_remaining: data.budget_remaining || 0,
            total_budget: data.total_budget || 0
        };

        console.log('📊 Displaying orchestration report with:', analysisData);
        displayOrchestrationReport(companyInfo, analysisData); // switches to Reports tab internally

        // Feed card with link back to the now-visible report
        addFeedCard(
            'success',
            '🎯 Orchestration Complete',
            (data.completed_tasks || 0) + ' of ' + (data.total_tasks || 0) + ' tasks',
            null,
            [
                { val: data.completed_tasks || 0, lbl: 'Done' },
                { val: '$' + (data.budget_used || 0), lbl: 'Used' },
                { val: data.total_tasks || 0, lbl: 'Total' },
            ],
            [{ label: '📄 View Report', onclick: "switchTab('reports', document.querySelector(\"[data-tab='reports']\"))", primary: true }]
        );

        // Chat notification - orchestration complete
        addChatMessage(`🎉 Full orchestration complete! Executed ${data.total_tasks || 0} tasks. Total budget used: $${data.budget_used}. The Execution Report is now open.`, 'assistant');

        setTimeout(() => {
            hideProgressBar();
        }, 2000);
    });

    socket.on('orchestration_error', (data) => {
        updateStatus(`Error: ${data.error}`, 'error');
        addChatMessage(`❌ Orchestration error: ${data.error}`, 'error');
        addLogEntry(`Error: ${data.error}`, 'error');
        hideProgressBar();
    });

    // ── LLM Agent Chat reply ─────────────────────────────────────────────
    socket.on('ai_chat_response', function (data) {
        setChatStatus('');
        if (data && data.message) addChatMessage(data.message, data.error ? 'error' : 'assistant');
    });

    socket.on('execution_started', (data) => {
        state.activeThreadId = data.thread_id;
        if (data.job_id) {
            localStorage.setItem(ACTIVE_JOB_STORAGE_KEY, data.job_id);
            watchDurableJob(data.job_id);
        }
        updateStatus('Generating local artifacts...', 'running');
        showProgressBar();
    });
    socket.on('phase_update', (data) => {
        updateStatus(data.message, 'running');
        updateProgress(data.progress);
    });
    socket.on('agent_update', (data) => {
        highlightAgent(data.agent, data.status);
        addLogEntry(data.message, 'info');
    });
    socket.on('execution_complete', (data) => {
        if (state.activeThreadId && data.thread_id !== state.activeThreadId) return;
        const result = data.result || {};
        updateStatus('Local artifacts generated; no external actions executed.', 'success');
        updateProgress(100);
        displayAgentReport('ceo', {
            agent_type: 'ceo',
            status: 'artifacts_generated',
            ...result,
            deliverables: [],
        }, getScenarioFromForm());
        addChatMessage('Local artifact generation complete. Review the files in Reports. No publishing, purchases, deployment or outreach was performed.', 'assistant');
        hideProgressBar();
    });
    socket.on('execution_error', (data) => {
        updateStatus('Execution failed', 'error');
        addLogEntry(data.error, 'error');
        addChatMessage(`Execution failed: ${data.error}`, 'error');
        hideProgressBar();
    });

    // ── Agent lifecycle → live feed cards ───────────────────────────────
    socket.on('agent_deploying', function (data) {
        const name = (data.agent || '').split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        addFeedCard('running', '🔄 ' + name + ' Agent Deploying',
            'Task: ' + (data.task || 'executing'), null, null, null);
    });

    socket.on('agent_deployed', function (data) {
        const name = (data.agent || '').split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        addFeedCard('success', '✅ ' + name + ' Agent Ready', 'Deployed successfully',
            null, null, [{ label: 'View Details', onclick: "viewAgentDetails('" + data.agent + "')" }]);
    });

    // orchestration_complete feed card is handled in the primary listener above

    console.log('✅ Socket listeners configured');
}

// Load available agents
async function loadAvailableAgents() {
    try {
        const response = await fetch('/api/agents/available');
        const data = await response.json();

        if (data.agents) {
            state.agents = data.agents;
            displayAgents(data.agents);
            addLogEntry(`Loaded ${data.agents.length} specialized agents`, 'success');
        }
    } catch (error) {
        console.error('Error loading agents:', error);
        addLogEntry('Error loading agents', 'error');
    }
}

// Display agents in grid
function displayAgents(agents) {
    const container = document.getElementById('agentsContainer');
    if (!container) {
        console.error('❌ agentsContainer element not found');
        return;
    }
    container.innerHTML = '';

    const colors = [
        'linear-gradient(160deg, #1e3a5f 0%, #1d4ed8 100%)',
        'linear-gradient(160deg, #1e293b 0%, #0f4060 100%)',
        'linear-gradient(160deg, #164e63 0%, #0369a1 100%)',
        'linear-gradient(160deg, #14532d 0%, #166534 100%)',
        'linear-gradient(160deg, #1c1917 0%, #44403c 100%)',
        'linear-gradient(160deg, #1e1b4b 0%, #312e81 100%)'
    ];

    agents.forEach((agent, index) => {
        const card = document.createElement('div');
        card.className = 'agent-card';
        card.style.background = colors[index % colors.length];
        card.id = `agent-${agent.type}`;

        const capabilitiesList = agent.capabilities.slice(0, 3).map(cap =>
            `<li>${cap}</li>`
        ).join('');

        card.innerHTML = `
            <div class="agent-header">
                <div>
                    <div class="agent-name">${getAgentIcon(agent.type)} ${agent.name}</div>
                    <div class="agent-type">${agent.type}</div>
                </div>
                <div class="agent-status">${agent.status}</div>
            </div>
            <div class="agent-budget">$${agent.budget.toFixed(0)}</div>
            <ul class="agent-capabilities">
                ${capabilitiesList}
            </ul>
            <div class="agent-actions">
                <button class="btn btn-small" style="background: rgba(255,255,255,0.9); color: #1A365D;"
                        onclick="viewAgentDetails('${agent.type}')">
                    View Details
                </button>
                <button class="btn btn-small" style="background: rgba(255,255,255,0.2); color: white;"
                        onclick="executeAgent('${agent.type}')">
                    Execute
                </button>
            </div>
        `;

        container.appendChild(card);
    });
}

// Get agent icon
function getAgentIcon(type) {
    const icons = {
        'branding': '🎨',
        'web_development': '💻',
        'legal': '⚖️',
        'martech': '📊',
        'content': '📸',
        'campaigns': '🚀'
    };
    return icons[type] || '🤖';
}

// Agent configurations for reports and modals
const agentConfigs = {
    'ceo': { icon: '👔', name: 'CEO Orchestration' },
    'cto': { icon: '🔧', name: 'CTO Architecture' },
    'engineer': { icon: '🛠️', name: 'Engineering' },
    'software_eng': { icon: '💻', name: 'Software Review' },
    'branding': { icon: '🎨', name: 'Branding & Visual Identity' },
    'web_development': { icon: '💻', name: 'Web Development' },
    'legal': { icon: '⚖️', name: 'Legal Compliance' },
    'martech': { icon: '📊', name: 'Marketing Technology' },
    'content': { icon: '📸', name: 'Content Creation' },
    'campaigns': { icon: '🚀', name: 'Campaign Management' }
};

// Analyze objectives
async function analyzeObjectives() {
    console.log('🔍 Analyze button clicked');
    try {
        const scenario = persistScenarioToStorage();
        if (!validateScenarioForExecution(scenario)) return;
        updateStatus('Analyzing strategic objectives...', 'running');
        addLogEntry('CEO Agent: Initiating executive orchestration analysis', 'info');

        // Explicitly pick only the fields the backend allowlist accepts
        // to avoid accidental rejection if the scenario object grows extra keys
        const analyzePayload = {
            company_name: scenario.company_name,
            dba_name: scenario.dba_name,
            industry: scenario.industry,
            location: scenario.location,
            budget: scenario.budget,
            timeline: scenario.timeline,
            objectives: scenario.objectives,
            updated_at: scenario.updated_at
        };

        console.log('Analyze payload:', analyzePayload);

        // Chat notification - analysis starting
        addChatMessage(`� CEO Agent: Initiating multidisciplinary strategic intake for **${scenario.company_name}**...`, 'system');

        const response = await fetch('/api/ceo/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(analyzePayload)
        });

        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Response data:', data);

        if (data.success) {
            displayTasks(data.tasks);
            updateBudgetDisplay(data.budget_allocation);
            updateStatus('Strategic analysis complete!', 'success');
            const domainCount = Object.keys(data.budget_allocation || {}).length || Object.keys(data.domain_sections || {}).length;
            addLogEntry(`CEO: ${data.tasks.length} tasks across ${domainCount} domains | $${(data.budget || 0).toLocaleString()} budget`, 'success');

            // Surface Prompt Expert intake result in chat
            const pe = data.prompt_expert || {};
            if (pe.intent_summary) {
                addChatMessage(
                    `🧠 **Research & Prompt Agent intake complete**\n` +
                    `Intent: ${pe.intent_summary}\n` +
                    `Primary domain: ${pe.primary_domain || 'strategy'}` +
                    (pe.confidence_score ? ` • Confidence: ${Math.round(pe.confidence_score * 100)}%` : '') +
                    (pe.ambiguities && pe.ambiguities.length ? `\n⚠️ Ambiguities: ${pe.ambiguities.join('; ')}` : ''),
                    'system'
                );
            }

            // CEO directives in chat
            if (data.ceo_directives && data.ceo_directives.length) {
                addChatMessage(
                    `👔 **CEO Executive Directives**\n` +
                    data.ceo_directives.slice(0, 3).map((d, i) => `${i + 1}. ${d}`).join('\n'),
                    'assistant'
                );
            }

            // Display analysis report in execution report section
            displayAnalysisReport(data.company_name ? data : scenario, data);

            // Chat notification - analysis complete
            addChatMessage(
                `✅ **CEO Executive Analysis complete!**\n` +
                `${data.tasks.length} tasks identified across ${domainCount} domains.\n` +
                `Budget: $${(data.budget || 0).toLocaleString()} | Timeline: ${data.timeline} days`,
                'assistant'
            );
        } else {
            updateStatus(`Error: ${data.error}`, 'error');
            addLogEntry(`Analysis failed: ${data.error}`, 'error');
            const errDetail = (data.details && data.details.length) ? `\n  → ${data.details.join('\n  → ')}` : '';
            addChatMessage(`❌ Analysis failed: ${data.error}${errDetail}`, 'error');
        }
    } catch (error) {
        console.error('Analyze error:', error);
        updateStatus('Analysis failed', 'error');
        addLogEntry(`Error: ${error.message}`, 'error');
        addChatMessage(`❌ Error during analysis: ${error.message}`, 'error');
    }
}

// Run full orchestration
async function runFullOrchestration() {
    console.log('🚀 Launch Full Orchestration button clicked');
    try {
        const scenario = persistScenarioToStorage();
        if (!validateScenarioForExecution(scenario)) return;
        const companyInfo = {
            company_name: scenario.company_name,
            dba_name: scenario.dba_name,
            industry: scenario.industry,
            location: scenario.location,
            budget: scenario.budget,
            timeline: scenario.timeline
        };

        const objectives = Array.isArray(scenario.objectives) && scenario.objectives.length > 0
            ? scenario.objectives
            : buildDefaultObjectives(companyInfo);

        console.log('Starting graph orchestration with:', { company_info: companyInfo, objectives });

        // Chat notification - orchestration starting
        addChatMessage(`🚀 Launching graph orchestration for ${companyInfo.company_name}. This will invoke the multi-agent execution path...`, 'system');

        const response = await fetch('/api/graph/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company_name: companyInfo.company_name,
                dba_name: companyInfo.dba_name,
                industry: companyInfo.industry,
                location: companyInfo.location,
                total_budget: companyInfo.budget,
                target_days: companyInfo.timeline,
                objectives: objectives,
            }),
        });

        const data = await response.json();
        if (response.ok && data.success) {
            state.activeThreadId = data.thread_id;
            if (data.job_id) {
                localStorage.setItem(ACTIVE_JOB_STORAGE_KEY, data.job_id);
                watchDurableJob(data.job_id);
            }
            addLogEntry('Graph execution request accepted by server.', 'success');
            addChatMessage('✅ Graph execution request submitted. Check the dashboard for progress.', 'assistant');
        } else {
            addLogEntry(`Graph execution failed: ${data.error || response.statusText}`, 'error');
            addChatMessage(`❌ Graph execution failed: ${data.error || response.statusText}`, 'error');
        }
    } catch (error) {
        console.error('Orchestration error:', error);
        addLogEntry(`Error launching orchestration: ${error.message}`, 'error');
        addChatMessage(`❌ Orchestration failed: ${error.message}`, 'error');
    }
}

// Execute specific agent
async function executeAgent(agentType) {
    console.log(`🤖 Execute button clicked for: ${agentType}`);

    // CEO is the orchestration entry-point — route to full orchestration
    if (agentType === 'ceo') {
        try {
            const scenario = persistScenarioToStorage({ syncBackend: false });
            if (!validateScenarioForExecution(scenario)) return;
            addLogEntry('CEO Agent: Initiating full multi-agent orchestration...', 'info');
            addChatMessage(
                `👔 **CEO Agent activated** — launching full orchestration for **${scenario.company_name || 'your company'}**.\n` +
                `CEO will coordinate all specialized agents and emit the final executive report.`,
                'system'
            );
            const companyInfo = {
                company_name: scenario.company_name,
                name: scenario.company_name,
                dba_name: scenario.dba_name,
                industry: scenario.industry,
                location: scenario.location,
                budget: scenario.budget,
                timeline: scenario.timeline
            };
            const response = await fetch('/api/graph/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    company_name: companyInfo.company_name,
                    dba_name: companyInfo.dba_name,
                    industry: companyInfo.industry,
                    location: companyInfo.location,
                    total_budget: companyInfo.budget,
                    target_days: companyInfo.timeline,
                    objectives: scenario.objectives || [],
                }),
            });

            const result = await response.json();
            if (response.ok && result.success) {
                state.activeThreadId = result.thread_id;
                if (result.job_id) {
                    localStorage.setItem(ACTIVE_JOB_STORAGE_KEY, result.job_id);
                    watchDurableJob(result.job_id);
                }
                addChatMessage('✅ CEO orchestration request accepted. Monitoring execution progress...', 'assistant');
            } else {
                addChatMessage(`❌ CEO orchestration failed: ${result.error || response.statusText}`, 'error');
            }
            highlightAgent('ceo', 'executing');
        } catch (err) {
            addChatMessage(`❌ CEO orchestration failed to start: ${err.message}`, 'error');
        }
        return;
    }

    addLogEntry(`Executing ${agentType.toUpperCase()} Agent...`, 'warning');
    highlightAgent(agentType, 'executing');

    try {
        const scenario = persistScenarioToStorage();
        if (!validateScenarioForExecution(scenario)) return;
        const companyInfo = {
            company_name: scenario.company_name,
            name: scenario.company_name,
            dba_name: scenario.dba_name,
            industry: scenario.industry,
            location: scenario.location,
            budget: scenario.budget,
            timeline: scenario.timeline
        };

        // Chat notification - agent starting
        const agentName = agentType.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        addChatMessage(`⚙️ Executing ${agentName} Agent for ${companyInfo.company_name || 'your company'}...`, 'system');

        console.log('Executing agent with data:', { agentType, companyInfo });

        const response = await fetch(`/api/agent/execute/${agentType}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                task: `Execute ${agentType} tasks`,
                company_info: {
                    company_name: companyInfo.company_name,
                    name: companyInfo.company_name,
                    dba_name: companyInfo.dba_name,
                    industry: companyInfo.industry,
                    location: companyInfo.location,
                    budget: companyInfo.budget,
                    timeline: companyInfo.timeline
                },
                strategic_objectives: scenario.objectives || []
            })
        });

        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Response data:', data);

        if (data.success) {
            console.log('✅ Agent execution successful!');
            console.log('Result data:', data.result);
            console.log('Deliverables found:', data.result.deliverables);

            addLogEntry(`${agentType.toUpperCase()} Agent execution complete ✓`, 'success');
            addLogEntry('Local artifacts generated. Actual provider spending is not measured.', 'info');
            if (data.result.deliverables && data.result.deliverables.length > 0) {
                addLogEntry(`Deliverables: ${data.result.deliverables.length} items created`, 'success');
            }
            highlightAgent(agentType, 'complete');
            updateStatus(`${agentType} agent completed successfully`, 'success');

            // Chat notification - agent complete
            const agentName = agentType.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
            const deliverableCount = data.result.artifacts?.length || 0;
            addChatMessage(`✅ ${agentName} generated ${deliverableCount} local artifacts. No external actions were performed. Check the Execution Report for details.`, 'assistant');

            // IMPORTANT: Display report in the report area FIRST
            console.log('📊 Displaying report in main report area...');
            displayAgentReport(agentType, data.result, companyInfo);

            // THEN show results modal
            console.log('🔄 Showing results modal...');
            showAgentResults(agentType, data.result, companyInfo);
        } else {
            addLogEntry(`${agentType.toUpperCase()} Agent failed: ${data.error}`, 'error');
            highlightAgent(agentType, 'error');
            updateStatus(`Error: ${data.error}`, 'error');

            // Chat notification - agent failed
            const agentName = agentType.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
            const errDetail = data.details && data.details.length ? ` (${data.details.join('; ')})` : '';
            addChatMessage(`❌ ${agentName} Agent failed: ${data.error}${errDetail}`, 'error');
        }
    } catch (error) {
        console.error('Execute agent error:', error);
        addLogEntry(`Error executing agent: ${error.message}`, 'error');
        highlightAgent(agentType, 'error');
        updateStatus(`Error executing agent: ${error.message}`, 'error');

        // Chat notification - execution error
        const agentName = agentType.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        addChatMessage(`❌ Error executing ${agentName} Agent: ${error.message}`, 'error');
    }
}

// View agent details
async function viewAgentDetails(agentType) {
    console.log(`👁️ View Details clicked for: ${agentType}`);
    try {
        addLogEntry(`Loading ${agentType} agent details...`, 'warning');

        // Chat notification - viewing details
        const agentName = agentType.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        addChatMessage(`📋 Opening ${agentName} Agent details and guard rails...`, 'system');

        const response = await fetch(`/api/guard-rails/${agentType}`);
        console.log('Guard rails response status:', response.status);
        const data = await response.json();
        console.log('Guard rails data:', data);

        if (data.success) {
            showAgentModal(agentType, data.guard_rail);
            addLogEntry(`${agentType} agent details loaded`, 'success');
            const limitLabel = (data.guard_rail.quality_standards && data.guard_rail.quality_standards.budget_unit && data.guard_rail.quality_standards.budget_unit.includes("API cost"))
                ? `API spend cap: $${data.guard_rail.max_budget}`
                : `Budget limit: $${data.guard_rail.max_budget.toLocaleString()}`;
            addChatMessage(`✅ ${agentName} Agent details loaded. ${limitLabel}`, 'assistant');
        } else {
            addLogEntry(`Failed to load agent details: ${data.error}`, 'error');
            console.error('Failed to load guard rails:', data.error);
            addChatMessage(`❌ Failed to load agent details: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error loading guard rails:', error);
        addLogEntry(`Error loading agent details: ${error.message}`, 'error');
        addChatMessage(`❌ Error loading agent details: ${error.message}`, 'error');
    }
}

// Show agent modal
function showAgentModal(agentType, guardRail) {
    const modal = document.getElementById('agentModal');
    const content = document.getElementById('modalContent');

    const permittedTasks = guardRail.permitted_tasks.map(task =>
        `<li>✅ ${task}</li>`
    ).join('');

    const allowedCategories = guardRail.allowed_categories.map(cat =>
        `<li>💰 ${cat}</li>`
    ).join('');

    const isApiSpendCap = guardRail.quality_standards && guardRail.quality_standards.budget_unit && guardRail.quality_standards.budget_unit.includes("API cost");
    const budgetBadgeTitle = isApiSpendCap ? "API Spend Ceiling (Per-Call Cost Metering)" : "Allocated Scenario Budget";
    const budgetNote = isApiSpendCap 
        ? `<div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">Per-call model inference safety cap. Not your business scenario budget.</div>`
        : `<div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">Dynamic business budget governed by CEO Orchestrator.</div>`;

    content.innerHTML = `
        <h2 style="margin-top: 0; color: #f8fafc; font-size: 1.35rem; display: flex; align-items: center; gap: 0.5rem;">
            ${getAgentIcon(agentType)} ${agentType.toUpperCase().replace('_', ' ')} Agent Details
        </h2>

        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 10px; padding: 1rem; margin-bottom: 1.25rem;">
            <div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; font-weight: 700;">${budgetBadgeTitle}</div>
            <p style="font-size: 26px; font-weight: 700; color: #10B981; margin: 4px 0 0 0;">$${guardRail.max_budget.toLocaleString()}</p>
            ${budgetNote}
        </div>

        <h3 style="color: #cbd5e1; font-size: 0.95rem; margin-top: 1rem; margin-bottom: 0.5rem;">✅ Permitted Tasks (Execution Scope)</h3>
        <ul style="list-style: none; padding-left: 0; margin-bottom: 1rem; display: flex; flex-direction: column; gap: 0.35rem; font-size: 0.85rem; color: #f1f5f9;">
            ${permittedTasks}
        </ul>

        <h3 style="color: #cbd5e1; font-size: 0.95rem; margin-top: 1rem; margin-bottom: 0.5rem;">💳 Allowed Categories</h3>
        <ul style="list-style: none; padding-left: 0; margin-bottom: 1rem; display: flex; flex-direction: column; gap: 0.35rem; font-size: 0.85rem; color: #f1f5f9;">
            ${allowedCategories}
        </ul>

        <h3 style="color: #cbd5e1; font-size: 0.95rem; margin-top: 1rem; margin-bottom: 0.5rem;">🛡️ Safety Guard Rails</h3>
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); padding: 14px; border-radius: 8px; color: #e2e8f0; font-size: 0.82rem; line-height: 1.55;">
            <strong>✅ Autonomous Execution:</strong> Direct AI delivery within sandboxed boundary.<br>
            <strong>✅ Cost Metering:</strong> Hard spend ceiling of $${guardRail.max_budget} per operation.<br>
            <strong>✅ Scope Validation:</strong> Enforces permitted tasks and approved deliverables.<br>
            <strong>✅ Standards:</strong> ${Object.keys(guardRail.quality_standards || {}).length} quality standards enforced.
        </div>
    `;

    modal.style.display = 'block';
}

// Close modal
function closeModal() {
    document.getElementById('agentModal').style.display = 'none';
}

// Show agent execution results
function showAgentResults(agentType, resultData, companyInfo) {
    console.log('🎯 showAgentResults called:', { agentType, resultData, companyInfo });

    const modal = document.getElementById('resultsModal');
    const content = document.getElementById('resultsContent');

    if (!modal) {
        console.error('❌ Results modal element not found!');
        alert('Error: Results modal not found. Please refresh the page.');
        return;
    }

    if (!content) {
        console.error('❌ Results content element not found!');
        alert('Error: Results content area not found. Please refresh the page.');
        return;
    }

    // Get agent configuration
    const agentConfig = agentConfigs[agentType];
    if (!agentConfig) {
        console.error('❌ Agent config not found for:', agentType);
        // Fallback to basic config
        const fallbackIcon = getAgentIcon(agentType);
        const agentName = agentType.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        agentConfigs[agentType] = { icon: fallbackIcon, name: agentName };
    }

    const agentName = agentType.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');

    // Format deliverables
    const deliverablesHTML = resultData.deliverables && resultData.deliverables.length > 0
        ? `<ul class="deliverables-list">
            ${resultData.deliverables.map(d => `<li>📦 ${d}</li>`).join('')}
           </ul>`
        : '<p>No deliverables available</p>';

    // Format tech stack if available
    const techStackHTML = resultData.tech_stack && resultData.tech_stack.length > 0
        ? `<div class="results-section">
            <h3>🛠️ Technology Stack</h3>
            <ul class="tech-stack-list">
                ${resultData.tech_stack.map(tech => `<li>${tech}</li>`).join('')}
            </ul>
           </div>`
        : '';

    // Format timeline if available
    const timelineHTML = resultData.timeline && resultData.timeline.length > 0
        ? `<div class="results-section">
            <h3>📅 Project Timeline</h3>
            ${resultData.timeline.map(item => `
                <div class="timeline-item">
                    <strong>${item.phase || item.week || 'Phase'}</strong>: ${item.description || item.deliverable || item}
                </div>
            `).join('')}
           </div>`
        : '';

    // Format budget breakdown if available
    const budgetBreakdownHTML = resultData.budget_breakdown
        ? `<div class="results-section">
            <h3>💰 Budget Breakdown</h3>
            <div class="results-grid">
                ${Object.entries(resultData.budget_breakdown).map(([key, value]) => `
                    <div class="result-card">
                        <div class="result-value">$${value}</div>
                        <div class="result-label">${key.replace(/_/g, ' ')}</div>
                    </div>
                `).join('')}
            </div>
           </div>`
        : '';

    // Build the results HTML
    content.innerHTML = `
        <div class="results-header">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <span style="font-size: 2rem;">${agentConfig.icon}</span>
                <div>
                    <h2>${agentName} Agent Results</h2>
                    <p style="margin: 0; opacity: 0.8;">For: ${companyInfo.company_name || 'Your Company'}</p>
                </div>
            </div>
            <span class="status-badge" style="background: var(--success-color); color: white; padding: 0.5rem 1rem; border-radius: 20px;">
                ✓ Complete
            </span>
        </div>

        <div class="results-grid">
            <div class="result-card">
                <div class="result-value">$${resultData.budget_used || 0}</div>
                <div class="result-label">Budget Used</div>
            </div>
            <div class="result-card">
                <div class="result-value">${resultData.deliverables ? resultData.deliverables.length : 0}</div>
                <div class="result-label">Deliverables</div>
            </div>
            <div class="result-card">
                <div class="result-value">${resultData.status || 'Success'}</div>
                <div class="result-label">Status</div>
            </div>
        </div>

        <div class="results-section">
            <h3>📦 Deliverables</h3>
            ${deliverablesHTML}
        </div>

        ${techStackHTML}
        ${timelineHTML}
        ${budgetBreakdownHTML}

        ${resultData.recommendations ? `
            <div class="results-section">
                <h3>💡 Recommendations</h3>
                ${Array.isArray(resultData.recommendations)
                ? `<ul class="deliverables-list">${resultData.recommendations.map(r => `<li>💡 ${r}</li>`).join('')}</ul>`
                : `<p>${resultData.recommendations}</p>`}
            </div>` : ''}

        ${resultData.action_plan_30_60_90 && Object.keys(resultData.action_plan_30_60_90).length > 0 ? `
            <div class="results-section">
                <h3>📅 30 / 60 / 90 Day Execution Plan</h3>
                ${['day_0_to_30', 'day_31_to_60', 'day_61_to_90'].map((key, i) => {
                    const ph = resultData.action_plan_30_60_90[key];
                    if (!ph) return '';
                    const labels = ['Days 1–30', 'Days 31–60', 'Days 61–90'];
                    const colors = ['#f59e0b', '#3b82f6', '#10b981'];
                    return `<div style="margin-bottom:12px;padding:12px;background:rgba(255,255,255,0.04);border-radius:8px;border-left:3px solid ${colors[i]};">
                        <strong style="color:${colors[i]};">${labels[i]} — ${ph.theme || ''}</strong>
                        ${ph.objectives && ph.objectives.length > 0 ? `<ul style="margin:8px 0 0;padding-left:18px;">${ph.objectives.slice(0, 3).map(o => `<li style="font-size:13px;color:#cbd5e1;margin-bottom:3px;">${o}</li>`).join('')}${ph.objectives.length > 3 ? `<li style="font-size:12px;color:#64748b;">+${ph.objectives.length - 3} more...</li>` : ''}</ul>` : ''}
                    </div>`;
                }).join('')}
            </div>` : ''}

        ${resultData.best_practices && resultData.best_practices.length > 0 ? `
            <div class="results-section">
                <h3>⭐ Expert Best Practices</h3>
                <ul class="deliverables-list">
                    ${resultData.best_practices.map(bp => `<li>⭐ ${bp}</li>`).join('')}
                </ul>
            </div>` : ''}

        ${resultData.design_concepts && resultData.design_concepts.length > 0 ? `
            <div class="results-section">
                <h3>🖼️ Design Proposals (${resultData.design_concepts.length})</h3>
                ${resultData.design_concepts.map((c, idx) => `
                    <div style="margin-bottom:10px;padding:12px;background:rgba(37,99,235,0.1);border-radius:8px;border-left:3px solid #2563eb;">
                        <strong>0${idx + 1} — ${c.concept_name}</strong>
                        <p style="margin:4px 0;font-size:13px;opacity:0.8;">${c.description}</p>
                        <small style="opacity:0.6;">📱 ${c.applications} | 💰 ${c.tools_budget}</small>
                    </div>`).join('')}
            </div>` : ''}

        <div style="margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid #34495e; opacity: 0.6; font-size: 0.9rem;">
            <p>Execution Time: ${resultData.timestamp || new Date().toLocaleString()}</p>
        </div>
    `;

    console.log('✅ Results modal content set, displaying modal...');
    modal.style.display = 'block';
    console.log('✅ Modal display set to block. Modal should now be visible.');
}

// Close results modal
function closeResultsModal() {
    document.getElementById('resultsModal').style.display = 'none';
}

// Display agent report in the report display area
function displayAgentReport(agentType, resultData, companyInfo) {
    console.log('📊 [displayAgentReport] Starting report display for:', agentType);
    console.log('📊 [displayAgentReport] Result data:', resultData);
    console.log('📊 [displayAgentReport] Company info:', companyInfo);

    const reportDisplay = document.getElementById('reportDisplay');
    if (!reportDisplay) {
        console.error('❌ [displayAgentReport] Report display element #reportDisplay not found in DOM!');
        alert('Error: Report display area not found. Please refresh the page.');
        return;
    }

    console.log('✅ [displayAgentReport] Found reportDisplay element');

    // Add a flash effect to draw attention
    reportDisplay.style.transition = 'all 0.3s ease';
    reportDisplay.style.transform = 'scale(0.98)';
    reportDisplay.style.opacity = '0.7';

    setTimeout(() => {
        reportDisplay.style.transform = 'scale(1)';
        reportDisplay.style.opacity = '1';
    }, 50);

    // Get agent configuration with proper fallback
    let agentConfig = agentConfigs[agentType];
    if (!agentConfig) {
        console.warn('⚠️ [displayAgentReport] Agent config not found for:', agentType, '- creating fallback');
        const fallbackIcon = getAgentIcon(agentType);
        const agentName = agentType.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        agentConfig = { icon: fallbackIcon, name: agentName };
        agentConfigs[agentType] = agentConfig;
    }

    const agentName = agentConfig.name || agentType.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    const agentIcon = agentConfig.icon || '🤖';

    console.log('✅ [displayAgentReport] Agent name:', agentName, 'Icon:', agentIcon);

    // Safely get company info
    const companyName = (companyInfo && companyInfo.company_name) || (companyInfo && companyInfo.name) || 'Your Company';
    const industry = (companyInfo && companyInfo.industry) || 'N/A';
    const location = (companyInfo && companyInfo.location) || 'N/A';

    console.log('✅ [displayAgentReport] Company info extracted:', { companyName, industry, location });

    // Format deliverables
    const deliverables = Array.isArray(resultData.deliverables) ? resultData.deliverables : [];
    console.log('📦 [displayAgentReport] Processing deliverables:', deliverables);

    const deliverablesHTML = deliverables.length > 0
        ? `<ul class="report-deliverables">
        ${deliverables.map(d => `<li>${typeof d === 'string' ? d : JSON.stringify(d)}</li>`).join('')}
       </ul>`
        : '<p style="opacity: 0.7; color: #94a3b8;">No deliverables available</p>';

    // Format tech stack if available
    const techStack = resultData.tech_stack || [];
    const techStackHTML = techStack.length > 0
        ? `<div class="report-section">
        <h4>🛠️ Technology Stack</h4>
        <div class="report-tech-stack">
            ${techStack.map(tech => `<span class="report-tech-item">${tech}</span>`).join('')}
        </div>
       </div>`
        : '';

    // Format timeline if available
    const timeline = resultData.timeline || [];
    const timelineHTML = timeline.length > 0
        ? `<div class="report-section">
        <h4>📅 Project Timeline</h4>
        ${timeline.map(item => `
            <div class="report-timeline-item">
                <strong>${item.phase || item.week || 'Phase'}</strong>: ${item.description || item.deliverable || item}
            </div>
        `).join('')}
       </div>`
        : '';

    // Format budget breakdown if available
    const budgetBreakdownHTML = resultData.budget_breakdown
        ? `<div class="report-section">
        <h4>💰 Budget Breakdown</h4>
        <div class="report-metrics">
            ${Object.entries(resultData.budget_breakdown).map(([key, value]) => `
                <div class="report-metric">
                    <div class="report-metric-label">${key.replace(/_/g, ' ')}</div>
                    <div class="report-metric-value">$${value}</div>
                </div>
            `).join('')}
        </div>
       </div>`
        : '';

    // Handle recommendations: may be array (branding) or string
    const _recs = resultData.recommendations;
    const recommendationsHTML = _recs
        ? Array.isArray(_recs)
            ? `<ul class="report-deliverables">${_recs.map(r => `<li>${r}</li>`).join('')}</ul>`
            : `<p style="color:#f1f5f9;line-height:1.8;">${_recs}</p>`
        : '';

    // Brand kit reference (branding agent)
    const _brandKit = resultData.brand_kit_reference;
    const brandKitHTML = _brandKit && _brandKit.brand_name
        ? (() => {
            const hexPalette = (_brandKit.color_palette && _brandKit.color_palette.hex) || {};
            const primaryNames = (_brandKit.color_palette && _brandKit.color_palette.primary) || [];
            const supportingNames = (_brandKit.color_palette && _brandKit.color_palette.supporting) || [];
            const allSwatches = [...primaryNames, ...supportingNames];
            const swatchesHTML = allSwatches.map(name => {
                const hex = hexPalette[name] || '#888';
                const isDark = name.toLowerCase().includes('black') || name.toLowerCase().includes('navy') || name.toLowerCase().includes('charcoal');
                return `<div style="display:flex;flex-direction:column;align-items:center;gap:6px;min-width:80px;">
                    <div style="width:72px;height:72px;border-radius:10px;background:${hex};border:2px solid rgba(255,255,255,0.12);box-shadow:0 4px 12px rgba(0,0,0,0.3);"></div>
                    <span style="font-size:11px;color:#e2e8f0;text-align:center;font-weight:600;">${name}</span>
                    <span style="font-size:10px;color:#64748b;font-family:monospace;">${hex}</span>
                </div>`;
            }).join('');

            const typo = _brandKit.typography || {};
            const typoHTML = typo.primary_serif ? `
                <div style="margin-top:16px;padding:14px;background:rgba(255,255,255,0.04);border-radius:8px;">
                    <p style="margin:0 0 10px;font-size:12px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:1px;">Typography System</p>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                        <div style="padding:10px;background:rgba(255,255,255,0.04);border-radius:6px;">
                            <p style="margin:0 0 4px;font-size:13px;font-weight:700;color:#e2e8f0;font-family:Georgia,serif;">${typo.primary_serif.family}</p>
                            <p style="margin:0 0 4px;font-size:11px;color:#94a3b8;">Serif — ${typo.primary_serif.use}</p>
                            <p style="margin:0;font-size:10px;color:#64748b;">${typo.primary_serif.weight}</p>
                        </div>
                        <div style="padding:10px;background:rgba(255,255,255,0.04);border-radius:6px;">
                            <p style="margin:0 0 4px;font-size:13px;font-weight:700;color:#e2e8f0;">${typo.primary_sans.family}</p>
                            <p style="margin:0 0 4px;font-size:11px;color:#94a3b8;">Sans — ${typo.primary_sans.use}</p>
                            <p style="margin:0;font-size:10px;color:#64748b;">${typo.primary_sans.weight}</p>
                        </div>
                    </div>
                    ${typo.scale ? `<p style="margin:8px 0 0;font-size:11px;color:#64748b;">Scale: ${typo.scale}</p>` : ''}
                </div>` : `<p style="margin:8px 0 0;font-size:13px;color:#94a3b8;">${_brandKit.typography_note || ''}</p>`;

            return `<div class="report-section">
                <h4 style="color:#c9a84c;border-bottom:2px solid rgba(201,168,76,0.3);padding-bottom:8px;margin-bottom:16px;">🎨 Brand Identity Kit — ${_brandKit.brand_name}</h4>
                <div style="padding:14px;background:rgba(201,168,76,0.06);border-radius:10px;border:1px solid rgba(201,168,76,0.2);margin-bottom:16px;">
                    <p style="margin:0 0 4px;font-size:12px;color:#94a3b8;"><strong style="color:#c9a84c;">Direction:</strong> ${_brandKit.direction || ''}</p>
                    <p style="margin:0 0 4px;font-size:12px;color:#94a3b8;"><strong style="color:#c9a84c;">Logo Approach:</strong> ${_brandKit.logo_reference || ''}</p>
                    ${_brandKit.legacy_name ? `<p style="margin:0;font-size:12px;color:#94a3b8;"><strong style="color:#c9a84c;">Rebranding From:</strong> ${_brandKit.legacy_name}</p>` : ''}
                </div>
                <p style="margin:0 0 10px;font-size:12px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:1px;">Colour Palette</p>
                <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:8px;">${swatchesHTML}</div>
                ${typoHTML}
            </div>`;
        })()
        : '';

    // Design concept proposals with visual SVG logo previews
    const _concepts = resultData.design_concepts;
    const _logoSVGs = (resultData.brand_kit_reference && resultData.brand_kit_reference.logo_svgs) || {};
    const designConceptsHTML = _concepts && _concepts.length > 0
        ? `<div class="report-section">
            <h4 style="color:#c9a84c;border-bottom:2px solid rgba(201,168,76,0.3);padding-bottom:8px;margin-bottom:16px;">🖼️ Logo Proposals — ${_concepts.length} Directions</h4>
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;">
            ${_concepts.map((c, idx) => {
            const svgContent = _logoSVGs[c.svg_key] || '';
            const swatches = (c.colors || []).map((hex, i) => `<div title="${(c.color_names || [])[i] || hex}" style="width:22px;height:22px;border-radius:4px;background:${hex};border:1.5px solid rgba(255,255,255,0.15);cursor:pointer;"></div>`).join('');
            return `<div style="background:rgba(255,255,255,0.04);border-radius:12px;border:1px solid rgba(201,168,76,0.2);overflow:hidden;">
                    ${svgContent
                    ? `<div style="background:#0f1117;padding:20px;display:flex;justify-content:center;align-items:center;min-height:120px;">${svgContent}</div>`
                    : `<div style="background:#0f1117;padding:20px;display:flex;justify-content:center;align-items:center;min-height:120px;color:#64748b;font-size:12px;">Preview not available</div>`}
                    <div style="padding:14px;">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
                            <p style="margin:0;font-weight:700;font-size:13px;color:#e2e8f0;">0${idx + 1} — ${c.concept_name.replace(/Polished Proposal \d+ — /, '')}</p>
                            ${c.best_for ? `<span style="padding:2px 8px;background:rgba(201,168,76,0.15);border:1px solid rgba(201,168,76,0.4);border-radius:20px;font-size:10px;color:#c9a84c;white-space:nowrap;">${c.best_for}</span>` : ''}
                        </div>
                        <p style="margin:0 0 10px;font-size:12px;color:#94a3b8;line-height:1.5;">${c.description}</p>
                        <div style="display:flex;gap:6px;margin-bottom:10px;">${swatches}</div>
                        <div style="font-size:11px;color:#64748b;display:flex;gap:10px;flex-wrap:wrap;">
                            <span>📱 ${c.applications}</span>
                            <span>💰 ${c.tools_budget}</span>
                        </div>
                        <ul style="margin:8px 0 0;padding-left:16px;font-size:11px;color:#64748b;line-height:1.6;">
                            ${(c.design_principles || []).slice(0, 2).map(p => `<li>${p}</li>`).join('')}
                        </ul>
                    </div>
                </div>`;
        }).join('')}
            </div>
        </div>`
        : '';

    // 30/60/90 day action plan
    const _plan = resultData.action_plan_30_60_90;
    const actionPlanHTML = _plan && Object.keys(_plan).length > 0
        ? (() => {
            const phaseStyles = [
                { key: 'day_0_to_30', label: 'Days 1–30', color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', border: '#f59e0b' },
                { key: 'day_31_to_60', label: 'Days 31–60', color: '#3b82f6', bg: 'rgba(59,130,246,0.08)', border: '#3b82f6' },
                { key: 'day_61_to_90', label: 'Days 61–90', color: '#10b981', bg: 'rgba(16,185,129,0.08)', border: '#10b981' },
            ];
            const phases = phaseStyles.map(ps => {
                const phase = _plan[ps.key];
                if (!phase) return '';
                const objs = (phase.objectives || []).map(o => `<li style="margin-bottom:4px;color:#cbd5e1;">${o}</li>`).join('');
                const delivs = (phase.deliverables || []).map(d => `<li style="margin-bottom:4px;color:#94a3b8;">${d}</li>`).join('');
                const kpis = (phase.kpis || []).map(k => `<span style="display:inline-block;margin:2px 4px 2px 0;padding:2px 8px;background:rgba(255,255,255,0.07);border-radius:20px;font-size:11px;color:#94a3b8;">${k}</span>`).join('');
                const tools = Array.isArray(phase.tools) ? phase.tools.map(t => `<span style="display:inline-block;margin:2px 4px 2px 0;padding:2px 8px;background:rgba(255,255,255,0.05);border-radius:20px;font-size:11px;color:#64748b;">${t}</span>`).join('') : '';
                return `<div style="margin-bottom:16px;padding:16px;background:${ps.bg};border-radius:10px;border-left:4px solid ${ps.border};">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                        <strong style="color:${ps.color};font-size:15px;">${ps.label} — ${phase.theme || ''}</strong>
                        ${phase.priority ? `<span style="padding:2px 10px;background:${ps.border}22;border:1px solid ${ps.border};border-radius:20px;font-size:11px;color:${ps.color};">${phase.priority}</span>` : ''}
                    </div>
                    ${objs ? `<div style="margin-bottom:8px;"><p style="margin:0 0 4px;font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px;">Objectives</p><ul style="margin:0;padding-left:18px;">${objs}</ul></div>` : ''}
                    ${delivs ? `<div style="margin-bottom:8px;"><p style="margin:0 0 4px;font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px;">Deliverables</p><ul style="margin:0;padding-left:18px;">${delivs}</ul></div>` : ''}
                    ${kpis ? `<div style="margin-bottom:6px;"><p style="margin:0 0 4px;font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px;">KPIs</p><div>${kpis}</div></div>` : ''}
                    ${tools ? `<div><p style="margin:0 0 4px;font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px;">Tools</p><div>${tools}</div></div>` : ''}
                    ${phase.budget_allocation ? `<p style="margin:8px 0 0;font-size:12px;color:#64748b;">💰 Budget: ${phase.budget_allocation}</p>` : ''}
                </div>`;
            }).join('');
            return `<div class="report-section">
                <h4 style="color:#f59e0b;border-bottom:2px solid rgba(245,158,11,0.3);padding-bottom:8px;margin-bottom:16px;">📅 30 / 60 / 90 Day Action Plan</h4>
                ${phases}
            </div>`;
        })()
        : '';

    // Expert best practices
    const _bestPractices = resultData.best_practices || (Array.isArray(resultData.recommendations) ? resultData.recommendations : []);
    const bestPracticesHTML = _bestPractices.length > 0
        ? `<div class="report-section">
            <h4 style="color:#a78bfa;border-bottom:2px solid rgba(167,139,250,0.3);padding-bottom:8px;margin-bottom:12px;">⭐ Expert Best Practices</h4>
            <ul style="margin:0;padding-left:0;list-style:none;">
                ${_bestPractices.map((bp, i) => `<li style="display:flex;gap:10px;align-items:flex-start;margin-bottom:10px;padding:10px 12px;background:rgba(167,139,250,0.06);border-radius:8px;border-left:3px solid #7c3aed;">
                    <span style="color:#a78bfa;font-weight:700;min-width:22px;">${String(i + 1).padStart(2, '0')}</span>
                    <span style="color:#e2e8f0;font-size:13px;line-height:1.5;">${bp}</span>
                </li>`).join('')}
            </ul>
           </div>`
        : '';

    // Legal-specific: filings + compliance checklist + risks
    const _filings = resultData.filings_required || [];
    const _compliance = resultData.compliance_checklist || [];
    const _risks = resultData.risks_identified || [];
    const legalFilingsHTML = _filings.length > 0
        ? `<div class="report-section"><h4>📋 Filings Required</h4><ul class="report-deliverables">${_filings.map(f => `<li>📄 ${typeof f === 'object' ? (f.filing || JSON.stringify(f)) : f}</li>`).join('')}</ul></div>`
        : '';
    const legalComplianceHTML = _compliance.length > 0
        ? `<div class="report-section"><h4>✅ Compliance Checklist</h4><ul class="report-deliverables">${_compliance.map(c => `<li>☑️ ${typeof c === 'object' ? (c.item || JSON.stringify(c)) : c}</li>`).join('')}</ul></div>`
        : '';
    const legalRisksHTML = _risks.length > 0
        ? `<div class="report-section"><h4>⚠️ Risks Identified</h4><ul class="report-deliverables">${_risks.map(r => `<li>🔴 ${typeof r === 'object' ? (r.risk || JSON.stringify(r)) : r}</li>`).join('')}</ul></div>`
        : '';

    // AI Tools 2026 (ux_ui / designer agent)
    const _aiTools = resultData.ai_tools_2026;
    const aiToolsHTML = _aiTools && Object.keys(_aiTools).length > 0
        ? `<div class="report-section">
            <h4 style="color:#38bdf8;">🤖 AI Design Tools Stack 2026</h4>
            ${Object.entries(_aiTools).map(([cat, tools]) => `
                <div style="margin-bottom:10px;">
                    <p style="margin:0 0 6px;font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px;">${cat.replace(/_/g, ' ')}</p>
                    <div>${(Array.isArray(tools) ? tools : [tools]).map(t => `<span style="display:inline-block;margin:2px 4px 2px 0;padding:3px 10px;background:rgba(56,189,248,0.08);border:1px solid rgba(56,189,248,0.25);border-radius:20px;font-size:12px;color:#7dd3fc;">${t}</span>`).join('')}</div>
                </div>`).join('')}
          </div>`
        : '';

    // Social media-specific sections
    const _playbook = resultData.community_playbook;
    const communityPlaybookHTML = _playbook
        ? `<div class="report-section"><h4>💬 Community Playbook</h4><p style="color:#f1f5f9;line-height:1.8;">${_playbook}</p></div>`
        : '';
    const _campaigns = resultData.campaign_ideas;
    const campaignIdeasHTML = _campaigns && _campaigns.length > 0
        ? `<div class="report-section"><h4>🎯 Campaign Concepts (${_campaigns.length})</h4>
        ${_campaigns.map(c => `<div style="margin-bottom:8px;padding:10px;background:rgba(37,99,235,0.08);border-radius:6px;">
            <strong style="color:#60a5fa;">${c.campaign}</strong>
            <span style="font-size:12px;color:#64748b;margin-left:8px;">${c.platform}</span>
            <p style="margin:2px 0 0;font-size:12px;color:#94a3b8;">Objective: ${c.objective}</p></div>`).join('')}</div>`
        : '';

    console.log('🎨 [displayAgentReport] Building HTML for report...');

    // Generated artifact files panel
    const _artifacts = resultData.artifacts || [];
    const artifactsHTML = _artifacts.length > 0
        ? `<div class="report-section">
            <h4 style="color:#22d3ee;border-bottom:2px solid rgba(34,211,238,0.3);padding-bottom:8px;margin-bottom:14px;">📎 Generated Artifacts (${_artifacts.length})</h4>
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;">
                ${_artifacts.map(a => {
            const icon = a.type === 'image' ? '🖼️' : a.type === 'markdown' ? '📄' : a.type === 'json' ? '📊' : a.mime_type === 'text/css' ? '🎨' : a.mime_type === 'text/html' ? '🌐' : '📁';
            const href = a.url || ('/static/' + (a.path || ''));
            return `<a href="${href}" target="_blank" rel="noopener" style="display:flex;align-items:center;gap:8px;padding:10px 12px;background:rgba(34,211,238,0.06);border:1px solid rgba(34,211,238,0.2);border-radius:8px;text-decoration:none;color:#e2e8f0;font-size:12px;transition:background .2s;" onmouseover="this.style.background='rgba(34,211,238,0.13)'" onmouseout="this.style.background='rgba(34,211,238,0.06)'">
                        <span style="font-size:18px;flex-shrink:0;">${icon}</span>
                        <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${a.title || a.filename || 'Artifact'}</span>
                    </a>`;
        }).join('')}
            </div>
            ${resultData.artifact_directory ? `<p style="margin:10px 0 0;font-size:11px;color:#64748b;">📁 Output directory: <code style="background:rgba(255,255,255,0.05);padding:2px 6px;border-radius:4px;">${resultData.artifact_directory}</code></p>` : ''}
        </div>`
        : '';

    // Build the full report HTML
    const reportHTML = `
        <div class="report-content">
            <div class="report-header">
                <span style="font-size: 2.5rem;">${agentIcon}</span>
                <h3>${agentName} Agent Report</h3>
                <span class="report-badge">${resultData.execution_mode === 'local_artifacts' ? 'Local artifacts generated · Review required' : 'Report ready'}</span>
            </div>

            <div class="report-section" style="margin-bottom: 24px; padding: 16px; background: rgba(59, 130, 246, 0.08); border-radius: 10px; border-left: 4px solid #3b82f6;">
                <p style="color: #cbd5e1; margin: 0; font-size: 15px;">
                    <strong style="color: #60a5fa;">Company:</strong> ${companyName} |
                    <strong style="color: #60a5fa;">Industry:</strong> ${industry} |
                    <strong style="color: #60a5fa;">Location:</strong> ${location}
                </p>
            </div>

        <div class="report-metrics">
            <div class="report-metric">
                <div class="report-metric-label">${Number.isFinite(resultData.measured_model_cost) ? 'Model Cost (rate-calculated)' : 'Provider Spending'}</div>
                <div class="report-metric-value">${Number.isFinite(resultData.measured_model_cost) ? '$' + resultData.measured_model_cost.toFixed(4) : resultData.spend_verified === true ? '$' + resultData.budget_used : 'Not measured'}</div>
            </div>
            <div class="report-metric">
                <div class="report-metric-label">Deliverables</div>
                <div class="report-metric-value">${deliverables.length}</div>
            </div>
            <div class="report-metric">
                <div class="report-metric-label">Status</div>
                <div class="report-metric-value" style="font-size: 20px; color: #10b981;">${resultData.status || 'Completed'}</div>
            </div>
        </div>

        <div class="report-section">
            <h4>📦 Deliverables</h4>
            ${deliverablesHTML}
        </div>

        ${techStackHTML}
        ${timelineHTML}
        ${budgetBreakdownHTML}
        ${_recs ? `<div class="report-section"><h4>💡 Recommendations</h4>${recommendationsHTML}</div>` : ''}
        ${actionPlanHTML}
        ${bestPracticesHTML}
        ${brandKitHTML}
        ${designConceptsHTML}
        ${aiToolsHTML}
        ${legalFilingsHTML}
        ${legalComplianceHTML}
        ${legalRisksHTML}
        ${communityPlaybookHTML}
        ${campaignIdeasHTML}
        ${artifactsHTML}

        <div style="margin-top: 2.5rem; padding-top: 1.5rem; border-top: 2px solid rgba(59, 130, 246, 0.2); opacity: 0.7; font-size: 0.9rem; color: #94a3b8;">
            <p style="margin: 0;">⏱️ Execution Time: ${resultData.timestamp || new Date().toLocaleString()}</p>
        </div>
    </div>
`;

    // Ensure the Reports tab is visible before writing content
    switchTab('reports', document.querySelector('[data-tab="reports"]'));

    console.log('🎨 [displayAgentReport] Setting innerHTML...');
    reportDisplay.innerHTML = reportHTML;
    console.log('✅ [displayAgentReport] innerHTML set successfully!');

    // Add a glowing border effect temporarily
    reportDisplay.style.border = '3px solid #667eea';
    reportDisplay.style.boxShadow = '0 0 30px rgba(102, 126, 234, 0.6), 0 12px 40px rgba(0, 0, 0, 0.2)';

    setTimeout(() => {
        reportDisplay.style.border = '2px solid rgba(102, 126, 234, 0.5)';
        reportDisplay.style.boxShadow = '0 12px 40px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)';
    }, 2000);

    // Scroll to the report with smooth animation
    console.log('📜 [displayAgentReport] Scrolling to report...');
    setTimeout(() => {
        reportDisplay.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'nearest'
        });
        console.log('✅ [displayAgentReport] Scrolled to report! Report should now be visible.');
    }, 200);

    console.log('🎉 [displayAgentReport] COMPLETE - Report display finished!');
}

// Display analysis report in the execution report area
function displayAnalysisReport(companyInfo, analysisData) {
    console.log('📊 [displayAnalysisReport] CEO executive report render');

    const reportDisplay = document.getElementById('reportDisplay');
    if (!reportDisplay) {
        console.error('❌ [displayAnalysisReport] Report display element not found!');
        return;
    }

    // Flash-in animation
    reportDisplay.style.transition = 'all 0.3s ease';
    reportDisplay.style.transform = 'scale(0.98)';
    reportDisplay.style.opacity = '0.7';
    setTimeout(() => { reportDisplay.style.transform = 'scale(1)'; reportDisplay.style.opacity = '1'; }, 50);

    // ── data helpers ────────────────────────────────────────────────────────
    const cn = analysisData.company_name || companyInfo.company_name || 'Company';
    const ind = analysisData.industry || companyInfo.industry || '';
    const loc = analysisData.location || companyInfo.location || '';
    const budget = analysisData.budget || companyInfo.budget || 0;
    const timeline = analysisData.timeline ?? companyInfo.timeline ?? 'Not provided';
    const tasks = analysisData.tasks || [];
    const risks = analysisData.risks || [];
    const budgetAllocation = analysisData.budget_allocation || {};
    const domainSections = analysisData.domain_sections || {};
    const ceoDirectives = analysisData.ceo_directives || [];
    const opportunities = analysisData.opportunities || [];
    const milestones = analysisData.milestones || [];
    const recommendations = analysisData.recommendations || [];
    const discoveryQuestions = analysisData.discovery_questions || [];
    const totalAllocated = Object.values(budgetAllocation).reduce((s, v) => s + (Number(v) || 0), 0);
    const pe = analysisData.prompt_expert || {};

    // Build domain sections from domainSections map OR group tasks ourselves
    const domainSource = Object.keys(domainSections).length
        ? domainSections
        : (() => {
            const ds = {};
            tasks.forEach(t => {
                const key = (t.required_expertise || t.expertise_required || t.agent_type || 'strategy').toLowerCase().replace(/ /g, '_');
                if (!ds[key]) ds[key] = { icon: '📋', label: key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()), tasks: [], priority_tasks: [], budget: budgetAllocation[key] || 0 };
                ds[key].tasks.push(t);
                if (['CRITICAL', 'HIGH'].includes(String(t.priority || '').toUpperCase()))
                    ds[key].priority_tasks.push(t.task_name || t.description || 'Task');
            });
            return ds;
        })();

    // ── Prompt Expert panel ─────────────────────────────────────────────────
    const peHTML = pe.intent_summary ? (() => {
        const flags = pe.routing_flags || {};
        const activeFlags = Object.entries(flags).filter(([, v]) => v).map(([k]) => k);
        const domains = [pe.primary_domain, ...(pe.secondary_domains || [])].filter(Boolean);
        return `<div style="margin-bottom:18px;padding:16px;
            background:rgba(139,92,246,.08);
            border-radius:10px;border:1px solid rgba(139,92,246,.25);border-left:4px solid #8b5cf6;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
                <span>🧠</span>
                <strong style="color:#a78bfa;font-size:.82rem;letter-spacing:.06em;text-transform:uppercase;">Research &amp; Prompt Agent ─ Intake</strong>
                ${pe.confidence_score ? `<span style="margin-left:auto;background:rgba(139,92,246,.2);color:#c4b5fd;padding:2px 8px;border-radius:999px;font-size:.72rem;font-weight:700;">${Math.round(pe.confidence_score * 100)}% confidence</span>` : ''}
            </div>
            <p style="margin:0 0 6px;color:#f1f5f9;font-size:.88rem;"><strong>Intent:</strong> ${pe.intent_summary}</p>
            ${domains.length ? `<p style="margin:0 0 4px;color:#cbd5e1;font-size:.8rem;"><strong>Domains:</strong> ${domains.join(' → ')}</p>` : ''}
            ${activeFlags.length ? `<p style="margin:0 0 4px;color:#cbd5e1;font-size:.8rem;"><strong>Routing:</strong> ${activeFlags.map(f => `<span style="background:rgba(139,92,246,.2);color:#ddd6fe;padding:1px 6px;border-radius:4px;margin-right:4px;">${f}</span>`).join('')}</p>` : ''}
            ${pe.ambiguities && pe.ambiguities.length ? `<p style="margin:4px 0 0;color:#fbbf24;font-size:.78rem;">⚠️ ${pe.ambiguities.join(' • ')}</p>` : ''}
        </div>`;
    })() : '';

    // ── CEO hierarchy chain ─────────────────────────────────────────────────
    const chainAgents = Object.keys(domainSource).slice(0, 6);
    const chainHTML = `
        <div style="margin-bottom:18px;padding:16px;background:rgba(30,41,59,.45);border-radius:10px;border:1px solid rgba(148,163,184,.16);">
            <div style="font-size:.78rem;font-weight:700;color:#60a5fa;text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px;">⬡ Orchestration Hierarchy</div>
            <div style="display:flex;align-items:center;flex-wrap:wrap;gap:6px;">
                <div style="background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;padding:6px 14px;border-radius:999px;font-weight:700;font-size:.82rem;box-shadow:0 2px 8px rgba(37,99,235,.35);">👔 CEO</div>
                <span style="color:#94a3b8;font-size:1.1rem;">→</span>
                ${chainAgents.map(k => {
        const s = domainSource[k];
        return `<div style="background:rgba(30,41,59,.75);color:#e2e8f0;padding:5px 12px;border-radius:999px;font-size:.78rem;font-weight:600;border:1px solid rgba(148,163,184,.22);">${s.icon || '📋'} ${s.label || k}</div>`;
    }).join('<span style="color:#64748b;">·</span>')}
                ${chainAgents.length < Object.keys(domainSource).length ? `<span style="color:#94a3b8;font-size:.78rem;">+${Object.keys(domainSource).length - chainAgents.length} more</span>` : ''}
            </div>
        </div>`;

    // ── CEO directives ──────────────────────────────────────────────────────
    const directivesHTML = ceoDirectives.length ? `
        <div style="margin-bottom:18px;padding:16px;background:rgba(37,99,235,.08);border-radius:10px;border:1px solid rgba(37,99,235,.2);border-left:4px solid #3b82f6;">
            <div style="font-weight:700;color:#60a5fa;margin-bottom:10px;font-size:.9rem;">📌 CEO Executive Directives</div>
            <ol style="margin:0;padding-left:20px;">
                ${ceoDirectives.map(d => `<li style="color:#f1f5f9;font-size:.88rem;padding:3px 0;line-height:1.5;">${d}</li>`).join('')}
            </ol>
        </div>` : '';

    // ── CEO Strategic Recommendations ────────────────────────────────────────
    const recsHTML = recommendations.length ? `
        <div style="margin-bottom:18px;padding:16px;background:rgba(16,185,129,.08);border-radius:10px;border:1px solid rgba(16,185,129,.2);border-left:4px solid #10b981;">
            <div style="font-weight:700;color:#34d399;margin-bottom:10px;font-size:.9rem;">💡 CEO Strategic Recommendations</div>
            <ol style="margin:0;padding-left:18px;">
                ${recommendations.map(r => `<li style="font-size:.86rem;color:#f1f5f9;padding:4px 0;line-height:1.5;">${r}</li>`).join('')}
            </ol>
        </div>` : '';

    // ── CEO Discovery Questions ───────────────────────────────────────────────
    const questionsHTML = discoveryQuestions.length ? `
        <div style="margin-bottom:18px;padding:16px;background:rgba(245,158,11,.08);border-radius:10px;border:1px solid rgba(245,158,11,.2);border-left:4px solid #f59e0b;">
            <div style="font-weight:700;color:#fbbf24;margin-bottom:8px;font-size:.9rem;">❓ CEO Discovery Questions</div>
            <p style="font-size:.8rem;color:#cbd5e1;margin:0 0 10px;">Answering these in chat will help the CEO refine your execution plan:</p>
            <div style="display:flex;flex-direction:column;gap:8px;">
                ${discoveryQuestions.map(q => `
                    <div style="padding:10px 14px;background:rgba(15,23,42,.65);border-radius:8px;border:1px solid rgba(245,158,11,.25);">
                        <span style="font-size:.7rem;font-weight:700;color:#fbbf24;text-transform:uppercase;letter-spacing:.05em;">${q.icon || ''} ${q.category || ''}</span>
                        <p style="margin:4px 0 0;font-size:.84rem;color:#f1f5f9;line-height:1.5;">${q.question}</p>
                    </div>`).join('')}
            </div>
        </div>` : '';

    // ── Domain sections ─────────────────────────────────────────────────────
    const domainColors = {
        branding: '#f59e0b', web_development: '#3b82f6', legal: '#10b981',
        martech: '#8b5cf6', content: '#06b6d4', campaigns: '#ef4444',
        social_media: '#ec4899', security: '#f97316', strategy: '#3b82f6'
    };
    const domainsHTML = Object.entries(domainSource).length ? `
        <div style="margin-bottom:18px;">
            <div style="font-weight:700;color:#f8fafc;margin-bottom:12px;font-size:.9rem;">🗂️ Domain Execution Plans</div>
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;">
                ${Object.entries(domainSource).map(([key, sec]) => {
        const color = domainColors[key] || '#3b82f6';
        const taskList = (sec.tasks || []).slice(0, 3);
        const budget_d = sec.budget || budgetAllocation[key] || 0;
        return `<div style="padding:14px;background:rgba(24,34,52,.75);border-radius:10px;border:1px solid rgba(148,163,184,.16);border-top:3px solid ${color};">
                        <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
                            <span style="font-size:1.2rem;">${sec.icon || '📋'}</span>
                            <strong style="color:#f8fafc;font-size:.88rem;">${sec.label || key}</strong>
                            ${budget_d ? `<span style="margin-left:auto;background:rgba(16,185,129,.16);color:#34d399;padding:2px 7px;border-radius:999px;font-size:.72rem;font-weight:700;">$${Number(budget_d).toLocaleString()}</span>` : ''}
                        </div>
                        ${taskList.length ? `<ul style="list-style:none;padding:0;margin:0;">${taskList.map(t => `<li style="font-size:.78rem;color:#cbd5e1;padding:2px 0;">• ${t.task_name || t.description || ''}</li>`).join('')}</ul>` : ''}
                        ${(sec.tasks || []).length > 3 ? `<p style="margin:4px 0 0;font-size:.72rem;color:#94a3b8;">+${sec.tasks.length - 3} more tasks</p>` : ''}
                        ${sec.priority_tasks && sec.priority_tasks.length ? `<p style="margin:6px 0 0;font-size:.72rem;color:${color};font-weight:600;">🔥 Priority: ${sec.priority_tasks[0]}</p>` : ''}
                    </div>`;
    }).join('')}
            </div>
        </div>` : '';

    // ── Risks ────────────────────────────────────────────────────────────────
    const risksHTML = risks.length ? `
        <div style="margin-bottom:18px;padding:14px 18px;background:rgba(239,68,68,.08);border-radius:10px;border:1px solid rgba(239,68,68,.2);border-left:4px solid #ef4444;">
            <div style="font-weight:700;color:#f87171;margin-bottom:8px;font-size:.88rem;">⚠️ Identified Risks</div>
            <ul style="list-style:none;padding:0;margin:0;">
                ${risks.slice(0, 5).map(r => `<li style="font-size:.82rem;color:#fca5a5;padding:3px 0;line-height:1.5;">• ${typeof r === 'object' ? (r.description || r.risk || JSON.stringify(r)) : r}</li>`).join('')}
                ${risks.length > 5 ? `<li style="font-size:.78rem;color:#94a3b8;font-style:italic;">+${risks.length - 5} more risks identified</li>` : ''}
            </ul>
        </div>` : '';

    // ── Milestones ───────────────────────────────────────────────────────────
    const milestonesHTML = milestones.length ? `
        <div style="margin-bottom:18px;padding:14px 18px;background:rgba(16,185,129,.08);border-radius:10px;border:1px solid rgba(16,185,129,.2);border-left:4px solid #10b981;">
            <div style="font-weight:700;color:#34d399;margin-bottom:8px;font-size:.88rem;">🏁 Milestones</div>
            <ul style="list-style:none;padding:0;margin:0;">
                ${milestones.slice(0, 5).map(m => {
        const label = typeof m === 'object' ? (m.name || m.milestone || m.description || JSON.stringify(m)) : m;
        const day = typeof m === 'object' ? m.day : '';
        return `<li style="font-size:.84rem;color:#f1f5f9;padding:3px 0;line-height:1.5;">${day ? `<strong style="color:#6ee7b7;">Day ${day}:</strong> ` : ''} ${label}</li>`;
    }).join('')}
            </ul>
        </div>` : '';

    // ── Opportunities ────────────────────────────────────────────────────────
    const oppsHTML = opportunities.length ? `
        <div style="margin-bottom:18px;padding:14px 18px;background:rgba(59,130,246,.08);border-radius:10px;border:1px solid rgba(59,130,246,.2);border-left:4px solid #3b82f6;">
            <div style="font-weight:700;color:#60a5fa;margin-bottom:8px;font-size:.88rem;">💡 Opportunities</div>
            <ul style="list-style:none;padding:0;margin:0;">
                ${opportunities.slice(0, 4).map(o => `<li style="font-size:.84rem;color:#f1f5f9;padding:3px 0;line-height:1.5;">• ${typeof o === 'object' ? (o.description || o.opportunity || JSON.stringify(o)) : o}</li>`).join('')}
            </ul>
        </div>` : '';

    // ── Full report HTML ─────────────────────────────────────────────────────
    const reportHTML = `
        <div class="report-content">
            <!-- CEO Header -->
            <div class="report-header" style="background:rgba(30,41,59,.55);border:1px solid rgba(148,163,184,.16);border-radius:12px;padding:20px;margin-bottom:18px;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <span style="font-size:2.5rem;">👔</span>
                    <div>
                        <h3 style="margin:0;color:#f8fafc;font-size:1.25rem;font-weight:700;">CEO Executive Strategic Report</h3>
                        <p style="margin:4px 0 0;color:#cbd5e1;font-size:.85rem;">${cn} · ${ind} · ${loc}</p>
                    </div>
                    <span class="report-badge" style="margin-left:auto;background:rgba(16,185,129,.16);color:#34d399;border:1px solid rgba(16,185,129,.3);">✓ Multidisciplinary Analysis Complete</span>
                </div>
            </div>

            <!-- KPI metrics -->
            <div class="report-metrics" style="margin-bottom:18px;">
                <div class="report-metric"><div class="report-metric-label">Tasks Identified</div><div class="report-metric-value">${tasks.length}</div></div>
                <div class="report-metric"><div class="report-metric-label">Exec Domains</div><div class="report-metric-value">${Object.keys(domainSource).length}</div></div>
                <div class="report-metric"><div class="report-metric-label">Total Budget</div><div class="report-metric-value" style="font-size:17px;">$${Number(budget).toLocaleString()}</div></div>
                <div class="report-metric"><div class="report-metric-label">Allocated</div><div class="report-metric-value" style="font-size:17px;color:#10b981;">$${totalAllocated.toLocaleString()}</div></div>
                <div class="report-metric"><div class="report-metric-label">Timeline</div><div class="report-metric-value" style="font-size:17px;color:#f59e0b;">${timeline}d</div></div>
                <div class="report-metric"><div class="report-metric-label">Risks Flagged</div><div class="report-metric-value" style="color:#ef4444;">${risks.length}</div></div>
            </div>

            ${peHTML}
            ${chainHTML}
            ${directivesHTML}
            ${recsHTML}
            ${questionsHTML}
            ${domainsHTML}
            ${risksHTML}
            ${milestonesHTML}
            ${oppsHTML}

            <!-- Artifacts panel -->
            ${(() => {
            const _ceoArts = analysisData.artifacts || [];
            if (!_ceoArts.length) return '';
            return `<div style="margin-bottom:18px;padding:14px 18px;background:rgba(6,182,212,.08);border-radius:10px;border:1px solid rgba(6,182,212,.2);border-left:4px solid #06b6d4;">
                    <div style="font-weight:700;color:#22d3ee;margin-bottom:10px;font-size:.88rem;">📎 Generated CEO Artifacts (${_ceoArts.length})</div>
                    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;">
                        ${_ceoArts.map(a => {
                const icon = a.type === 'image' ? '🖼️' : a.type === 'markdown' ? '📄' : a.type === 'json' ? '📊' : '📁';
                const href = a.url || ('/static/' + (a.path || ''));
                return `<a href="${href}" target="_blank" rel="noopener" style="display:flex;align-items:center;gap:8px;padding:8px 12px;background:rgba(6,182,212,0.12);border:1px solid rgba(6,182,212,0.25);border-radius:7px;text-decoration:none;color:#e2e8f0;font-size:.78rem;">
                                <span>${icon}</span><span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${a.title || a.filename || 'File'}</span>
                            </a>`;
            }).join('')}
                    </div>
                    ${analysisData.artifact_directory ? `<p style="margin:8px 0 0;font-size:.7rem;color:#94a3b8;">📁 ${analysisData.artifact_directory}</p>` : ''}
                </div>`;
        })()}

            <!-- Next Steps -->
            <div style="padding:14px 18px;background:rgba(37,99,235,.08);border-radius:10px;border:1px solid rgba(37,99,235,.2);border-left:4px solid #3b82f6;">
                <div style="font-weight:700;color:#60a5fa;margin-bottom:6px;font-size:.88rem;">👉 Next Steps</div>
                <p style="color:#f1f5f9;line-height:1.7;font-size:.88rem;margin:0;">
                    Review domain plans above and execute individual agents from <strong>Available AI Agents</strong>,
                    or click <strong>Launch Graph Execution</strong> to generate local planning artifacts for the selected domains. No external actions are performed.
                </p>
            </div>

            <div style="margin-top:20px;padding-top:12px;border-top:1px solid rgba(148,163,184,.2);font-size:.78rem;color:#94a3b8;">
                ⏱️ Generated: ${new Date().toLocaleString()}
            </div>
        </div>
    `;

    switchTab('reports', document.querySelector('[data-tab="reports"]'));
    console.log('🎨 [displayAnalysisReport] rendering CEO executive report...');
    reportDisplay.innerHTML = reportHTML;

    // Brief highlight effect
    reportDisplay.style.border = '2px solid rgba(59,130,246,0.6)';
    reportDisplay.style.boxShadow = '0 0 20px rgba(59,130,246,0.25), 0 12px 40px rgba(0,0,0,0.2)';
    setTimeout(() => {
        reportDisplay.style.border = '1px solid rgba(148,163,184,0.18)';
        reportDisplay.style.boxShadow = '0 12px 40px rgba(0,0,0,0.15)';
    }, 1800);
    setTimeout(() => {
        reportDisplay.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 150);

    console.log('🎉 [displayAnalysisReport] COMPLETE!');
}

// Display orchestration report - shows comprehensive results after full orchestration
function displayOrchestrationReport(companyInfo, reportData) {
    console.log('🎉 [displayOrchestrationReport] Starting orchestration report display');
    console.log('📊 Report data:', reportData);

    const reportDisplay = document.getElementById('reportDisplay');
    if (!reportDisplay) {
        console.error('❌ [displayOrchestrationReport] Report display element not found!');
        return;
    }

    // Add flash effect
    reportDisplay.style.transition = 'all 0.3s ease';
    reportDisplay.style.transform = 'scale(0.98)';
    reportDisplay.style.opacity = '0.7';

    setTimeout(() => {
        reportDisplay.style.transform = 'scale(1)';
        reportDisplay.style.opacity = '1';
    }, 50);

    const tasks = reportData.tasks || [];
    const budgetAllocation = reportData.budget_allocation || {};
    const totalAllocated = Object.values(budgetAllocation).reduce((sum, val) => sum + val, 0);
    const risks = reportData.risks || [];
    const opportunities = reportData.opportunities || [];
    const deliverables = reportData.deliverables || [];
    const agentOutputs = reportData.agent_outputs || [];
    const completedTasks = reportData.completed_tasks || 0;
    const totalTasks = reportData.total_tasks || tasks.length;
    const timeline = reportData.timeline ?? 'Not provided';
    const budgetUsed = reportData.budget_used || totalAllocated;
    const totalBudget = reportData.total_budget || (budgetUsed + (reportData.budget_remaining || 0));
    const budgetRemaining = reportData.budget_remaining || Math.max(0, totalBudget - budgetUsed);

    // Build agent outputs section
    const agentOutputsHTML = agentOutputs.length > 0
        ? `<div class="report-section">
            <h4>🤖 Agent Execution Results</h4>
            ${agentOutputs.map(output => `
                <div class="report-timeline-item" style="margin-bottom: 12px;">
                    <strong style="color: #667eea;">${output.agent_name || output.agent || 'Agent'}:</strong>
                    <p style="margin: 8px 0 0 0; color: #cbd5e1; line-height: 1.6;">
                        ${typeof output.summary === 'string'
                ? output.summary
                : (output.summary?.key_findings?.join(' • ') || output.result?.status || 'Executed successfully')}
                    </p>
                </div>
            `).join('')}
        </div>`
        : '';

    // Build deliverables section
    const deliverablesHTML = deliverables.length > 0
        ? `<div class="report-section">
            <h4>📦 All Deliverables</h4>
            <ul class="report-deliverables">
                ${deliverables.map(d => `<li>${d}</li>`).join('')}
            </ul>
        </div>`
        : '';

    // Build opportunities section
    const opportunitiesHTML = opportunities.length > 0
        ? `<div class="report-section">
            <h4>✨ Identified Opportunities</h4>
            <ul class="report-deliverables" style="list-style: none; padding-left: 0;">
                ${opportunities.map(opp => `
                    <li style="padding: 12px; margin-bottom: 8px; background: rgba(34, 197, 94, 0.1); border-left: 3px solid #22c55e; border-radius: 6px;">
                        ${opp.description || opp}
                    </li>
                `).join('')}
            </ul>
        </div>`
        : '';

    // Build risks section
    const risksHTML = risks.length > 0
        ? `<div class="report-section">
            <h4>⚠️ Risk Assessment</h4>
            <ul class="report-deliverables" style="list-style: none; padding-left: 0;">
                ${risks.map(risk => `
                    <li style="padding: 12px; margin-bottom: 8px; background: rgba(239, 68, 68, 0.1); border-left: 3px solid #ef4444; border-radius: 6px;">
                        <strong style="color: #f87171;">${risk.category || 'Risk'}:</strong> ${risk.description || risk}
                        ${risk.mitigation ? `<br><span style="color: #10b981; font-size: 0.9em;">→ Mitigation: ${risk.mitigation}</span>` : ''}
                    </li>
                `).join('')}
            </ul>
        </div>`
        : '';

    // Build budget breakdown
    const budgetHTML = Object.keys(budgetAllocation).length > 0
        ? `<div class="report-section">
            <h4>💰 Budget Allocation by Domain</h4>
            <div class="report-metrics">
                ${Object.entries(budgetAllocation).map(([domain, amount]) => `
                    <div class="report-metric">
                        <div class="report-metric-label">${domain}</div>
                        <div class="report-metric-value">$${amount}</div>
                    </div>
                `).join('')}
            </div>
        </div>`
        : '';

    // Build task summary
    const tasksSummaryHTML = `<div class="report-section">
        <h4>📋 Task Execution Summary</h4>
        <div class="report-metrics">
            <div class="report-metric">
                <div class="report-metric-label">Total Tasks</div>
                <div class="report-metric-value">${totalTasks}</div>
            </div>
            <div class="report-metric">
                <div class="report-metric-label">Completed</div>
                <div class="report-metric-value" style="color: #10b981;">${completedTasks}</div>
            </div>
            <div class="report-metric">
                <div class="report-metric-label">Success Rate</div>
                <div class="report-metric-value">${totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0}%</div>
            </div>
        </div>
    </div>`;

    const reportHTML = `
        <div class="report-content">
            <div class="report-header">
                <span style="font-size: 2.5rem;">🎯</span>
                <h3>Full Orchestration Complete</h3>
                <span class="report-badge">✓ Success</span>
            </div>

            <div class="report-section" style="margin-bottom: 24px; padding: 16px; background: rgba(16, 185, 129, 0.12); border-radius: 10px; border-left: 4px solid #10b981;">
                <p style="color: #f1f5f9; margin: 0; font-size: 15px;">
                    <strong style="color: #667eea;">Company:</strong> ${companyInfo.company_name} |
                    <strong style="color: #667eea;">Industry:</strong> ${companyInfo.industry} |
                    <strong style="color: #667eea;">Location:</strong> ${companyInfo.location}
                </p>
            </div>

            <div class="report-metrics">
                <div class="report-metric">
                    <div class="report-metric-label">Total Budget</div>
                    <div class="report-metric-value">$${totalBudget}</div>
                </div>
                <div class="report-metric">
                    <div class="report-metric-label">Budget Used</div>
                    <div class="report-metric-value">$${budgetUsed}</div>
                </div>
                <div class="report-metric">
                    <div class="report-metric-label">Budget Remaining</div>
                    <div class="report-metric-value">$${budgetRemaining}</div>
                </div>
                <div class="report-metric">
                    <div class="report-metric-label">Domains</div>
                    <div class="report-metric-value">${Object.keys(budgetAllocation).length}</div>
                </div>
                <div class="report-metric">
                    <div class="report-metric-label">Agents Deployed</div>
                    <div class="report-metric-value">${agentOutputs.length || Object.keys(budgetAllocation).length}</div>
                </div>
                <div class="report-metric">
                    <div class="report-metric-label">Timeline</div>
                    <div class="report-metric-value" style="font-size: 20px; color: #10b981;">${timeline} days</div>
                </div>
            </div>

            ${tasksSummaryHTML}
            ${budgetHTML}
            ${agentOutputsHTML}
            ${deliverablesHTML}
            ${opportunitiesHTML}
            ${risksHTML}

    <div class="report-section">
        <h4>👉 Next Steps</h4>
        <p style="color: #f1f5f9; line-height: 1.8; font-size: 15px;">
            ✅ All agents have been successfully deployed and executed.<br>
                ✅ Review the detailed reports in the <strong>Task Decomposition</strong> section below.<br>
                    ✅ You can now execute individual agents again or proceed with implementation.<br>
                        💡 Consider the <strong>risks</strong> and <strong>opportunities</strong> identified above in your planning.
                    </p>
                </div>

                <div style="margin-top: 2.5rem; padding-top: 1.5rem; border-top: 2px solid rgba(16, 185, 129, 0.2); opacity: 0.7; font-size: 0.9rem; color: #64748b;">
                    <p style="margin: 0;">⏱️ Orchestration Time: ${new Date().toLocaleString()}</p>
                </div>
            </div>
    `;

    // Ensure the Reports tab is visible before writing content
    switchTab('reports', document.querySelector('[data-tab="reports"]'));

    console.log('🎨 [displayOrchestrationReport] Setting innerHTML...');
    reportDisplay.innerHTML = reportHTML;
    console.log('✅ [displayOrchestrationReport] innerHTML set successfully!');

    // Add glowing border effect
    reportDisplay.style.border = '3px solid #10b981';
    reportDisplay.style.boxShadow = '0 0 30px rgba(16, 185, 129, 0.6), 0 12px 40px rgba(0, 0, 0, 0.2)';

    setTimeout(() => {
        reportDisplay.style.border = '2px solid rgba(16, 185, 129, 0.5)';
        reportDisplay.style.boxShadow = '0 12px 40px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)';
    }, 2000);

    // Scroll to report with smooth animation
    setTimeout(() => {
        reportDisplay.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'nearest'
        });
    }, 200);

    console.log('🎉 [displayOrchestrationReport] COMPLETE - Orchestration report displayed!');
}

// Close modal when clicking outside of it
window.onclick = function (event) {
    const modal = document.getElementById('agentModal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
    const resultsModal = document.getElementById('resultsModal');
    if (event.target == resultsModal) {
        resultsModal.style.display = 'none';
    }
}

// Display tasks
function displayTasks(tasks) {
    const container = document.getElementById('tasksContainer');
    container.innerHTML = '';

    tasks.forEach(task => {
        const card = document.createElement('div');
        card.className = 'task-card';

        const priorityClass = task.priority ? task.priority.toLowerCase() : 'medium';

        card.innerHTML = `
            <div class="task-header">
                <div>
                    <span class="task-id">${task.task_id || 'Task'}</span>
                    <div>${task.description || task.task_description || 'No description'}</div>
                </div>
                <span class="task-priority ${priorityClass}">${task.priority || 'MEDIUM'}</span>
            </div>
            <div class="task-details">
                <div class="task-detail-item">
                    <strong>EXPERTISE</strong>
                    ${task.expertise_required || 'General'}
                </div>
                <div class="task-detail-item">
                    <strong>BUDGET</strong>
                    $${task.budget || 0}
                </div>
                <div class="task-detail-item">
                    <strong>TIMELINE</strong>
                    ${task.timeline_days || task.timeline || 0} days
                </div>
                <div class="task-detail-item">
                    <strong>STATUS</strong>
                    ${task.status || 'Pending'}
                </div>
            </div>
            `;

        container.appendChild(card);
    });

    state.tasks = tasks;
}

// Update status display
function updateStatus(message, type = 'idle') {
    const display = document.getElementById('statusDisplay');
    display.innerHTML = `<p class="status-${type}">${message}</p>`;
    state.executionStatus = type;
}

// Update budget display
function updateBudgetDisplay(allocation) {
    const total = Object.values(allocation).reduce((sum, val) => sum + val, 0);
    const remaining = state.budget.total - total;

    document.getElementById('remainingBudget').textContent = `$${remaining.toFixed(0)}`;

    if (remaining < 1000) {
        document.getElementById('remainingBudget').className = 'value danger';
    } else if (remaining < 2000) {
        document.getElementById('remainingBudget').className = 'value warning';
    } else {
        document.getElementById('remainingBudget').className = 'value success';
    }

    state.budget.remaining = remaining;
    state.budget.allocated = allocation;
}

// Add log entry
function addLogEntry(message, type = 'info') {
    const log = document.getElementById('executionLog');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;

    const timestamp = new Date().toLocaleTimeString();
    entry.innerHTML = `
            <span class="timestamp">[${timestamp}]</span>
            <span class="message">${message}</span>
            `;

    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;
}

// Highlight agent
function highlightAgent(agentType, status) {
    const agentCard = document.getElementById(`agent-${agentType}`);
    if (!agentCard) return;

    agentCard.classList.remove('pulsing');

    if (status === 'deploying' || status === 'executing') {
        agentCard.classList.add('pulsing');
    } else if (status === 'active' || status === 'complete') {
        agentCard.style.boxShadow = '0 0 20px rgba(16, 185, 129, 0.6)';
        setTimeout(() => {
            agentCard.style.boxShadow = '';
        }, 3000);
    }
}

// Progress bar functions
function showProgressBar() {
    document.getElementById('progressBar').style.display = 'block';
    updateProgress(0);
}

function hideProgressBar() {
    document.getElementById('progressBar').style.display = 'none';
}

function updateProgress(percent) {
    document.getElementById('progressFill').style.width = `${percent}%`;
    document.getElementById('progressText').textContent = `${percent}%`;
}

// Close modal when clicking outside
window.onclick = function (event) {
    const modal = document.getElementById('agentModal');
    if (event.target === modal) {
        closeModal();
    }
}

// ============================================================================
// INTERACTIVE CHAT INTERFACE
// ============================================================================

let chatMessages = [];
let chatMinimized = false;

// Initialize chat interface
function initializeChat() {
    console.log('🔧 Initializing chat interface...');

    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendChat');
    const clearButton = document.getElementById('clearChat');
    const toggleButton = document.getElementById('toggleChat');

    if (!chatInput || !sendButton) {
        console.error('❌ Chat elements not found');
        return;
    }

    // Send message on button click
    sendButton.addEventListener('click', () => sendChatMessage());

    // Send message on Enter key
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });

    // Clear chat
    clearButton?.addEventListener('click', () => clearChat());

    // Toggle chat minimize
    toggleButton?.addEventListener('click', () => toggleChatMinimize());

    console.log('✅ Chat interface initialized');
}

// Send chat message — routed through LLM socket with per-agent identity + debate mode
async function sendChatMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();

    if (!message) return;

    addChatMessage(message, 'user');
    chatInput.value = '';
    setChatStatus('typing');

    // Build a minimal, safe scenario payload for context
    const scenario = persistScenarioToStorage({ syncBackend: false });
    const scenarioCtx = {
        company_name: scenario.company_name || '',
        industry: scenario.industry || '',
        location: scenario.location || '',
        budget: scenario.budget || 0,
        timeline: scenario.timeline || 0,
        objectives: Array.isArray(scenario.objectives) ? scenario.objectives.slice(0, 10) : [],
    };

    // ── Primary path: SocketIO LLM chat ──────────────────────────────────
    if (socket && socket.connected) {
        socket.emit('ai_chat_request', {
            message,
            agent: _v4ActiveAgent || 'ceo',
            debate_mode: _v4DebateMode,
            scenario: scenarioCtx,
        });
        // ai_chat_response socket listener clears status + renders reply
        return;
    }

    // ── Fallback: REST endpoint when socket is unavailable ───────────────
    try {
        const res = await fetch('/api/chat/message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message,
                agent: _v4ActiveAgent || 'ceo',
                debate_mode: _v4DebateMode,
                scenario: scenarioCtx,
            }),
        });
        const data = await res.json();
        setChatStatus('');
        if (!res.ok || data.error) throw new Error(data.error || `Chat failed (${res.status})`);
        addChatMessage(data.response, 'assistant');
    } catch (error) {
        setChatStatus('');
        addChatMessage(`Connection error: ${error.message}`, 'error');
    }
}

// Process chat commands
async function processChatCommand(message) {
    const lowerMessage = message.toLowerCase();

    // Check for agent execution commands
    const agentTypes = ['branding', 'web_development', 'legal', 'martech', 'content', 'campaigns'];

    for (const agentType of agentTypes) {
        if (lowerMessage.includes(agentType.replace('_', ' ')) || lowerMessage.includes(agentType)) {
            if (lowerMessage.includes('execute') || lowerMessage.includes('run') || lowerMessage.includes('start')) {
                // Execute the agent
                addChatMessage(`Executing ${agentType.replace('_', ' ')} agent...`, 'system');
                setTimeout(() => executeAgent(agentType), 500);
                return `Initiating ${agentType.replace('_', ' ')} agent execution. Check the execution log for progress.`;
            }
            if (lowerMessage.includes('details') || lowerMessage.includes('info') || lowerMessage.includes('view')) {
                setTimeout(() => viewAgentDetails(agentType), 500);
                return `Opening ${agentType.replace('_', ' ')} agent details...`;
            }
        }
    }

    // Status inquiry
    if (lowerMessage.includes('status') || lowerMessage.includes('progress')) {
        const executing = document.querySelectorAll('.agent-card.executing').length;
        const complete = document.querySelectorAll('.agent-card.complete').length;
        return `System Status:\n✓ ${complete} agents completed\n⚙️ ${executing} agents executing\n🤖 ${agentTypes.length} agents available`;
    }

    // Orchestration commands
    if (lowerMessage.includes('orchestration') || lowerMessage.includes('launch all')) {
        setTimeout(() => runFullOrchestration(), 500);
        return 'Launching full CFO orchestration...';
    }

    // Analysis commands
    if (lowerMessage.includes('analyze') || lowerMessage.includes('analysis')) {
        setTimeout(() => analyzeObjectives(), 500);
        return 'Starting strategic analysis...';
    }

    // Help command
    if (lowerMessage.includes('help') || lowerMessage.includes('commands')) {
        return `Available Commands:
            • "Execute [agent name]" - Run a specific agent
            • "Show status" - View system status
            • "Launch orchestration" - Run all agents
            • "Analyze objectives" - Strategic analysis
            • "Clear chat" - Clear chat history
            • "Agent details [name]" - View agent info

            Available Agents:
            🎨 Branding • 💻 Web Development • ⚖️ Legal
            📊 MarTech • ✍️ Content • 📢 Campaigns`;
    }

    // Budget info
    if (lowerMessage.includes('budget')) {
        const totalBudget = document.getElementById('totalBudget')?.textContent || '$5,000';
        const remaining = document.getElementById('remainingBudget')?.textContent || '$5,000';
        return `Budget Information:\n💰 Total Budget: ${totalBudget}\n💵 Remaining: ${remaining}`;
    }

    // Default response
    return `I can help you with:
            • Executing AI agents
            • Viewing agent status
            • Running orchestration
            • Managing budgets

            Type "help" for available commands or ask me anything!`;
}

// Add message to chat
function addChatMessage(text, type = 'assistant') {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    messageDiv.innerHTML = `
            <div class="chat-message-content">${formatChatMessage(text, type)}</div>
            <div class="chat-message-time">${timeStr}</div>
            `;

    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Store message
    chatMessages.push({ text, type, timestamp: now });

    // Limit message history
    if (chatMessages.length > 100) {
        chatMessages.shift();
        if (messagesContainer.children.length > 100) {
            messagesContainer.removeChild(messagesContainer.firstChild);
        }
    }
}

// Escape HTML to prevent XSS attacks
function escapeHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Format chat message (preserve line breaks, add styling)
function formatChatMessage(text, type) {
    // ✅ SECURITY: Escape HTML first to prevent XSS
    let escaped = escapeHTML(text);

    // Now safe to add formatted elements
    escaped = escaped.replace(/\n/g, '<br>');

    // Add icons for certain keywords (safe since we escaped first)
    escaped = escaped.replace(/✓/g, '<span style="color: #2ecc71;">✓</span>');
    escaped = escaped.replace(/⚙️/g, '<span class="pulsing">⚙️</span>');

    return escaped;
}

// Set chat status
function setChatStatus(status) {
    const statusElement = document.getElementById('chatStatus');
    if (!statusElement) return;

    if (status === 'typing') {
        statusElement.innerHTML = `
            <div class="chat-typing">
                <span>CEO Executive Agent is typing</span>
                <span></span><span></span><span></span>
            </div>
        `;
    } else if (status) {
        statusElement.textContent = status;
    } else {
        statusElement.textContent = '';
    }
}

// Clear chat
async function clearChat() {
    try {
        const response = await fetch('/api/chat/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ agent: _v4ActiveAgent || 'ceo' }),
        });
        if (!response.ok) throw new Error('Could not clear server chat history');
    } catch (error) {
        addChatMessage(error.message, 'error');
        return;
    }
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;

    messagesContainer.innerHTML = `
                <div class="chat-message system">
                    <div class="chat-message-content">
                        <strong>System:</strong> Chat cleared. How can I help you?
                    </div>
                    <div class="chat-message-time">Just now</div>
                </div>
                `;

    chatMessages = [];
}

// Toggle chat minimize
function toggleChatMinimize() {
    const chatInterface = document.getElementById('chatInterface');
    const toggleButton = document.getElementById('toggleChat');

    if (!chatInterface) return;

    chatMinimized = !chatMinimized;

    if (chatMinimized) {
        chatInterface.classList.add('minimized');
        toggleButton.textContent = '+';
        toggleButton.title = 'Maximize';
    } else {
        chatInterface.classList.remove('minimized');
        toggleButton.textContent = '−';
        toggleButton.title = 'Minimize';
    }
}

// Make functions globally accessible for inline onclick handlers
window.analyzeObjectives = analyzeObjectives;
window.runFullOrchestration = runFullOrchestration;
window.executeAgent = executeAgent;
window.viewAgentDetails = viewAgentDetails;
window.closeModal = closeModal;
window.sendChatMessage = sendChatMessage;
window.clearChat = clearChat;
window.toggleChatMinimize = toggleChatMinimize;

console.log('✅ All functions attached to window object');

// =============================================================================
// v0.4  THREE-PANEL LAYOUT  &  LLM CHAT
// All identifiers are prefixed v4 to avoid collisions with legacy code.
// =============================================================================

let _v4ActiveAgent = 'ceo';
let _v4DebateMode = false;
let _v4ConfigOpen = true;

// ── Tab switching ─────────────────────────────────────────────────────────────
function switchTab(tabName, btn) {
    document.querySelectorAll('.v4-tab-panel').forEach(p => p.classList.add('v4-hidden'));
    document.querySelectorAll('.v4-tab').forEach(t => t.classList.remove('v4-tab-active'));
    const panel = document.getElementById('tab-' + tabName);
    if (panel) panel.classList.remove('v4-hidden');
    if (btn) btn.classList.add('v4-tab-active');
}

// ── Sidebar config accordion ──────────────────────────────────────────────────
function toggleConfig() {
    const body = document.getElementById('cfgBody');
    const arrow = document.getElementById('cfgToggleArrow');
    if (!body) return;
    _v4ConfigOpen = !_v4ConfigOpen;
    body.style.display = _v4ConfigOpen ? 'flex' : 'none';
    if (arrow) arrow.textContent = _v4ConfigOpen ? '▲' : '▼';
}

// ── Agent selection (chat panel + roster + header pills) ─────────────────────
const _V4_AGENT_LABELS = {
    ceo: '👔 CEO Agent',
    cfo: '💰 CFO Agent',
    cto: '🔧 CTO Agent',
    legal: '⚖️ Legal Agent',
    branding: '🎨 Branding Agent',
    web_development: '💻 Web Dev Agent',
    martech: '📊 MarTech Agent',
    content: '✍️ Content Agent',
};

function selectChatAgent(agentKey) {
    _v4ActiveAgent = agentKey;

    // Chat-panel selector buttons
    document.querySelectorAll('.v4-agt-btn').forEach(b =>
        b.classList.toggle('v4-agt-active', b.dataset.agent === agentKey));

    // Header agent pills
    document.querySelectorAll('.v4-ha-chip').forEach(c =>
        c.classList.toggle('v4-chip-active', c.dataset.agent === agentKey));

    // Sidebar roster rows
    document.querySelectorAll('.v4-agent-row').forEach(r =>
        r.classList.toggle('v4-row-active', r.dataset.agent === agentKey));

    // Update placeholder
    const input = document.getElementById('chatInput');
    const agentLabel = (_V4_AGENT_LABELS[agentKey] || agentKey).replace(/^\S+\s/, ''); // strip emoji
    if (input) input.placeholder = 'Ask the ' + agentLabel + ' anything…';

    addChatMessage('Now talking to ' + (_V4_AGENT_LABELS[agentKey] || agentKey), 'system');
}

// ── Strategic Debate Mode toggle ──────────────────────────────────────────────
function toggleDebateMode() {
    _v4DebateMode = !_v4DebateMode;
    const btn = document.getElementById('debateModeBtn');
    if (btn) {
        btn.classList.toggle('v4-debate-active', _v4DebateMode);
        btn.textContent = _v4DebateMode
            ? '⚡ Debate Mode: ON — agent will push back'
            : '⚡ Strategic Debate Mode';
    }
    addChatMessage(
        _v4DebateMode
            ? '⚡ Debate Mode activated — the agent will challenge your ideas and defend its recommendations.'
            : '✓ Debate Mode off — returning to advisory mode.',
        'system'
    );
}

// ── Live feed cards ───────────────────────────────────────────────────────────
/**
 * addFeedCard(type, title, meta, body, metrics, actions)
 *
 * type    : 'success' | 'running' | 'info' | 'error'
 * metrics : [{val, lbl}, …]   (optional)
 * actions : [{label, onclick, primary}, …]  (optional)
 */
function addFeedCard(type, title, meta, body, metrics, actions) {
    const container = document.getElementById('liveFeedContainer');
    if (!container) return;

    const TYPE_CLASS = { success: 'v4-card-success', running: 'v4-card-running', info: 'v4-card-info', error: 'v4-card-error' };
    const BADGE_CLASS = { success: 'v4-badge-success', running: 'v4-badge-running', info: 'v4-badge-info', error: 'v4-badge-error' };

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const metricsHtml = (metrics && metrics.length)
        ? '<div class="v4-fc-metrics">' +
        metrics.map(m =>
            '<div class="v4-fc-metric"><div class="v4-m-val">' + m.val + '</div><div class="v4-m-lbl">' + m.lbl + '</div></div>'
        ).join('') +
        '</div>'
        : '';

    const actionsHtml = (actions && actions.length)
        ? '<div class="v4-fc-actions">' +
        actions.map(a => {
            // Embed onclick safely: &quot; so double-quotes inside the handler
            // don't terminate the HTML attribute value prematurely.
            const safeOnclick = a.onclick
                ? a.onclick.replace(/"/g, '&quot;')
                : '';
            return '<button class="' + (a.primary ? 'v4-btn-accent' : 'v4-btn-outline') + '"' +
                (safeOnclick ? ' onclick="' + safeOnclick + '"' : '') + '>' + a.label + '</button>';
        }).join('') +
        '</div>'
        : '';

    const card = document.createElement('div');
    card.className = 'v4-feed-card ' + (TYPE_CLASS[type] || 'v4-card-info');
    card.innerHTML =
        '<div class="v4-fc-header">' +
        '<div class="v4-fc-title">' + title +
        ' <span class="v4-fc-badge ' + (BADGE_CLASS[type] || 'v4-badge-info') + '">' +
        type.charAt(0).toUpperCase() + type.slice(1) +
        '</span>' +
        '</div>' +
        '<span class="v4-fc-time">' + now + '</span>' +
        '</div>' +
        '<div class="v4-fc-meta">' + (meta || '') + '</div>' +
        (body ? '<p class="v4-fc-text">' + body + '</p>' : '') +
        metricsHtml + actionsHtml;

    // Prepend so newest is at top
    container.insertBefore(card, container.firstChild);

    // Only auto-switch to Live if no meaningful content is in Reports yet
    const feedPanel = document.getElementById('tab-feed');
    const reportsPanel = document.getElementById('tab-reports');
    const reportDisplay = document.getElementById('reportDisplay');
    const reportsHasContent = reportDisplay &&
        reportDisplay.querySelector('.report-content') !== null;
    if (feedPanel && feedPanel.classList.contains('v4-hidden') && !reportsHasContent) {
        switchTab('feed', document.querySelector("[data-tab='feed']"));
    }
}

// ── SocketIO event handlers (registered in setupSocketListeners above) ───────
// Note: ai_chat_response, agent_deploying, agent_deployed, orchestration_complete
// listeners are registered inside setupSocketListeners() to ensure socket is ready.

// ── Intercept displayAgentReport to also add a feed card ─────────────────────
(function patchDisplayAgentReport() {
    const _orig = window.displayAgentReport;
    if (typeof _orig !== 'function') return;
    window.displayAgentReport = function (agentType, resultData, companyInfo) {
        _orig(agentType, resultData, companyInfo);
        const name = (agentType || '').split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        addFeedCard(
            'success',
            '✅ ' + name + ' Report Ready',
            (resultData.artifacts || []).length + ' local artifact(s) · Review required · Spending not measured',
            null, null,
            [{ label: '📋 View Report', onclick: "switchTab('reports', document.querySelector(\"[data-tab='reports']\"))", primary: true }]
        );
        switchTab('reports', document.querySelector('[data-tab="reports"]'));
    };
})();

// ── Expose new v0.4 functions on window ──────────────────────────────────────
window.switchTab = switchTab;
window.toggleConfig = toggleConfig;
window.selectChatAgent = selectChatAgent;
window.toggleDebateMode = toggleDebateMode;
window.addFeedCard = addFeedCard;

console.log('✅ v0.4 three-panel layout and LLM chat initialized');

async function runtimeRequest(path, body) {
    const response = await fetch(path, body === undefined ? {} : {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    });
    const data = await response.json();
    if (!response.ok || data.success === false) throw new Error(data.error || `Request failed (${response.status})`);
    return data;
}

async function setScenarioMemory(enabled) {
    try {
        if (enabled && !confirm('Save this agent/scenario conversation locally? Retrieved excerpts will be included in model prompts.')) return;
        await runtimeRequest('/api/memory/policy', {
            enabled, scenario: getScenarioFromForm(), agent: _v4ActiveAgent
        });
        addChatMessage(`Scenario memory ${enabled ? 'enabled' : 'disabled'} for ${_v4ActiveAgent}.`, 'system');
    } catch (error) { addChatMessage(error.message, 'error'); }
}

async function deleteScenarioMemory() {
    try {
        if (!confirm('Delete retained memory for this agent and current scenario?')) return;
        await runtimeRequest('/api/memory/clear', { scenario: getScenarioFromForm(), agent: _v4ActiveAgent });
        await clearChat();
        addChatMessage('Retained scenario memory deleted and disabled.', 'system');
    } catch (error) { addChatMessage(error.message, 'error'); }
}

let jobPollTimer;
async function watchDurableJob(identifier) {
    clearTimeout(jobPollTimer);
    try {
        const { job } = await runtimeRequest(`/api/jobs/${encodeURIComponent(identifier)}`);
        state.activeThreadId = identifier;
        document.getElementById('jobControls').hidden = false;
        document.getElementById('jobState').textContent =
            `${job.status} · ${job.tokens}/${job.max_tokens} measured tokens · $${job.cost.toFixed(4)} rate-calculated / $${job.max_cost} limit · ${job.reserved_tokens} tokens / $${job.reserved_cost.toFixed(4)} reserved or uncertain`;
        const approval = document.getElementById('jobApprove');
        const tests = document.getElementById('jobTests');
        const runnerLink = document.getElementById('runnerRequestLink');
        if (approval) approval.hidden = job.status !== 'awaiting_approval';
        if (tests) tests.hidden = job.kind !== 'build' || job.status !== 'succeeded';
        if (runnerLink) runnerLink.hidden = true;
        if (job.status === 'awaiting_approval') {
            updateStatus(`${job.kind}: awaiting your approval; no work started`, 'pending');
        } else if (['queued', 'running'].includes(job.status)) {
            updateStatus(`Job ${job.status}`, 'running');
            jobPollTimer = setTimeout(() => watchDurableJob(identifier), 2000);
        } else if (job.status === 'succeeded') {
            if (job.kind === 'test_request') {
                updateStatus('Runner request prepared. Tests NOT run; isolated runner is not configured.', 'pending');
                if (runnerLink) {
                    runnerLink.href = `/api/jobs/${encodeURIComponent(identifier)}/runner-request`;
                    runnerLink.hidden = false;
                }
                hideProgressBar();
                return;
            }
            updateStatus('Local artifacts generated; review required.', 'success');
            displayAgentReport('ceo', {
                ...job.result,
                execution_mode: 'local_artifacts',
                status: job.kind === 'build' ? 'Source generated · Tests NOT run' : 'Artifacts generated',
                measured_model_cost: job.cost,
                deliverables: job.kind === 'build' ? job.result.deliverables :
                    (job.result.agent_outputs || []).map(record =>
                        `${record.agent}: ${record.artifacts.length} verified local report files`)
            }, job.kind === 'build' ? job.payload.scenario : {
                ...job.payload, budget: job.payload.total_budget, timeline: job.payload.target_days
            });
            hideProgressBar();
        } else {
            updateStatus(`${job.status}: ${job.error || 'No further work will be performed'}`, 'error');
            addChatMessage(`❌ Job ${job.status}: ${job.error || 'No further work will be performed'}. No complete orchestration report was generated.`, 'error');
            hideProgressBar();
        }
    } catch (error) {
        addChatMessage(`Job status unavailable: ${error.message}. Use the job status endpoint to retry.`, 'error');
    }
}

async function proposeSourceBuild() {
    try {
        const scenario = getScenarioFromForm();
        if (!validateScenarioForExecution(scenario)) return;
        const { job } = await runtimeRequest('/api/builds/propose', { scenario });
        localStorage.setItem(ACTIVE_JOB_STORAGE_KEY, job.id);
        addChatMessage('Python source build proposed. Review and approve to generate tool.py, test_tool.py and README.md. No generated code will run on this Mac.', 'system');
        await watchDurableJob(job.id);
    } catch (error) { addChatMessage(`Source build proposal failed: ${error.message}`, 'error'); }
}

async function approveCurrentJob() {
    try {
        const { job } = await runtimeRequest(`/api/jobs/${encodeURIComponent(state.activeThreadId)}`);
        if (job.status !== 'awaiting_approval') throw new Error('Job is not awaiting approval');
        const description = job.kind === 'build'
            ? `Approve Python source generation for ${job.payload.scenario.company_name}?\nObjectives: ${job.payload.scenario.objectives.join('; ')}\nLimit: ${job.max_tokens} tokens / $${job.max_cost}. Files are untrusted; tests will NOT run.`
            : 'Approve preparing a hash-bound isolated test request? No Oracle connection or code execution occurs; tests remain NOT run.';
        if (!confirm(description)) return;
        await runtimeRequest(`/api/jobs/${encodeURIComponent(job.id)}/approve`, {});
        await watchDurableJob(job.id);
    } catch (error) { addChatMessage(`Approval failed: ${error.message}`, 'error'); }
}

async function proposeBuildTests() {
    try {
        const { job } = await runtimeRequest(`/api/builds/${encodeURIComponent(state.activeThreadId)}/propose-tests`, {});
        localStorage.setItem(ACTIVE_JOB_STORAGE_KEY, job.id);
        await watchDurableJob(job.id);
    } catch (error) { addChatMessage(`Test request failed: ${error.message}`, 'error'); }
}

async function cancelCurrentJob() {
    try {
        await runtimeRequest(`/api/jobs/${encodeURIComponent(state.activeThreadId)}/cancel`, {});
        addChatMessage('Cancellation requested. An in-flight model call may finish; later calls will be blocked.', 'system');
        watchDurableJob(state.activeThreadId);
    } catch (error) { addChatMessage(error.message, 'error'); }
}

async function proposeCurrentExport() {
    try {
        const { job } = await runtimeRequest('/api/connectors/local-export', { source_job: state.activeThreadId });
        if (!confirm(`Approve local ZIP export of job ${state.activeThreadId}? No network action is performed.`)) {
            await runtimeRequest(`/api/jobs/${job.id}/cancel`, {});
            return;
        }
        await runtimeRequest(`/api/jobs/${job.id}/approve`, {});
        const check = async () => {
            try {
                const { job: exportJob } = await runtimeRequest(`/api/jobs/${job.id}`);
                if (['queued', 'running'].includes(exportJob.status)) return setTimeout(check, 1000);
                if (exportJob.status !== 'succeeded') throw new Error(exportJob.error || exportJob.status);
                addChatMessage('Approved local export ready. Download from the job controls.', 'system');
                const link = document.createElement('a');
                link.href = `/api/jobs/${job.id}/download`;
                link.textContent = 'Download approved ZIP';
                document.getElementById('jobControls').appendChild(link);
            } catch (error) { addChatMessage(error.message, 'error'); }
        };
        check();
    } catch (error) { addChatMessage(error.message, 'error'); }
}

document.addEventListener('DOMContentLoaded', () => {
    const job = localStorage.getItem(ACTIVE_JOB_STORAGE_KEY);
    if (job) watchDurableJob(job);
});
