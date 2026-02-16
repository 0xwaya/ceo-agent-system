/**
 * CEO Executive Agent - Graph Dashboard
 * Frontend controller for graph_architecture system
 */

// WebSocket connection
const socket = io();
const SCENARIO_STORAGE_KEY = 'ceo_agent_scenario';
const DASHBOARD_CONFIG = window.GRAPH_DASHBOARD_CONFIG || {};
const SCENARIO_STORAGE_SCHEMA_VERSION = DASHBOARD_CONFIG.defaults?.scenario_schema_version || 1;
const SCENARIO_DEFAULTS_VERSION = DASHBOARD_CONFIG.defaults?.scenario_defaults_version || (DASHBOARD_CONFIG.isProduction ? 'production' : 'development');

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

const DEFAULT_DEV_SCENARIO = {
    company_name: 'Amazon Granite LLC',
    dba_name: 'SurfaceCraft Studio',
    industry: 'Construction, Custom Countertops',
    location: 'Cincinnati, OH',
    budget: 1000,
    timeline: 30,
    objectives: [
        'Launch AR platform showroom',
        'Relaunch the company brand as SurfaceCraft Studio',
        'Create a brand kit to be use across platforms',
        'Create and maintain social media accounts and content creation',
        'Possition the company in the highend exclusive market',
        'Create all necessary agent to execute and manage customer caption and retention',
        'Create sales agent to target residential and commercial contracts',
        'Register as a minority business with the city of Cincinnati',
        'Automate most processes that deals with outside sales'
    ]
};

const LEGACY_OBJECTIVE_MARKERS = new Set([
    'Launch SaaS platform',
    'Build enterprise sales team',
    'Establish market presence',
    'Scale to $1M ARR'
]);

// State management
let currentExecution = null;
let isExecuting = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Graph Dashboard initialized');
    setupSocketListeners();
    initializeScenarioForm();
    loadAvailableAgents();
});

async function loadAvailableAgents() {
    const container = document.getElementById('specializedAgentsList');
    if (!container) return;

    try {
        const response = await fetch('/api/agents/available');
        const data = await response.json();
        const agents = Array.isArray(data.agents) ? data.agents : [];

        if (agents.length === 0) {
            container.innerHTML = '<div style="color: var(--text-tertiary)">No agents available.</div>';
            return;
        }

        container.innerHTML = agents
            .map((agent) => {
                const icon = getAgentIcon(agent.type || agent.name || 'agent');
                const capabilities = Array.isArray(agent.capabilities) ? agent.capabilities : [];
                const primaryCapability = capabilities[0] || 'Specialized support';
                return `
                    <div style="padding: 0.75rem 0; border-bottom: 1px solid var(--border-primary);">
                        <div style="display: flex; justify-content: space-between; align-items: center; gap: 1rem;">
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span>${icon}</span>
                                <strong>${agent.name || (agent.type || 'Agent').toUpperCase()}</strong>
                            </div>
                            <span class="badge badge-info">${(agent.status || 'available').toUpperCase()}</span>
                        </div>
                        <div style="margin-top: 0.25rem; color: var(--text-tertiary); font-size: var(--text-sm);">
                            ${primaryCapability}
                        </div>
                    </div>
                `;
            })
            .join('');
    } catch (error) {
        console.error('Failed to load available agents', error);
        container.innerHTML = '<div style="color: var(--error)">Failed to load agents.</div>';
    }
}

