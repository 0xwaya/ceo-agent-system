// Multi-Agent System Dashboard JavaScript

// Initialize Socket.IO connection
let socket;

// State management
const state = {
    agents: [],
    tasks: [],
    budget: {
        total: 5000,
        remaining: 5000,
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

    console.log('✅ Dashboard initialized');
});

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
        addChatMessage('🌐 Connected to CFO Catalyst server. Real-time updates enabled.', 'system');
    });

    socket.on('disconnect', () => {
        console.log('⚠️ Socket.IO disconnected');
        addLogEntry('Disconnected from server', 'warning');
        addChatMessage('⚠️ Disconnected from server. Attempting to reconnect...', 'system');
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
        updateStatus('Orchestration complete! All agents executed successfully.', 'success');
        addLogEntry(`Total budget used: $${data.budget_used}`, 'success');
        updateProgress(100);

        // Chat notification - orchestration complete
        addChatMessage(`🎉 Full orchestration complete! Total budget used: $${data.budget_used}. All deliverables generated successfully.`, 'assistant');

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
        'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
        'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
        'linear-gradient(135deg, #30cfd0 0%, #330867 100%)'
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

        const companyInfo = {
            company_name: document.getElementById('companyName').value,
            dba_name: document.getElementById('dbaName').value,
            industry: document.getElementById('industry').value,
            location: document.getElementById('location').value,
            budget: parseFloat(document.getElementById('budget').value),
            timeline: parseInt(document.getElementById('timeline').value)
        };

        console.log('Company Info:', companyInfo);

        // Chat notification - analysis starting
        addChatMessage(`🔍 Starting strategic analysis for ${companyInfo.company_name}...`, 'system');

        const response = await fetch('/api/cfo/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(companyInfo)
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
            displayAnalysisReport(companyInfo, data);

            // Chat notification - analysis complete
            addChatMessage(`✅ Analysis complete! Identified ${data.tasks.length} tasks across ${Object.keys(data.budget_allocation).length} domains. Budget allocated accordingly.`, 'assistant');
        } else {
            updateStatus(`Error: ${data.error}`, 'error');
            addLogEntry(`Analysis failed: ${data.error}`, 'error');
            addChatMessage(`❌ Analysis failed: ${data.error}`, 'error');
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
        const companyInfo = {
            company_name: document.getElementById('companyName').value,
            dba_name: document.getElementById('dbaName').value,
            industry: document.getElementById('industry').value,
            location: document.getElementById('location').value
        };

        const objectives = [
            `File DBA registration for ${companyInfo.dba_name}`,
            'Engage branding agency for logo/visual identity',
            'Develop website with AR integration',
            'Set up marketing technology stack',
            'Create foundational content',
            'Launch Phase 1 campaigns within 90 days'
        ];

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
        const companyInfo = {
            company_name: document.getElementById('companyName').value,
            name: document.getElementById('companyName').value,
            dba_name: document.getElementById('dbaName').value,
            industry: document.getElementById('industry').value,
            location: document.getElementById('location').value
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
                <p>${resultData.recommendations}</p>
            </div>
        ` : ''}
        
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
        
        ${resultData.recommendations ? `
            <div class="report-section">
                <h4>💡 Recommendations</h4>
                <p style="color: #f1f5f9; line-height: 1.8;">${resultData.recommendations}</p>
            </div>
        ` : ''}
        
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

// Format chat message (preserve line breaks, add styling)
function formatChatMessage(text, type) {
    if (type === 'user') {
        return text;
    }

    // Convert line breaks to <br>
    text = text.replace(/\n/g, '<br>');

    // Add icons for certain keywords
    text = text.replace(/✓/g, '<span style="color: #2ecc71;">✓</span>');
    text = text.replace(/⚙️/g, '<span class="pulsing">⚙️</span>');

    return text;
}

// Set chat status
function setChatStatus(status) {
    const statusElement = document.getElementById('chatStatus');
    if (!statusElement) return;

    if (status === 'typing') {
        statusElement.innerHTML = `
            <div class="chat-typing">
                <span>CFO Catalyst is typing</span>
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
