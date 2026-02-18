// Multi-Agent System Dashboard JavaScript

// Initialize Socket.IO connection
let socket;

const SCENARIO_STORAGE_KEY = 'ceo_agent_scenario';
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
    'Hospitality & Tourism'
]);

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
        total: 1000,
        remaining: 1000,
        allocated: {}
    },
    executionStatus: 'idle'
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Dashboard initializing...');

    // Initialize SocketIO
    try {
        socket = io();
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
        company_name: configDefaults.company_name || 'Amazon Granite LLC',
        dba_name: configDefaults.dba_name || 'SurfaceCraft Studio',
        industry: configDefaults.industry || 'Construction, Custom Countertops',
        location: configDefaults.location || 'Cincinnati, OH',
        budget: Number.parseFloat(configDefaults.budget) || 1000,
        timeline: Number.parseInt(configDefaults.timeline, 10) || 30,
        objectives: Array.isArray(configDefaults.objectives) && configDefaults.objectives.length > 0
            ? configDefaults.objectives
            : [...DEFAULT_DEV_OBJECTIVES]
    };
}

function isLegacyScenarioShape(scenario) {
    if (!scenario || typeof scenario !== 'object') return false;

    let score = 0;
    if (['Software & Technology', 'AI Technology', 'General Business', 'Granite & Countertops'].includes((scenario.industry || '').trim())) {
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

    const parsedBudget = Number.parseFloat(budgetInput?.value || '');
    const parsedTimeline = Number.parseInt(timelineInput?.value || '', 10);

    const companyInfo = {
        company_name: companyNameInput?.value || defaults.company_name,
        dba_name: dbaNameInput?.value || companyNameInput?.value || defaults.dba_name,
        industry: getIndustryValueFromForm() || defaults.industry,
        location: locationInput?.value || defaults.location,
        budget: Number.isFinite(parsedBudget) ? parsedBudget : defaults.budget,
        timeline: Number.isFinite(parsedTimeline) ? parsedTimeline : defaults.timeline
    };

    return {
        ...companyInfo,
        objectives: Array.isArray(defaults.objectives) ? defaults.objectives : buildDefaultObjectives(companyInfo),
        updated_at: new Date().toISOString()
    };
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
}

async function syncScenarioToBackend(scenario) {
    try {
        await fetch('/api/scenario/current', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(scenario)
        });
    } catch (error) {
        console.warn('Scenario sync to backend failed:', error);
    }
}