// Socket event listeners
function setupSocketListeners() {
    socket.on('connect', () => {
        console.log('Connected to server');
        addTerminalLine('✅ Connected to orchestration server', 'success');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        addTerminalLine('⚠️ Disconnected from server', 'warning');
    });

    socket.on('execution_started', (data) => {
        console.log('Execution started:', data);
        handleExecutionStarted(data);
    });

    socket.on('agent_update', (data) => {
        console.log('Agent update:', data);
        handleAgentUpdate(data);
    });

    socket.on('execution_complete', (data) => {
        console.log('Execution complete:', data);
        handleExecutionComplete(data);
    });

    socket.on('execution_error', (data) => {
        console.error('Execution error:', data);
        handleExecutionError(data);
    });

    socket.on('phase_update', (data) => {
        console.log('Phase update:', data);
        handlePhaseUpdate(data);
    });

    socket.on('scenario_updated', (data) => {
        if (!data || !data.scenario) return;
        applyScenarioToForm(data.scenario);
        saveScenarioToLocal(data.scenario, { source: 'socket_sync', userModified: false });
    });
}

function getDefaultScenario() {
    const configDefaults = DASHBOARD_CONFIG.defaults || {};
    if (DASHBOARD_CONFIG.isProduction) {
        return {
            company_name: '',
            dba_name: '',
            industry: '',
            location: '',
            budget: '',
            timeline: '',
            objectives: []
        };
    }

    return {
        ...DEFAULT_DEV_SCENARIO,
        ...configDefaults,
        objectives: Array.isArray(configDefaults.objectives)
            ? configDefaults.objectives
            : (typeof configDefaults.objectives_text === 'string'
                ? configDefaults.objectives_text.split('\n').map((line) => line.trim()).filter(Boolean)
                : DEFAULT_DEV_SCENARIO.objectives)
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
            environment: DASHBOARD_CONFIG.isProduction ? 'production' : 'development',
            source: options.source || 'dashboard',
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

        if (parsed.scenario && typeof parsed.scenario === 'object' && parsed.meta && typeof parsed.meta === 'object') {
            const sameSchema = parsed.meta.schema_version === SCENARIO_STORAGE_SCHEMA_VERSION;
            const sameDefaults = parsed.meta.defaults_version === SCENARIO_DEFAULTS_VERSION;

            if (sameSchema && sameDefaults) {
                return parsed.scenario;
            }

            if (!DASHBOARD_CONFIG.isProduction && !parsed.meta.user_modified && isLegacyScenarioShape(parsed.scenario)) {
                return getDefaultScenario();
            }

            return parsed.scenario;
        }

        if (parsed.company_name || parsed.industry || parsed.location) {
            if (!DASHBOARD_CONFIG.isProduction && isLegacyScenarioShape(parsed)) {
                return getDefaultScenario();
            }
            return parsed;
        }
    } catch (error) {
        console.warn('Unable to parse scenario storage envelope', error);
    }

    return null;
}

function getSelectedIndustry() {
    const industrySelect = document.getElementById('industry');
    const industryOther = document.getElementById('industryOther');
    if (!industrySelect) return '';
    if (industrySelect.value === 'Other') {
        return (industryOther?.value || '').trim();
    }
    return industrySelect.value.trim();
}

function setIndustryValue(industryValue) {
    const industrySelect = document.getElementById('industry');
    const industryOther = document.getElementById('industryOther');
    const industryOtherGroup = document.getElementById('industryOtherGroup');
    const normalized = (industryValue || '').trim();

    if (!industrySelect || !industryOther || !industryOtherGroup) return;

    if (!normalized) {
        industrySelect.value = '';
        industryOther.value = '';
        industryOtherGroup.style.display = 'none';
        return;
    }

    if (INDUSTRY_OPTIONS.has(normalized)) {
        industrySelect.value = normalized;
        industryOther.value = '';
        industryOtherGroup.style.display = 'none';
    } else {
        industrySelect.value = 'Other';
        industryOther.value = normalized;
        industryOtherGroup.style.display = 'block';
    }
}

function collectScenarioFromForm() {
    const objectivesText = document.getElementById('objectives').value.trim();
    return {
        company_name: document.getElementById('companyName').value.trim(),
        dba_name: document.getElementById('dbaName').value.trim(),
        industry: getSelectedIndustry(),
        location: document.getElementById('location').value.trim(),
        budget: parseFloat(document.getElementById('totalBudget').value),
        timeline: parseInt(document.getElementById('targetDays').value),
        objectives: objectivesText
            .split('\n')
            .map((line) => line.trim())
            .filter((line) => line.length > 0)
    };
}

