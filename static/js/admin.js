// CEO Agent Admin Dashboard JavaScript

// Global state
const state = {
    socket: null,
    agents: [],
    approvals: [],
    activities: [],
    uptime: 0,
    uptimeInterval: null,
    currentSection: 'dashboard'
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeSocket();
    initializeNavigation();
    loadAgents();
    startUptimeCounter();
    setupEventListeners();
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
    const agentsData = [
        {
            id: 'ceo',
            name: 'CEO Agent',
            icon: '👔',
            status: 'active',
            description: 'Executive orchestrator making strategic decisions within guard rails',
            tasksCompleted: 0,
            successRate: 100,
            budget: 50000
        },
        {
            id: 'cfo',
            name: 'CFO Agent',
            icon: '💰',
            status: 'active',
            description: 'Financial oversight and budget management',
            tasksCompleted: 0,
            successRate: 100,
            budget: 970
        },
        {
            id: 'brand',
            name: 'Brand Agent',
            icon: '🎨',
            status: 'training',
            description: 'Brand strategy, design, and visual content creation',
            tasksCompleted: 0,
            successRate: 0,
            budget: 4500
        },
        {
            id: 'legal',
            name: 'Legal Agent',
            icon: '⚖️',
            status: 'training',
            description: 'Legal research and document preparation (Ohio)',
            tasksCompleted: 0,
            successRate: 0,
            budget: 3000
        },
        {
            id: 'martech',
            name: 'MarTech Agent',
            icon: '📱',
            status: 'training',
            description: 'Marketing automation, analytics, and customer engagement',
            tasksCompleted: 0,
            successRate: 0,
            budget: 6500
        },
        {
            id: 'ux-ui',
            name: 'UX/UI Agent',
            icon: '✨',
            status: 'training',
            description: 'User experience design and interface optimization',
            tasksCompleted: 0,
            successRate: 0,
            budget: 5000
        }
    ];

    state.agents = agentsData;
    renderAgents();
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
                <button class="agent-btn" onclick="viewAgentDetails('${agent.id}')">View</button>
                <button class="agent-btn primary" onclick="interactWithAgent('${agent.id}')">Interact</button>
            </div>
        </div>
    `).join('');
}

function viewAgentDetails(agentId) {
    const agent = state.agents.find(a => a.id === agentId);
    if (!agent) return;

    showToast(`Viewing ${agent.name} details`, 'info');
    // TODO: Show detailed modal
}

function interactWithAgent(agentId) {
    const agent = state.agents.find(a => a.id === agentId);
    if (!agent) return;

    switchSection('training');
    showToast(`Opening training session with ${agent.name}`, 'info');
}

// CEO Strategic Analysis
function startCEOAnalysis() {
    addActivity({
        icon: '🎯',
        message: 'Starting CEO strategic analysis...',
        time: new Date().toISOString()
    });

    showToast('CEO Agent analyzing strategic objectives', 'info');

    // Send analysis request to backend
    fetch('/api/ceo/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            objective: 'Analyze current business objectives and deploy specialized agents',
            budget: 50000,
            constraints: ['financial_safety', 'user_approval_required']
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

    showToast('CEO Strategic Analysis Complete', 'success');
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

    messageEl.innerHTML = prefix + message;
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
    showToast(`Generating ${reportType} report...`, 'info');

    const viewer = document.getElementById('report-viewer');
    const title = document.getElementById('report-title');
    const content = document.getElementById('report-content');

    // Map report types to API endpoints
    const reportEndpoints = {
        'ceo': { endpoint: '/api/reports/strategic', method: 'POST', title: 'CEO Strategic Report' },
        'cfo': { endpoint: '/api/reports/financial', method: 'POST', title: 'CFO Financial Report' },
        'agent-performance': { endpoint: '/api/reports/training', method: 'GET', title: 'Agent Performance Report' },
        'training-progress': { endpoint: '/api/reports/research', method: 'GET', title: 'Training & Research Report' }
    };

    const reportConfig = reportEndpoints[reportType];
    if (!reportConfig) {
        showToast('Unknown report type', 'error');
        return;
    }

    // Prepare company info for POST requests
    const companyInfo = {
        name: 'CEO Agent Platform',
        industry: 'AI Technology',
        stage: 'Early Stage',
        team_size: 'Small (1-10)',
        monthly_revenue: 10000,
        monthly_expenses: 45000,
        available_cash: 200000
    };

    // Make API call
    const fetchOptions = {
        method: reportConfig.method,
        headers: { 'Content-Type': 'application/json' }
    };

    if (reportConfig.method === 'POST') {
        fetchOptions.body = JSON.stringify(companyInfo);
    }

    fetch(reportConfig.endpoint, fetchOptions)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                title.textContent = reportConfig.title;
                content.innerHTML = renderComprehensiveReport(data.report, reportType);
                viewer.style.display = 'flex';

                addActivity({
                    icon: '📊',
                    message: `Generated ${reportConfig.title} - ${data.report.report_id}`,
                    time: new Date().toISOString()
                });
            } else {
                showToast('Error generating report: ' + data.error, 'error');
            }
        })
        .catch(error => {
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
            title.textContent = report.title;
            content.innerHTML = report.content;
            viewer.style.display = 'flex';
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
window.resetSettings = resetSettings;
window.saveSettings = saveSettings;
