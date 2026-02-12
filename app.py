"""
CEO Agent - Executive AI System
Flask backend serving admin dashboard and multi-agent orchestration
"""

from flask import Flask, render_template, jsonify, request, session
from flask_socketio import SocketIO, emit
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any
import threading
import time
import traceback
from functools import wraps

# Import agent systems - CEO Agent (new architecture)
try:
    from agents.ceo_agent import CEOAgentState, analyze_strategic_objectives as ceo_analyze
    from agents.new_cfo_agent import CFOAgentState as NewCFOState, generate_financial_report
    CEO_AGENT_AVAILABLE = True
except ImportError:
    CEO_AGENT_AVAILABLE = False
    print("⚠️ CEO/CFO agents not available, using fallback")

# Backward compatibility with old CFO agent
from agents.cfo_agent import CFOAgentState, analyze_strategic_objectives, deploy_specialized_agents
from agents.specialized_agents import AgentFactory
from agents.agent_guard_rails import AgentGuardRail, AgentDomain, create_execution_summary

# Import utilities
try:
    from utils.logger import get_logger, app_logger, api_logger
    from utils.validators import validate_company_info, validate_agent_request, sanitize_input
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
    print("⚠️ Warning: Utils modules not available, using basic logging")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ceo-agent-executive-ai-2026')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max request size
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state for admin dashboard
pending_approvals = []
system_settings = {
    'system_mode': 'training',
    'auto_approve_api': True,
    'email_notifications': False,
    'total_budget': 50000,
    'cfo_api_limit': 100,
    'cfo_legal_limit': 500
}

# Initialize logger
if UTILS_AVAILABLE:
    logger = get_logger('app', 'logs/app.log')
else:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('app')

# Store active sessions and agent states
active_sessions = {}