function applyScenarioToForm(scenario) {
    const resolved = scenario || getDefaultScenario();
    document.getElementById('companyName').value = resolved.company_name || resolved.name || '';
    document.getElementById('dbaName').value = resolved.dba_name || '';
    setIndustryValue(resolved.industry || '');
    document.getElementById('location').value = resolved.location || '';
    document.getElementById('totalBudget').value = resolved.budget ?? '';
    document.getElementById('targetDays').value = resolved.timeline ?? '';

    const objectives = Array.isArray(resolved.objectives)
        ? resolved.objectives
        : [];
    document.getElementById('objectives').value = objectives.join('\n');
}

function saveScenarioToLocal(scenario, options = {}) {
    try {
        const envelope = buildScenarioEnvelope(scenario, {
            source: options.source || 'dashboard_local',
            userModified: Boolean(options.userModified)
        });
        localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(envelope));
    } catch (error) {
        console.warn('Unable to write scenario to localStorage', error);
    }
}

async function syncScenarioToBackend(scenario) {
    try {
        await fetch('/api/scenario/current', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(scenario)
        });
    } catch (error) {
        console.warn('Failed to sync scenario state to backend', error);
    }
}

async function initializeScenarioForm() {
    const industrySelect = document.getElementById('industry');
    const formIds = ['companyName', 'dbaName', 'industry', 'industryOther', 'location', 'totalBudget', 'targetDays', 'objectives'];

    if (industrySelect) {
        industrySelect.addEventListener('change', () => {
            const selected = industrySelect.value;
            const group = document.getElementById('industryOtherGroup');
            if (group) {
                group.style.display = selected === 'Other' ? 'block' : 'none';
            }
            if (selected !== 'Other') {
                const otherInput = document.getElementById('industryOther');
                if (otherInput) otherInput.value = '';
            }
        });
    }

    let initialScenario = getDefaultScenario();

    if (!DASHBOARD_CONFIG.isProduction) {
        try {
            const response = await fetch('/api/scenario/current');
            if (response.ok) {
                const data = await response.json();
                if (data && data.success && data.scenario) {
                    initialScenario = data.scenario;
                }
            }
        } catch (error) {
            console.warn('Unable to fetch shared scenario, using local/default values', error);
            const localScenario = parseScenarioEnvelope(localStorage.getItem(SCENARIO_STORAGE_KEY));
            if (localScenario) {
                initialScenario = localScenario;
            }
        }
    }

    applyScenarioToForm(initialScenario);
    saveScenarioToLocal(initialScenario, { source: 'init', userModified: false });

    let syncTimer = null;
    const queueSync = () => {
        const scenario = collectScenarioFromForm();
        saveScenarioToLocal(scenario, { source: 'form_change', userModified: true });
        if (syncTimer) {
            clearTimeout(syncTimer);
        }
        syncTimer = setTimeout(() => {
            syncScenarioToBackend(scenario);
        }, 300);
    };

    formIds.forEach((id) => {
        const element = document.getElementById(id);
        if (!element) return;
        element.addEventListener('input', queueSync);
        element.addEventListener('change', queueSync);
    });
}