function persistScenarioToStorage(options = {}) {
    const scenario = getScenarioFromForm();
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

    const handleUserChange = () => {
        persistScenarioToStorage({ syncBackend: true, userModified: true, source: 'user_change' });
    };

    ['companyName', 'dbaName', 'industry', 'industryOther', 'location', 'budget', 'timeline'].forEach((elementId) => {
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
        applyScenarioToForm(data.scenario);
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
            timeline: data.timeline || 90,
            deliverables: data.deliverables || [],
            agent_outputs: data.agent_outputs || [],
            completed_tasks: data.completed_tasks || 0,
            total_tasks: data.total_tasks || 0,
            budget_used: data.budget_used || 0,
            budget_remaining: data.budget_remaining || 0,
            total_budget: data.total_budget || 0
        };

        console.log('📊 Displaying orchestration report with:', analysisData);
        displayOrchestrationReport(companyInfo, analysisData);

        // Chat notification - orchestration complete
        addChatMessage(`🎉 Full orchestration complete! Executed ${data.total_tasks || 0} tasks. Total budget used: $${data.budget_used}. Check the Execution Report below for details.`, 'assistant');

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
        updateStatus('Analyzing strategic objectives...', 'running');
        addLogEntry('CFO Agent: Starting strategic analysis', 'warning');

        const scenario = persistScenarioToStorage();

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
        addChatMessage(`🔍 Starting strategic analysis for ${scenario.company_name}...`, 'system');

        const response = await fetch('/api/cfo/analyze', {
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
            addLogEntry(`Identified ${data.tasks.length} tasks across ${Object.keys(data.budget_allocation).length} domains`, 'success');

            // Display analysis report in execution report section
            displayAnalysisReport(scenario, data);

            // Chat notification - analysis complete
            addChatMessage(`✅ Analysis complete! Identified ${data.tasks.length} tasks across ${Object.keys(data.budget_allocation).length} domains. Budget allocated accordingly.`, 'assistant');
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
function runFullOrchestration() {
    console.log('🚀 Launch Full Orchestration button clicked');
    try {
        const scenario = persistScenarioToStorage();
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

        console.log('Emitting execute_full_orchestration with:', { company_info: companyInfo, objectives });

        // Chat notification - orchestration starting
        addChatMessage(`🚀 Launching full orchestration for ${companyInfo.company_name}. This will execute all 6 agents sequentially...`, 'system');

        socket.emit('execute_full_orchestration', {
            company_info: companyInfo,
            objectives: objectives
        });

        addLogEntry('Orchestration request sent to server...', 'warning');
        addChatMessage('📡 Orchestration request sent to CFO. Agents will execute in optimal order.', 'assistant');
    } catch (error) {
        console.error('Orchestration error:', error);
        addLogEntry(`Error launching orchestration: ${error.message}`, 'error');
        addChatMessage(`❌ Orchestration failed: ${error.message}`, 'error');
    }
}

// Execute specific agent
async function executeAgent(agentType) {
    console.log(`🤖 Execute button clicked for: ${agentType}`);
    addLogEntry(`Executing ${agentType.toUpperCase()} Agent...`, 'warning');
    highlightAgent(agentType, 'executing');

    try {
        const scenario = persistScenarioToStorage();
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
                company_info: companyInfo
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
            addLogEntry(`Budget used: $${data.result.budget_used || 0}`, 'success');
            if (data.result.deliverables && data.result.deliverables.length > 0) {
                addLogEntry(`Deliverables: ${data.result.deliverables.length} items created`, 'success');
            }
            highlightAgent(agentType, 'complete');
            updateStatus(`${agentType} agent completed successfully`, 'success');

            // Chat notification - agent complete
            const agentName = agentType.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
            const deliverableCount = data.result.deliverables ? data.result.deliverables.length : 0;
            const budgetUsed = data.result.budget_used || 0;
            addChatMessage(`✅ ${agentName} Agent completed! Generated ${deliverableCount} deliverables using $${budgetUsed} budget. Check the Execution Report for details.`, 'assistant');

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
            addChatMessage(`❌ ${agentName} Agent failed: ${data.error}`, 'error');
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
            addChatMessage(`✅ ${agentName} Agent details loaded. Budget limit: $${data.guard_rail.max_budget}`, 'assistant');
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

    content.innerHTML = `
        <h2>${getAgentIcon(agentType)} ${agentType.toUpperCase().replace('_', ' ')} Agent</h2>

        <h3>💰 Budget Constraint</h3>
        <p style="font-size: 24px; font-weight: bold; color: #10B981;">$${guardRail.max_budget}</p>

        <h3>✅ What This Agent DOES (Execution Mode)</h3>
        <ul style="list-style: none; padding-left: 0;">
            ${permittedTasks}
        </ul>

        <h3>💳 Allowed Spending Categories</h3>
        <ul style="list-style: none; padding-left: 0;">
            ${allowedCategories}
        </ul>

        <h3>🛡️ Guard Rails Active</h3>
        <div style="background: #D1FAE5; padding: 15px; border-radius: 8px; color: #065F46;">
            <strong>✅ Execution Mode:</strong> AI performs work (does not recommend vendors)<br>
            <strong>✅ Budget Protection:</strong> Cannot exceed $${guardRail.max_budget}<br>
            <strong>✅ Scope Validation:</strong> Stays within permitted tasks only<br>
            <strong>✅ Quality Standards:</strong> ${Object.keys(guardRail.quality_standards).length} metrics enforced
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
    const deliverables = resultData.deliverables || [];
    console.log('📦 [displayAgentReport] Processing deliverables:', deliverables);

    const deliverablesHTML = deliverables.length > 0
        ? `<ul class="report-deliverables">
        ${deliverables.map(d => `<li>${d}</li>`).join('')}
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
        ? `<div class="report-section">
        <h4>🎨 Brand Kit Reference</h4>
        <div style="padding:12px;background:rgba(37,99,235,0.08);border-radius:8px;border-left:3px solid #2563eb;">
            <p style="margin:4px 0;color:#cbd5e1;"><strong style="color:#60a5fa;">Brand:</strong> ${_brandKit.brand_name}</p>
            <p style="margin:4px 0;color:#cbd5e1;"><strong style="color:#60a5fa;">Direction:</strong> ${_brandKit.direction || ''}</p>
            <p style="margin:4px 0;color:#cbd5e1;"><strong style="color:#60a5fa;">Logo approach:</strong> ${_brandKit.logo_reference || ''}</p>
            <p style="margin:4px 0;color:#cbd5e1;"><strong style="color:#60a5fa;">Core palette:</strong> ${(_brandKit.color_palette && _brandKit.color_palette.primary ? _brandKit.color_palette.primary : []).join(' · ')}</p>
            <p style="margin:4px 0;color:#cbd5e1;"><strong style="color:#60a5fa;">Typography:</strong> ${_brandKit.typography_note || ''}</p>
        </div></div>`
        : '';

    // Design concept proposals (branding agent)
    const _concepts = resultData.design_concepts;
    const designConceptsHTML = _concepts && _concepts.length > 0
        ? `<div class="report-section">
        <h4>🖼️ Logo Proposals (${_concepts.length})</h4>
        ${_concepts.map((c, idx) => `
            <div style="margin-bottom:12px;padding:14px;background:rgba(37,99,235,0.08);border-radius:8px;border-left:3px solid #2563eb;">
                <p style="margin:0 0 4px;font-weight:700;font-size:14px;color:#60a5fa;">0${idx + 1} — ${c.concept_name}</p>
                <p style="margin:0 0 6px;font-size:13px;color:#cbd5e1;">${c.description}</p>
                <div style="font-size:11px;color:#64748b;display:flex;gap:12px;flex-wrap:wrap;margin-bottom:6px;">
                    <span>📱 ${c.applications}</span><span>⚡ ${c.scalability}</span><span>💰 ${c.tools_budget}</span>
                </div>
                <ul style="margin:0;padding-left:16px;font-size:12px;color:#94a3b8;">
                    ${(c.design_principles || []).map(p => `<li style="margin-bottom:2px;">${p}</li>`).join('')}
                </ul>
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

    // Build the full report HTML
    const reportHTML = `
        <div class="report-content">
            <div class="report-header">
                <span style="font-size: 2.5rem;">${agentIcon}</span>
                <h3>${agentName} Agent Report</h3>
                <span class="report-badge">✓ Completed</span>
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
                <div class="report-metric-label">Budget Used</div>
                <div class="report-metric-value">$${resultData.budget_used || 0}</div>
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
        ${brandKitHTML}
        ${designConceptsHTML}
        ${communityPlaybookHTML}
        ${campaignIdeasHTML}

        <div style="margin-top: 2.5rem; padding-top: 1.5rem; border-top: 2px solid rgba(59, 130, 246, 0.2); opacity: 0.7; font-size: 0.9rem; color: #94a3b8;">
            <p style="margin: 0;">⏱️ Execution Time: ${resultData.timestamp || new Date().toLocaleString()}</p>
        </div>
    </div>
`;

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
    console.log('📊 [displayAnalysisReport] Starting analysis report display');
    console.log('📊 Analysis data:', analysisData);

    const reportDisplay = document.getElementById('reportDisplay');
    if (!reportDisplay) {
        console.error('❌ [displayAnalysisReport] Report display element not found!');
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

    const tasks = analysisData.tasks || [];
    const budgetAllocation = analysisData.budget_allocation || {};
    const totalAllocated = Object.values(budgetAllocation).reduce((sum, val) => sum + val, 0);
    const risks = analysisData.risks || [];
    const timeline = analysisData.timeline || 90;

    // Group tasks by domain
    const tasksByDomain = {};
    tasks.forEach(task => {
        const domain = task.expertise_required || 'General';
        if (!tasksByDomain[domain]) {
            tasksByDomain[domain] = [];
        }
        tasksByDomain[domain].push(task);
    });

    // Build budget allocation HTML
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

    // Build tasks summary HTML
    const tasksSummaryHTML = Object.keys(tasksByDomain).length > 0
        ? `<div class="report-section">
            <h4>📋 Tasks by Domain</h4>
            ${Object.entries(tasksByDomain).map(([domain, domainTasks]) => `
                <div style="margin-bottom: 16px; padding: 16px; background: rgba(102, 126, 234, 0.08); border-radius: 10px; border-left: 4px solid #667eea;">
                    <div style="font-weight: 700; color: #667eea; margin-bottom: 8px; font-size: 16px;">
                        ${domain} (${domainTasks.length} tasks)
                    </div>
                    <ul style="list-style: none; padding: 0; margin: 0;">
                        ${domainTasks.slice(0, 3).map(task => `
                            <li style="padding: 8px 0; color: #64748b; font-size: 14px;">
                                • ${task.description || task.task_description}
                            </li>
                        `).join('')}
                        ${domainTasks.length > 3 ? `<li style="padding: 8px 0; color: #94a3b8; font-style: italic;">+ ${domainTasks.length - 3} more tasks</li>` : ''}
                    </ul>
                </div>
            `).join('')}
           </div>`
        : '';

    // Build risks HTML
    const risksHTML = risks.length > 0
        ? `<div class="report-section">
            <h4>⚠️ Identified Risks</h4>
            <ul class="report-deliverables">
                ${risks.map(risk => `<li style="border-left-color: #f59e0b; background: rgba(245, 158, 11, 0.12);">${risk}</li>`).join('')}
            </ul>
           </div>`
        : '';

    const reportHTML = `
        <div class="report-content">
            <div class="report-header">
                <span style="font-size: 2.5rem;">🔍</span>
                <h3>Strategic Analysis Report</h3>
                <span class="report-badge">✓ Complete</span>
            </div>

            <div class="report-section" style="margin-bottom: 24px; padding: 16px; background: rgba(59, 130, 246, 0.08); border-radius: 10px; border-left: 4px solid #3b82f6;">
                <p style="color: #334155; margin: 0; font-size: 15px;">
                    <strong style="color: #667eea;">Company:</strong> ${companyInfo.company_name} |
                    <strong style="color: #667eea;">Industry:</strong> ${companyInfo.industry} |
                    <strong style="color: #667eea;">Location:</strong> ${companyInfo.location}
                </p>
            </div>

            <div class="report-metrics">
                <div class="report-metric">
                    <div class="report-metric-label">Total Tasks</div>
                    <div class="report-metric-value">${tasks.length}</div>
                </div>
                <div class="report-metric">
                    <div class="report-metric-label">Domains</div>
                    <div class="report-metric-value">${Object.keys(budgetAllocation).length}</div>
                </div>
                <div class="report-metric">
                    <div class="report-metric-label">Budget Allocated</div>
                    <div class="report-metric-value">$${totalAllocated}</div>
                </div>
                <div class="report-metric">
                    <div class="report-metric-label">Timeline</div>
                    <div class="report-metric-value" style="font-size: 20px; color: #10b981;">${timeline} days</div>
                </div>
            </div>

            ${budgetHTML}
            ${tasksSummaryHTML}
            ${risksHTML}

            <div class="report-section">
                <h4>👉 Next Steps</h4>
                <p style="color: #334155; line-height: 1.8; font-size: 15px;">
                    Review the <strong>Task Decomposition</strong> section below for detailed breakdown.
                    You can now execute individual agents from the <strong>Available AI Agents</strong> section
                    or click <strong>Launch Full Orchestration</strong> to execute all tasks in optimal order.
                </p>
            </div>

            <div style="margin-top: 2.5rem; padding-top: 1.5rem; border-top: 2px solid rgba(148, 163, 184, 0.2); opacity: 0.7; font-size: 0.9rem; color: #64748b;">
                <p style="margin: 0;">⏱️ Analysis Time: ${new Date().toLocaleString()}</p>
            </div>
        </div>
    `;

    console.log('🎨 [displayAnalysisReport] Setting innerHTML...');
    reportDisplay.innerHTML = reportHTML;
    console.log('✅ [displayAnalysisReport] innerHTML set successfully!');

    // Add glowing border effect
    reportDisplay.style.border = '3px solid #f59e0b';
    reportDisplay.style.boxShadow = '0 0 30px rgba(245, 158, 11, 0.6), 0 12px 40px rgba(0, 0, 0, 0.2)';

    setTimeout(() => {
        reportDisplay.style.border = '2px solid rgba(102, 126, 234, 0.5)';
        reportDisplay.style.boxShadow = '0 12px 40px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)';
    }, 2000);

    // Scroll to the report
    setTimeout(() => {
        reportDisplay.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'nearest'
        });
        console.log('✅ [displayAnalysisReport] Scrolled to report!');
    }, 200);

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
    const timeline = reportData.timeline || 90;
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

// Send chat message
async function sendChatMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();

    if (!message) return;

    // Add user message to chat
    addChatMessage(message, 'user');
    chatInput.value = '';

    // Show typing indicator
    setChatStatus('typing');

    // Process message (simple command parser)
    try {
        const response = await processChatCommand(message);
        addChatMessage(response, 'assistant');
    } catch (error) {
        addChatMessage(`Error: ${error.message}`, 'error');
    } finally {
        setChatStatus('');
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
function clearChat() {
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

let _v4ActiveAgent  = 'ceo';
let _v4DebateMode   = false;
let _v4ConfigOpen   = true;

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
  const body  = document.getElementById('cfgBody');
  const arrow = document.getElementById('cfgToggleArrow');
  if (!body) return;
  _v4ConfigOpen = !_v4ConfigOpen;
  body.style.display = _v4ConfigOpen ? 'flex' : 'none';
  if (arrow) arrow.textContent = _v4ConfigOpen ? '▲' : '▼';
}

// ── Agent selection (chat panel + roster + header pills) ─────────────────────
const _V4_AGENT_LABELS = {
  ceo:             '👔 CEO Agent',
  cfo:             '💰 CFO Agent',
  cto:             '🔧 CTO Agent',
  legal:           '⚖️ Legal Agent',
  branding:        '🎨 Branding Agent',
  web_development: '💻 Web Dev Agent',
  martech:         '📊 MarTech Agent',
  content:         '✍️ Content Agent',
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
  const input      = document.getElementById('chatInput');
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

  const TYPE_CLASS  = { success:'v4-card-success', running:'v4-card-running', info:'v4-card-info', error:'v4-card-error' };
  const BADGE_CLASS = { success:'v4-badge-success', running:'v4-badge-running', info:'v4-badge-info', error:'v4-badge-error' };

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
        actions.map(a =>
          '<button class="' + (a.primary ? 'v4-btn-accent' : 'v4-btn-outline') + '"' +
          (a.onclick ? ' onclick="' + a.onclick + '"' : '') + '>' + a.label + '</button>'
        ).join('') +
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

  // Auto-switch to Live tab if another tab is active
  const feedPanel = document.getElementById('tab-feed');
  if (feedPanel && feedPanel.classList.contains('v4-hidden')) {
    switchTab('feed', document.querySelector('[data-tab="feed"]'));
  }
}

// ── Override sendChatMessage to use LLM backend via SocketIO ─────────────────
window.sendChatMessage = function () {
  const chatInput = document.getElementById('chatInput');
  const message   = chatInput ? chatInput.value.trim() : '';
  if (!message) return;

  addChatMessage(message, 'user');
  if (chatInput) chatInput.value = '';
  setChatStatus('typing…');

  // Build scenario context from sidebar form fields
  const scenario = {
    company_name: document.getElementById('companyName')?.value  || '',
    industry:     document.getElementById('industry')?.value     || '',
    location:     document.getElementById('location')?.value     || '',
    budget:       parseFloat(document.getElementById('budget')?.value)   || 5000,
    timeline:     parseInt(document.getElementById('timeline')?.value, 10) || 30,
  };

  if (typeof socket !== 'undefined' && socket && socket.connected) {
    socket.emit('ai_chat_request', {
      message,
      agent:       _v4ActiveAgent,
      debate_mode: _v4DebateMode,
      scenario,
    });
  } else {
    // Fallback: REST endpoint
    fetch('/api/chat/message', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ message, agent: _v4ActiveAgent, debate_mode: _v4DebateMode, scenario }),
    })
      .then(r  => r.json())
      .then(d  => { addChatMessage(d.response || 'No response received.', 'assistant'); setChatStatus(''); })
      .catch(e => { addChatMessage('Error: ' + e.message, 'error'); setChatStatus(''); });
  }
};

// ── SocketIO event handlers ───────────────────────────────────────────────────
(function attachV4SocketHandlers() {
  if (typeof socket === 'undefined' || !socket) return;

  // LLM chat reply
  socket.on('ai_chat_response', function (data) {
    setChatStatus('');
    if (data && data.message) addChatMessage(data.message, 'assistant');
  });

  // Agent lifecycle → live feed cards
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

  socket.on('orchestration_complete', function (data) {
    addFeedCard(
      'success',
      '🎯 Orchestration Complete',
      (data.completed_tasks || 0) + ' of ' + (data.total_tasks || 0) + ' tasks',
      null,
      [
        { val: data.completed_tasks || 0, lbl: 'Done' },
        { val: '$' + (data.budget_used || 0), lbl: 'Used' },
        { val: data.total_tasks      || 0, lbl: 'Total' },
      ],
      [{ label: '📄 View Report', onclick: "switchTab('reports', document.querySelector('[data-tab=\"reports\"]'))", primary: true }]
    );
  });
})();

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
      (resultData.deliverables ? resultData.deliverables.length : 0) + ' deliverable(s) · $' + (resultData.budget_used || 0),
      null, null,
      [{ label: '📋 View Report', onclick: "switchTab('reports', document.querySelector('[data-tab=\"reports\"]'))", primary: true }]
    );
    switchTab('reports', document.querySelector('[data-tab="reports"]'));
  };
})();

// ── Expose new v0.4 functions on window ──────────────────────────────────────
window.switchTab      = switchTab;
window.toggleConfig   = toggleConfig;
window.selectChatAgent = selectChatAgent;
window.toggleDebateMode = toggleDebateMode;
window.addFeedCard    = addFeedCard;

console.log('✅ v0.4 three-panel layout and LLM chat initialized');
