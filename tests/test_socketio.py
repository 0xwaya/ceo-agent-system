"""Test SocketIO orchestration"""
import socketio
import time

# Create Socket.IO client
sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('✅ Connected to server')

@sio.on('disconnect')
def on_disconnect():
    print('❌ Disconnected from server')

@sio.on('orchestration_started')
def on_orchestration_started(data):
    print(f'🚀 Orchestration started: {data}')

@sio.on('phase')
def on_phase(data):
    print(f'📊 Phase: {data["name"]} - {data["status"]}')
    if data.get('tasks'):
        print(f'   Tasks: {len(data["tasks"])}')

@sio.on('agent_deploying')
def on_agent_deploying(data):
    print(f'🤖 Deploying {data["agent"]} agent for task {data["task"]}')

@sio.on('agent_deployed')
def on_agent_deployed(data):
    print(f'✅ Agent deployed: {data["agent"]} - {data["status"]}')

@sio.on('orchestration_complete')
def on_orchestration_complete(data):
    print(f'🎉 Orchestration complete!')
    print(f'   Budget used: ${data["budget_used"]}')
    print(f'   Timestamp: {data["timestamp"]}')

@sio.on('orchestration_error')
def on_orchestration_error(data):
    print(f'❌ Orchestration error: {data["error"]}')

def test_orchestration():
    print('🧪 Testing Full Orchestration via SocketIO')
    print('=' * 60)
    
    try:
        # Connect to server
        print('Connecting to http://localhost:5001...')
        sio.connect('http://localhost:5001')
        
        # Wait for connection
        time.sleep(1)
        
        # Emit orchestration request
        print('\n📤 Emitting execute_full_orchestration event...')
        sio.emit('execute_full_orchestration', {
            'company_info': {
                'company_name': 'Test Company',
                'dba_name': 'Test DBA',
                'industry': 'Technology',
                'location': 'New York'
            },
            'objectives': [
                'Test objective 1',
                'Test objective 2',
                'Test objective 3'
            ]
        })
        
        # Wait for responses
        print('⏳ Waiting for orchestration to complete...\n')
        time.sleep(15)  # Wait 15 seconds for orchestration
        
        print('\n✅ Test complete')
        
    except Exception as e:
        print(f'❌ Error: {e}')
    finally:
        if sio.connected:
            sio.disconnect()
            print('Disconnected from server')

if __name__ == '__main__':
    test_orchestration()