// Execute multi-agent orchestration
async function executeOrchestration() {
    if (isExecuting) {
        alert('An execution is already in progress');
        return;
    }

    // Collect form data
    const companyName = document.getElementById('companyName').value.trim();
    const dbaName = document.getElementById('dbaName').value.trim();
    const industry = getSelectedIndustry();
    const location = document.getElementById('location').value.trim();
    const totalBudget = parseFloat(document.getElementById('totalBudget').value);
    const targetDays = parseInt(document.getElementById('targetDays').value);
    const objectivesText = document.getElementById('objectives').value.trim();
    const threadId = document.getElementById('threadId').value.trim();

    // Validation
    if (!companyName || !industry || !location) {
        alert('Please fill in all required fields');
        return;
    }

    if (!Number.isFinite(totalBudget) || totalBudget < 1000 || totalBudget > 1000000) {
        alert('Budget must be between $1,000 and $1,000,000');
        return;
    }

    if (!Number.isFinite(targetDays) || targetDays < 30 || targetDays > 365) {
        alert('Timeline must be between 30 and 365 days');
        return;
    }

    // Parse objectives
    const objectives = objectivesText
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);

    if (objectives.length === 0) {
        alert('Please enter at least one strategic objective');
        return;
    }

    // Prepare request payload
    const payload = {
        company_name: companyName,
        dba_name: dbaName,
        industry: industry,
        location: location,
        total_budget: totalBudget,
        target_days: targetDays,
        objectives: objectives,
        thread_id: threadId || null,
        use_checkpointing: true
    };

    saveScenarioToLocal({
        company_name: companyName,
        dba_name: dbaName,
        industry,
        location,
        budget: totalBudget,
        timeline: targetDays,
        objectives
    }, { source: 'execute_submit', userModified: true });
    syncScenarioToBackend({
        company_name: companyName,
        dba_name: dbaName,
        industry,
        location,
        budget: totalBudget,
        timeline: targetDays,
        objectives
    });

    // Update UI
    isExecuting = true;
    document.getElementById('executeBtn').disabled = true;
    document.getElementById('executeBtn').textContent = '⏳ Executing...';

    // Show progress card and output card
    document.getElementById('progressCard').style.display = 'block';
    document.getElementById('outputCard').style.display = 'block';
    document.getElementById('resultsCard').style.display = 'none';

    // Clear previous output
    document.getElementById('executionOutput').innerHTML =
        '<div class="terminal-line terminal-prompt">Initiating multi-agent system execution...</div>';

    // Reset agent statuses
    updateAgentStatus('ceo', 'active');
    updateAgentStatus('cfo', 'idle');
    updateAgentStatus('engineer', 'idle');
    updateAgentStatus('researcher', 'idle');

    try {
        // Make API request
        const response = await fetch('/api/graph/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Execution failed');
        }

        // Handle success (actual updates come via WebSocket)
    } catch (error) {
        console.error('Execution error:', error);
        addTerminalLine(`❌ Error: ${error.message}`, 'error');
        isExecuting = false;
        document.getElementById('executeBtn').disabled = false;
        document.getElementById('executeBtn').textContent = '🚀 Execute Multi-Agent System';
    }
}

// Handle execution started event
function handleExecutionStarted(data) {
    addTerminalLine('🚀 Multi-agent system execution started', 'info');
    addTerminalLine(`📋 Company: ${data.company_name}`, 'info');
    addTerminalLine(`💼 Industry: ${data.industry}`, 'info');
    addTerminalLine(`💰 Budget: $${data.total_budget.toLocaleString()}`, 'info');
    addTerminalLine(`📆 Timeline: ${data.target_days} days`, 'info');
    addTerminalLine('', 'info');

    currentExecution = data;
    updateProgress(0, 'Initializing CEO orchestrator...');
}

// Handle agent update
function handleAgentUpdate(data) {
    const { agent, status, message, phase } = data;

    // Update agent status badge
    updateAgentStatus(agent, status);

    // Add to terminal
    const icon = getAgentIcon(agent);
    addTerminalLine(`${icon} ${agent.toUpperCase()}: ${message}`, status);

    // Update phase if provided
    if (phase) {
        document.getElementById('currentPhase').textContent = `Current Phase: ${phase}`;
    }
}

// Handle phase update
function handlePhaseUpdate(data) {
    const { phase, progress, message } = data;

    updateProgress(progress, message || phase);
    addTerminalLine(`⚙️ Phase: ${phase}`, 'info');
}