# Error handler decorator
def handle_errors(f):
    """Decorator for consistent error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            duration = (time.time() - start_time) * 1000
            
            if UTILS_AVAILABLE:
                api_logger.api_request(
                    request.method,
                    request.path,
                    200,
                    duration
                )
            
            return result
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_msg = str(e)
            trace = traceback.format_exc()
            
            if UTILS_AVAILABLE:
                logger.error(f"Error in {f.__name__}: {error_msg}", exc_info=True)
                api_logger.api_request(
                    request.method,
                    request.path,
                    500,
                    duration
                )
            else:
                print(f"❌ Error in {f.__name__}: {error_msg}")
                print(trace)
            
            return jsonify({
                'success': False,
                'error': error_msg,
                'message': 'An error occurred processing your request'
            }), 500
    return decorated_function


@app.route('/')
def index():
    """Main dashboard page (legacy)"""
    if UTILS_AVAILABLE:
        logger.info('Legacy dashboard page accessed')
    return render_template('index.html')


@app.route('/admin')
def admin_dashboard():
    """CEO Agent Admin Dashboard - Primary interface"""
    if UTILS_AVAILABLE:
        logger.info('Admin dashboard accessed')
    return render_template('admin_dashboard.html')


@app.route('/debug')
def debug():
    """Debug console page"""
    return render_template('debug.html')


@app.route('/test')
def test_frontend():
    """Test page for button functionality"""
    with open('test_frontend.html', 'r') as f:
        return f.read()


@app.route('/api/agents/available')
def get_available_agents():
    """Get list of available specialized agents"""
    factory = AgentFactory()
    agents = []
    
    for agent_type in factory.get_available_agents():
        try:
            agent = factory.create_agent(agent_type)
            guard_rail = AgentGuardRail(AgentDomain[agent_type.upper()])
            
            agents.append({
                'type': agent_type,
                'name': agent.name,
                'capabilities': agent.capabilities,
                'budget': guard_rail.budget_constraint.max_budget if guard_rail.budget_constraint else 0,
                'status': 'available'
            })
        except Exception as e:
            print(f"Error loading agent {agent_type}: {e}")
    
    return jsonify({'agents': agents})


@app.route('/api/ceo/analyze', methods=['POST'])
@app.route('/api/cfo/analyze', methods=['POST'])  # Backward compatibility
def analyze_objectives():
    """Analyze strategic objectives with CEO/CFO agent"""
    try:
        data = request.json
        print(f"📊 CEO Analysis request received: {data}")
        print(f"📊 Data type: {type(data)}")
        print(f"📊 Data keys: {data.keys() if data else 'None'}")
        
        # Create initial state matching CFOAgentState schema
        state = {
            # Top-level company info (not nested)
            'company_name': data.get('company_name', 'Amazon Granite LLC'),
            'industry': data.get('industry', 'Granite & Countertops'),
            'location': data.get('location', 'Cincinnati, Ohio'),
            
            # Strategic objectives
            'strategic_objectives': data.get('objectives', [
                f"Launch {data.get('company_name', 'business')} with digital presence",
                "Build brand identity and market positioning"
            ]),
            
            # Budget management
            'total_budget': float(data.get('budget', 5000)),
            'budget_allocated': {},
            'budget_spent': {},
            'budget_remaining': float(data.get('budget', 5000)),
            
            # Timeline
            'target_completion_days': int(data.get('timeline', 90)),
            'current_day': 0,
            'milestones': [],
            
            # Multi-agent orchestration
            'active_agents': [],
            'agent_outputs': [],
            'agent_status': {},
            
            # Task breakdown
            'identified_tasks': [],
            'assigned_tasks': {},
            'completed_tasks': [],
            
            # Risk management
            'risks': [],
            'opportunities': [],
            
            # Deliverables
            'deliverables': [],
            'status_reports': [],
            'final_executive_summary': '',
            
            # Workflow
            'current_phase': 'initialization',
            'completed_phases': []
        }
        
        print(f"🔄 Running CFO strategic analysis...")
        
        # Run strategic analysis
        result = analyze_strategic_objectives(state)
        
        print(f"✅ Analysis complete. Tasks: {len(result.get('identified_tasks', []))}")
        
        return jsonify({
            'success': True,
            'tasks': result.get('identified_tasks', []),
            'budget_allocation': result.get('budget_allocated', {}),
            'risks': result.get('risks', []),
            'timeline': result.get('target_completion_days', 90)
        })
    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/agent/execute/<agent_type>', methods=['POST'])
def execute_agent(agent_type):
    """Execute a specific specialized agent"""
    data = request.json
    
    try:
        factory = AgentFactory()
        agent = factory.create_agent(agent_type)
        
        # Ensure company_info has the required fields
        company_info = data.get('company_info', {})
        if not company_info.get('name'):
            company_info['name'] = company_info.get('company_name', 'Company')
        if not company_info.get('dba_name'):
            company_info['dba_name'] = company_info.get('name', 'Company')
        if not company_info.get('industry'):
            company_info['industry'] = 'General Business'
        if not company_info.get('location'):
            company_info['location'] = 'United States'
        
        # Execute based on agent type
        result = {
            'agent_type': agent_type,
            'agent_name': agent.name,
            'status': 'executed',
            'timestamp': datetime.now().isoformat(),
            'execution_mode': 'AI_PERFORMED'
        }
        
        # Add agent-specific execution
        if agent_type == 'branding' and hasattr(agent, 'design_concepts'):
            state = {
                'task_description': data.get('task', 'Design brand identity'),
                'company_info': company_info,
                'research_findings': [],
                'design_concepts': [],
                'recommendations': [],
                'deliverables': [],
                'status': 'initializing',
                'budget_used': 0,
                'timeline_days': 30
            }
            concepts_result = agent.design_concepts(state)
            result['deliverables'] = concepts_result.get('deliverables', [])
            result['budget_used'] = concepts_result.get('budget_used', 0)
            
        elif agent_type == 'web_development' and hasattr(agent, 'analyze_requirements'):
            state = {
                'task_description': data.get('task', 'Build website with AR'),
                'requirements': data.get('requirements', company_info),
                'tech_stack': [],
                'architecture_design': '',
                'ar_features': [],
                'development_phases': [],
                'testing_results': [],
                'deliverables': [],
                'status': 'initializing',
                'budget_used': 0,
                'timeline_days': 60
            }
            web_result = agent.analyze_requirements(state)
            result['tech_stack'] = web_result.get('tech_stack', [])
            result['deliverables'] = web_result.get('deliverables', [])
            result['timeline'] = web_result.get('development_phases', [])
            result['budget_used'] = web_result.get('budget_used', 0)
            
        elif agent_type == 'martech' and hasattr(agent, 'configure_stack'):
            state = {
                'task_description': data.get('task', 'Configure marketing tech stack'),
                'current_systems': [],
                'recommended_stack': [],
                'integrations': [],
                'automation_workflows': [],
                'implementation_plan': '',
                'status': 'initializing',
                'budget_used': 0,
                'timeline_days': 30
            }
            martech_result = agent.configure_stack(state)
            result['tech_stack'] = martech_result.get('recommended_stack', [])
            result['deliverables'] = [
                f"✅ {tool.get('tool', 'Tool')}: {tool.get('ai_configures', 'Configured')}"
                for tool in martech_result.get('recommended_stack', [])
            ]
            result['budget_used'] = martech_result.get('budget_used', 0)
            
        elif agent_type == 'content' and hasattr(agent, 'produce_content'):
            state = {
                'task_description': data.get('task', 'Create marketing content'),
                'content_types': [],
                'production_schedule': [],
                'assets_created': [],
                'distribution_plan': '',
                'seo_strategy': '',
                'status': 'initializing',
                'budget_used': 0,
                'timeline_days': 30
            }
            content_result = agent.produce_content(state)
            result['deliverables'] = content_result.get('assets_created', [])
            result['budget_used'] = content_result.get('budget_used', 0)
            
        elif agent_type == 'campaigns' and hasattr(agent, 'launch_campaigns'):
            state = {
                'task_description': data.get('task', 'Launch advertising campaigns'),
                'channels': [],
                'audience_targeting': [],
                'creative_assets': [],
                'budget_allocation': [],
                'performance_metrics': [],
                'status': 'initializing',
                'budget_used': 0,
                'timeline_days': 30
            }
            campaign_result = agent.launch_campaigns(state)
            result['timeline'] = campaign_result.get('creative_concepts', [])
            result['deliverables'] = [
                concept.get('ai_creates', 'Campaign created')
                for concept in campaign_result.get('creative_concepts', [])
            ]
            result['budget_used'] = campaign_result.get('budget_used', 0)
        
        elif agent_type == 'legal' and hasattr(agent, 'dba_registration_process'):
            state = {
                'task_description': data.get('task', 'Legal compliance and filing'),
                'jurisdiction': company_info.get('location', 'United States'),
                'filings_required': [],
                'compliance_checklist': [],
                'documents_prepared': [],
                'risks_identified': [],
                'status': 'initializing',
                'budget_used': 0,
                'timeline_days': 14
            }
            legal_result = agent.dba_registration_process(state)
            result['deliverables'] = legal_result.get('documents_prepared', [])
            result['budget_used'] = legal_result.get('budget_used', 0)
        
        # Ensure all results have deliverables (fallback for agents without proper execution)
        if 'deliverables' not in result or not result.get('deliverables'):
            result['deliverables'] = [
                f"✅ {agent.name} execution completed",
                f"📋 Task: {data.get('task', 'Agent task execution')}",
                f"🏢 Company: {company_info.get('company_name', 'N/A')}"
            ]
        if 'budget_used' not in result:
            result['budget_used'] = agent.budget if hasattr(agent, 'budget') else 0
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/guard-rails/<agent_type>')
def get_guard_rails(agent_type):
    """Get guard rail information for an agent"""
    try:
        print(f"🛡️ Guard rails request for: {agent_type}")
        
        # Map agent_type to AgentDomain enum
        domain_map = {
            'branding': 'BRANDING',
            'web_development': 'WEB_DEVELOPMENT',
            'legal': 'LEGAL',
            'martech': 'MARTECH',
            'content': 'CONTENT',
            'campaigns': 'CAMPAIGNS'
        }
        
        domain_name = domain_map.get(agent_type.lower(), agent_type.upper())
        domain = AgentDomain[domain_name]
        
        summary = create_execution_summary(domain)
        guard_rail = AgentGuardRail(domain)
        
        print(f"✅ Guard rails loaded for {agent_type}")
        
        return jsonify({
            'success': True,
            'guard_rail': {
                'summary': summary,
                'max_budget': guard_rail.budget_constraint.max_budget if guard_rail.budget_constraint else 0,
                'allowed_categories': guard_rail.budget_constraint.allowed_categories if guard_rail.budget_constraint else [],
                'forbidden_categories': guard_rail.budget_constraint.forbidden_categories if guard_rail.budget_constraint else [],
                'permitted_tasks': guard_rail.scope_constraint.permitted_tasks if guard_rail.scope_constraint else [],
                'quality_standards': guard_rail.quality_standard.metrics if guard_rail.quality_standard else {}
            }
        })
    except Exception as e:
        print(f"❌ Guard rails error for {agent_type}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# CEO AGENT ADMIN API ENDPOINTS
# ============================================================================

@app.route('/api/approvals/pending', methods=['GET'])
def get_pending_approvals():
    """Get all pending payment approvals"""
    return jsonify({
        'success': True,
        'approvals': pending_approvals,
        'count': len(pending_approvals)
    })


@app.route('/api/approval/<approval_id>/approve', methods=['POST'])
def approve_payment(approval_id):
    """Approve a payment request"""
    global pending_approvals
    
    approval = next((a for a in pending_approvals if a['id'] == approval_id), None)
    if not approval:
        return jsonify({'success': False, 'error': 'Approval not found'}), 404
    
    # Remove from pending
    pending_approvals = [a for a in pending_approvals if a['id'] != approval_id]
    
    # Emit update via SocketIO
    socketio.emit('approval_approved', {
        'id': approval_id,
        'approval': approval,
        'timestamp': datetime.now().isoformat()
    })
    
    if UTILS_AVAILABLE:
        logger.info(f'Payment approved: {approval_id} - ${approval.get("amount", 0)}')
    
    return jsonify({
        'success': True,
        'message': 'Payment approved',
        'approval': approval
    })


@app.route('/api/approval/<approval_id>/reject', methods=['POST'])
def reject_payment(approval_id):
    """Reject a payment request"""
    global pending_approvals
    
    approval = next((a for a in pending_approvals if a['id'] == approval_id), None)
    if not approval:
        return jsonify({'success': False, 'error': 'Approval not found'}), 404
    
    # Remove from pending
    pending_approvals = [a for a in pending_approvals if a['id'] != approval_id]
    
    # Emit update via SocketIO
    socketio.emit('approval_rejected', {
        'id': approval_id,
        'approval': approval,
        'timestamp': datetime.now().isoformat()
    })
    
    if UTILS_AVAILABLE:
        logger.info(f'Payment rejected: {approval_id} - ${approval.get("amount", 0)}')
    
    return jsonify({
        'success': True,
        'message': 'Payment rejected',
        'approval': approval
    })


@app.route('/api/reports/strategic', methods=['POST'])
def generate_strategic_report():
    """Generate comprehensive strategic report with 30/60/90 day plans"""
    try:
        from services.report_service import report_service
        
        company_info = request.json or {}
        report = report_service.generate_strategic_report(company_info)
        
        # Emit update via SocketIO
        socketio.emit('report_generated', {
            'report_id': report['report_id'],
            'report_type': 'strategic',
            'timestamp': datetime.now().isoformat()
        })
        
        if UTILS_AVAILABLE:
            logger.info(f'Strategic report generated: {report["report_id"]}')
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f'Error generating strategic report: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reports/financial', methods=['POST'])
def generate_financial_report_endpoint():
    """Generate comprehensive financial report with projections"""
    try:
        from services.report_service import report_service
        
        company_info = request.json or {}
        report = report_service.generate_financial_report(company_info)
        
        # Emit update via SocketIO
        socketio.emit('report_generated', {
            'report_id': report['report_id'],
            'report_type': 'financial',
            'timestamp': datetime.now().isoformat()
        })
        
        if UTILS_AVAILABLE:
            logger.info(f'Financial report generated: {report["report_id"]}')
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f'Error generating financial report: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reports/training', methods=['GET'])
def generate_training_report_endpoint():
    """Generate training progress report"""
    try:
        from services.report_service import report_service
        
        report = report_service.generate_training_report()
        
        # Emit update via SocketIO
        socketio.emit('report_generated', {
            'report_id': report['report_id'],
            'report_type': 'training',
            'timestamp': datetime.now().isoformat()
        })
        
        if UTILS_AVAILABLE:
            logger.info(f'Training report generated: {report["report_id"]}')
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f'Error generating training report: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reports/research', methods=['GET'])
def generate_research_report_endpoint():
    """Generate research findings report"""
    try:
        from services.report_service import report_service
        
        report = report_service.generate_research_report()
        
        # Emit update via SocketIO
        socketio.emit('report_generated', {
            'report_id': report['report_id'],
            'report_type': 'research',
            'timestamp': datetime.now().isoformat()
        })
        
        if UTILS_AVAILABLE:
            logger.info(f'Research report generated: {report["report_id"]}')
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f'Error generating research report: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reports/history', methods=['GET'])
def get_report_history():
    """Get all historical reports"""
    try:
        from services.report_service import report_service
        
        history = report_service.get_report_history()
        
        return jsonify({
            'success': True,
            'reports': history,
            'count': len(history)
        })
        
    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f'Error retrieving report history: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reports/<report_id>', methods=['GET'])
def get_report_by_id(report_id):
    """Get specific report by ID"""
    try:
        from services.report_service import report_service
        
        report = report_service.get_report_by_id(report_id)
        
        if report is None:
            return jsonify({
                'success': False,
                'error': 'Report not found'
            }), 404
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f'Error retrieving report: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cfo/report', methods=['GET'])
def get_cfo_report():
    """Get CFO financial report"""
    try:
        if CEO_AGENT_AVAILABLE:
            # Use new CFO agent
            state = {
                'tracked_spending': {},
                'api_budget_allocated': system_settings['cfo_api_limit'],
                'legal_budget_allocated': system_settings['cfo_legal_limit'],
                'budget_alerts': [],
                'payment_requests': pending_approvals,
                'financial_insights': [],
                'recommendations': []
            }
            report = generate_financial_report(state)
            return jsonify({'success': True, 'report': report})
        else:
            # Fallback report
            return jsonify({
                'success': True,
                'report': {
                    'total_budget': system_settings['total_budget'],
                    'cfo_managed': system_settings['cfo_api_limit'] + system_settings['cfo_legal_limit'],
                    'user_approval_required': system_settings['total_budget'] - (system_settings['cfo_api_limit'] + system_settings['cfo_legal_limit']),
                    'pending_approvals': len(pending_approvals)
                }
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings/update', methods=['POST'])
def update_settings():
    """Update system settings"""
    global system_settings
    
    try:
        data = request.json
        
        # Update settings
        if 'systemMode' in data:
            system_settings['system_mode'] = data['systemMode']
        if 'autoApproveAPI' in data:
            system_settings['auto_approve_api'] = data['autoApproveAPI']
        if 'emailNotifications' in data:
            system_settings['email_notifications'] = data['emailNotifications']
        if 'totalBudget' in data:
            system_settings['total_budget'] = float(data['totalBudget'])
        if 'cfoAPILimit' in data:
            system_settings['cfo_api_limit'] = float(data['cfoAPILimit'])
        if 'cfoLegalLimit' in data:
            system_settings['cfo_legal_limit'] = float(data['cfoLegalLimit'])
        
        if UTILS_AVAILABLE:
            logger.info(f'Settings updated: {system_settings}')
        
        return jsonify({
            'success': True,
            'settings': system_settings
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/research/start', methods=['POST'])
def start_research():
    """Start research session"""
    data = request.json or {}
    
    # Simulate research findings
    socketio.emit('research_update', {
        'title': 'AI Tool Discovery',
        'description': 'Found new cost-effective API alternatives',
        'tags': ['API', 'Cost Optimization'],
        'timestamp': datetime.now().isoformat()
    })
    
    return jsonify({'success': True, 'message': 'Research started'})


# ============================================================================
# WEBSOCKET HANDLERS - Chat & Real-time Updates
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    if UTILS_AVAILABLE:
        logger.info(f'Client connected: {request.sid}')
    emit('connected', {
        'message': 'Connected to CEO Agent Executive AI System',
        'timestamp': datetime.now().isoformat(),
        'session_id': request.sid,
        'mode': system_settings['system_mode']
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    if UTILS_AVAILABLE:
        logger.info(f'Client disconnected: {request.sid}')


@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle incoming chat messages"""
    try:
        message = data.get('message', '').strip()
        sender = data.get('sender', 'user')
        
        if UTILS_AVAILABLE:
            logger.info(f'Chat message from {sender}: {message[:100]}...')
            
            # Validate message
            validation = validate_chat_message(data)
            if not validation.valid:
                emit('chat_error', {
                    'errors': validation.errors,
                    'timestamp': datetime.now().isoformat()
                })
                return
        
        # Sanitize input
        if UTILS_AVAILABLE:
            message = sanitize_input(message, max_length=5000)
        
        # Echo message back to all clients
        emit('chat_message', {
            'message': message,
            'sender': sender,
            'timestamp': datetime.now().isoformat()
        }, broadcast=True)
        
        # Process commands if from user
        if sender == 'user':
            response = process_chat_command(message)
            if response:
                socketio.emit('chat_message', {
                    'message': response,
                    'sender': 'assistant',
                    'timestamp': datetime.now().isoformat()
                }, broadcast=True)
                
    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f'Error handling chat message: {str(e)}', exc_info=True)
        emit('chat_error', {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })


def process_chat_command(message: str) -> str:
    """Process chat commands and return response"""
    lower_msg = message.lower()
    
    # Status query
    if 'status' in lower_msg:
        return "System is operational. All agents are ready for execution."
    
    # Budget query
    if 'budget' in lower_msg:
        return "Total budget: $5,000. Use the dashboard to track spending."
    
    # Agent list
    if 'agent' in lower_msg and ('list' in lower_msg or 'available' in lower_msg):
        return "Available agents: Branding, Web Development, Legal, MarTech, Content, Campaigns"
    
    return None


@socketio.on('agent_status_update')
def handle_agent_status(data):
    """Handle agent status updates"""
    try:
        agent_type = data.get('agent_type')
        status = data.get('status')
        
        if UTILS_AVAILABLE:
            logger.info(f'Agent status update: {agent_type} - {status}')
        
        emit('agent_status_update', {
            'agent_type': agent_type,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }, broadcast=True)
        
    except Exception as e:
        if UTILS_AVAILABLE:
            logger.error(f'Error handling agent status: {str(e)}', exc_info=True)


@socketio.on('execute_full_orchestration')
def handle_full_orchestration(data):
    """Execute full CFO orchestration in background"""
    if UTILS_AVAILABLE:
        logger.info(f'Full orchestration request received: {data}')
    else:
        print(f"🚀 Full orchestration request received: {data}")
    
    def run_orchestration():
        try:
            print("📡 Emitting orchestration_started")
            socketio.emit('orchestration_started', {'timestamp': datetime.now().isoformat()}, to=None)
            
            # Create state matching CFOAgentState schema
            company_info = data.get('company_info', {})
            state = {
                # Top-level company info (extract from company_info object)
                'company_name': company_info.get('company_name') or company_info.get('name', 'Amazon Granite LLC'),
                'industry': company_info.get('industry', 'Granite & Countertops'),
                'location': company_info.get('location', 'Cincinnati, Ohio'),
                
                # Strategic objectives
                'strategic_objectives': data.get('objectives', []),
                
                # Budget management
                'total_budget': 5000.0,
                'budget_allocated': {},
                'budget_spent': {},
                'budget_remaining': 5000.0,
                
                # Timeline
                'target_completion_days': 90,
                'current_day': 0,
                'milestones': [],
                
                # Multi-agent orchestration
                'active_agents': [],
                'agent_outputs': [],
                'agent_status': {},
                
                # Task breakdown
                'identified_tasks': [],
                'assigned_tasks': {},
                'completed_tasks': [],
                
                # Risk management
                'risks': [],
                'opportunities': [],
                
                # Deliverables
                'deliverables': [],
                'status_reports': [],
                'final_executive_summary': '',
                
                # Workflow
                'current_phase': 'initialization',
                'completed_phases': []
            }
            
            print("🔄 Running strategic analysis phase...")
            # Analyze objectives
            socketio.emit('phase', {'name': 'Strategic Analysis', 'status': 'running'}, to=None)
            state = analyze_strategic_objectives(state)
            socketio.emit('phase', {'name': 'Strategic Analysis', 'status': 'complete', 'tasks': state.get('identified_tasks', [])}, to=None)
            print(f"✅ Strategic analysis complete. Tasks: {len(state.get('identified_tasks', []))}")
            
            # Deploy agents
            print("🤖 Deploying agents...")
            socketio.emit('phase', {'name': 'Agent Deployment', 'status': 'running'}, to=None)
            
            for task in state.get('identified_tasks', [])[:3]:  # Deploy first 3 for demo
                agent_type = task.get('required_expertise', '').lower()
                print(f"  - Deploying {agent_type} agent")
                socketio.emit('agent_deploying', {'agent': agent_type, 'task': task.get('task_id')}, to=None)
                time.sleep(1)  # Simulate processing
                socketio.emit('agent_deployed', {'agent': agent_type, 'status': 'success'}, to=None)
            
            print("✅ Orchestration complete")
            socketio.emit('orchestration_complete', {
                'status': 'success',
                'budget_used': sum(state.get('budget_allocated', {}).values()),
                'timestamp': datetime.now().isoformat()
            }, to=None)
            
        except Exception as e:
            print(f"❌ Orchestration error: {str(e)}")
            import traceback
            traceback.print_exc()
            socketio.emit('orchestration_error', {'error': str(e)}, to=None)
    
    thread = threading.Thread(target=run_orchestration)
    thread.start()
    print("🔄 Orchestration thread started")


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("\n" + "="*80)
    print("� CEO AGENT - EXECUTIVE AI SYSTEM")
    print("="*80)
    print("\n📱 Starting web server...")
    print("🌐 Admin Dashboard:  http://localhost:5001/admin")
    print("   Legacy Dashboard: http://localhost:5001")
    print("   Alternative:      http://127.0.0.1:5001/admin")
    print("\n💡 Features:")
    print("   • Executive Admin Dashboard")
    print("   • CEO Strategic Decision-Making")
    print("   • CFO Financial Oversight")
    print("   • Payment Approval Workflow")
    print("   • Agent Training Interface")
    print("   • Daily Research & Evolution")
    print("   • Real-time Budget Tracking")
    print("   • Financial Guard Rails")
    print("\n⚙️  System Mode: TRAINING")
    print("   🎓 Agents in development - train before production")
    print("\n⚠️  Development Server Active")
    print("   For production, use: gunicorn -w 4 -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker app:app")
    print("\n🛑 Press CTRL+C to stop")
    print("="*80 + "\n")
    
    socketio.run(app, debug=False, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)