// Handle execution complete
function handleExecutionComplete(data) {
    console.log('Execution complete data:', data);

    isExecuting = false;
    document.getElementById('executeBtn').disabled = false;
    document.getElementById('executeBtn').textContent = '🚀 Execute Multi-Agent System';

    updateProgress(100, 'Execution complete');
    addTerminalLine('', 'info');
    addTerminalLine('✅ Multi-agent system execution completed successfully', 'success');

    // Update all agents to completed status
    updateAgentStatus('ceo', 'success');
    updateAgentStatus('cfo', 'success');
    updateAgentStatus('engineer', 'success');
    updateAgentStatus('researcher', 'success');

    // Display results
    displayResults(data.result);
}

// Handle execution error
function handleExecutionError(data) {
    isExecuting = false;
    document.getElementById('executeBtn').disabled = false;
    document.getElementById('executeBtn').textContent = '🚀 Execute Multi-Agent System';

    addTerminalLine('', 'info');
    addTerminalLine(`❌ Execution failed: ${data.error}`, 'error');

    if (data.traceback) {
        addTerminalLine('Stack trace:', 'error');
        data.traceback.split('\n').forEach(line => {
            addTerminalLine(line, 'error');
        });
    }

    // Update agents to error status
    updateAgentStatus('ceo', 'error');
}

// Display execution results
function displayResults(result) {
    const resultsCard = document.getElementById('resultsCard');
    resultsCard.style.display = 'block';

    // Update metrics
    document.getElementById('completedPhases').textContent = result.completed_phases?.length || 0;
    document.getElementById('executiveDecisions').textContent = result.executive_decisions?.length || 0;
    document.getElementById('budgetRemaining').textContent =
        `$${(result.budget_remaining || 0).toLocaleString()}`;

    // Display agent summaries
    const summariesContainer = document.getElementById('agentSummaries');
    summariesContainer.innerHTML = '';

    const agentOutputs = result.agent_outputs || [];

    if (agentOutputs.length > 0) {
        // Group by unique agent
        const uniqueAgents = {};
        agentOutputs.forEach(output => {
            const agent = output.agent;
            if (!uniqueAgents[agent]) {
                uniqueAgents[agent] = output;
            }
        });

        Object.keys(uniqueAgents).forEach(agentName => {
            const output = uniqueAgents[agentName];
            const summary = output.summary || {};

            const summaryCard = document.createElement('div');
            summaryCard.style.cssText = 'padding: 1rem; background: var(--bg-tertiary); border-radius: var(--radius-lg); margin-bottom: 1rem;';

            const icon = getAgentIcon(agentName);
            const status = summary.status || 'completed';
            const findings = summary.key_findings || [];
            const recommendations = summary.recommendations || [];

            summaryCard.innerHTML = `
                <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 0.75rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="font-size: 1.5rem;">${icon}</span>
                        <h4 style="font-size: var(--text-lg); font-weight: 600; margin: 0;">${agentName.toUpperCase()}</h4>
                    </div>
                    <span class="badge badge-success">${status}</span>
                </div>
                ${findings.length > 0 ? `
                    <div style="margin-bottom: 0.75rem;">
                        <div style="font-size: var(--text-sm); font-weight: 500; color: var(--text-secondary); margin-bottom: 0.25rem;">Key Findings:</div>
                        <ul style="margin: 0; padding-left: 1.5rem; font-size: var(--text-sm); color: var(--text-tertiary);">
                            ${findings.map(f => `<li>${f}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                ${recommendations.length > 0 ? `
                    <div>
                        <div style="font-size: var(--text-sm); font-weight: 500; color: var(--text-secondary); margin-bottom: 0.25rem;">Recommendations:</div>
                        <ul style="margin: 0; padding-left: 1.5rem; font-size: var(--text-sm); color: var(--text-tertiary);">
                            ${recommendations.map(r => `<li>${r}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            `;

            summariesContainer.appendChild(summaryCard);
        });
    } else {
        summariesContainer.innerHTML = '<p style="color: var(--text-tertiary);">No agent summaries available</p>';
    }
}

// Update agent status badge
function updateAgentStatus(agent, status) {
    const statusBadge = document.getElementById(`${agent}-status`);
    if (!statusBadge) return;

    statusBadge.className = 'badge';

    switch (status) {
        case 'active':
        case 'in_progress':
            statusBadge.classList.add('badge-info');
            statusBadge.textContent = 'Active';
            break;
        case 'success':
        case 'completed':
            statusBadge.classList.add('badge-success');
            statusBadge.textContent = 'Completed';
            break;
        case 'error':
        case 'failed':
            statusBadge.classList.add('badge-error');
            statusBadge.textContent = 'Error';
            break;
        case 'warning':
            statusBadge.classList.add('badge-warning');
            statusBadge.textContent = 'Warning';
            break;
        default:
            statusBadge.classList.add('badge-info');
            statusBadge.textContent = 'Idle';
    }
}

// Update progress bar
function updateProgress(percent, phase) {
    const progressFill = document.getElementById('progressFill');
    const progressPercent = document.getElementById('progressPercent');
    const currentPhase = document.getElementById('currentPhase');

    progressFill.style.width = `${percent}%`;
    progressPercent.textContent = `${Math.round(percent)}%`;
    currentPhase.textContent = phase;
}

// Add line to terminal
function addTerminalLine(text, type = 'info') {
    const terminal = document.getElementById('executionOutput');
    const line = document.createElement('div');
    line.className = 'terminal-line';

    let color = 'var(--accent-green)';
    if (type === 'error') color = 'var(--error)';
    if (type === 'warning') color = 'var(--warning)';
    if (type === 'success') color = 'var(--success)';
    if (type === 'info') color = 'var(--accent-cyan)';

    line.style.color = color;
    line.textContent = text;

    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
}

// Get agent icon
function getAgentIcon(agent) {
    const icons = {
        'ceo': '👔',
        'cfo': '💰',
        'engineer': '🛠️',
        'researcher': '🔍',
        'legal': '⚖️',
        'martech': '📱',
        'software_engineering': '🛠️',
        'security': '🛡️',
        'branding': '🎨',
        'ux_ui': '✨'
    };
    return icons[agent.toLowerCase()] || '🤖';
}

// Reset form
function resetForm() {
    if (isExecuting) {
        if (!confirm('An execution is in progress. Are you sure you want to reset?')) {
            return;
        }
    }

    const defaults = getDefaultScenario();
    applyScenarioToForm(defaults);
    document.getElementById('threadId').value = '';
    saveScenarioToLocal(defaults, { source: 'reset_defaults', userModified: false });
    syncScenarioToBackend(defaults);

    document.getElementById('progressCard').style.display = 'none';
    document.getElementById('outputCard').style.display = 'none';
    document.getElementById('resultsCard').style.display = 'none';

    updateAgentStatus('ceo', 'idle');
    updateAgentStatus('cfo', 'idle');
    updateAgentStatus('engineer', 'idle');
    updateAgentStatus('researcher', 'idle');

    isExecuting = false;
    document.getElementById('executeBtn').disabled = false;
    document.getElementById('executeBtn').textContent = '🚀 Execute Multi-Agent System';
}

// Download report
function downloadReport() {
    if (!currentExecution) {
        alert('No execution data available');
        return;
    }

    // Create report content
    const reportData = {
        execution_id: currentExecution.thread_id || 'unknown',
        timestamp: new Date().toISOString(),
        company: document.getElementById('companyName').value,
        industry: getSelectedIndustry(),
        results: currentExecution
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `execution-report-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// View logs
function viewLogs() {
    window.open('/api/logs', '_blank');
}

// Show documentation
function showDocs() {
    window.open('/docs', '_blank');
}
