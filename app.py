import streamlit as st
import requests
import json
import websocket
import threading
import time
import queue
from datetime import datetime

# Constants
API_BASE_URL = 'https://cwd-dq7n.onrender.com'

# Global message queue for thread-safe communication
message_queue = queue.Queue()

# Initialize session state variables
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'logs' not in st.session_state:
    st.session_state['logs'] = []

def add_log(message, type='info'):
    timestamp = datetime.now().strftime('%H:%M:%S')
    message_queue.put({
        'type': 'log',
        'data': {
            'timestamp': timestamp,
            'message': message,
            'type': type
        }
    })

def add_chat_message(message, is_user=False):
    message_queue.put({
        'type': 'chat',
        'data': {
            'content': message,
            'is_user': is_user
        }
    })

def process_message_queue():
    while not message_queue.empty():
        msg = message_queue.get()
        if msg['type'] == 'log':
            st.session_state['logs'].append(msg['data'])
        elif msg['type'] == 'chat':
            st.session_state['messages'].append(msg['data'])

def execute_tool(tool_name):
    try:
        response = requests.post(f"{API_BASE_URL}/execute/{tool_name}")
        data = response.json()
        if data.get('status') == 'processing':
            add_log(f"{tool_name} process started...", 'info')
    except Exception as e:
        add_log(f"Error executing {tool_name}: {str(e)}", 'error')

def send_query(query):
    if not query:
        return
    
    add_chat_message(query, True)
    add_log(f"Sending query: {query}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={'query': query}
        )
        data = response.json()
        if data.get('status') == 'processing':
            add_log('Query processing started...', 'info')
    except Exception as e:
        add_log(f"Error: {str(e)}", 'error')
        add_chat_message('Error processing query. Please try again.')

def handle_websocket_message(message):
    try:
        data = json.loads(message)
        if data['type'] == 'chat_response':
            add_chat_message(json.dumps(data['data'], indent=2))
            add_log('Chat response received', 'success')
        elif data['type'] == 'error':
            add_log(f"Error: {data['data']}", 'error')
        else:
            add_log(data['data'], data['type'])
    except Exception as e:
        add_log(f"Error processing message: {str(e)}", 'error')

def websocket_thread():
    while True:
        try:
            ws = websocket.WebSocketApp(
                f"wss://cwd-dq7n.onrender.com/ws",
                on_message=lambda ws, msg: handle_websocket_message(msg),
                on_error=lambda ws, err: add_log(f"WebSocket error: {str(err)}", 'error'),
                on_close=lambda ws: add_log("WebSocket disconnected", 'warning'),
                on_open=lambda ws: add_log("WebSocket connected", 'success')
            )
            ws.run_forever()
        except Exception as e:
            add_log(f"WebSocket connection error: {str(e)}", 'error')
            time.sleep(5)  # Wait before reconnecting

# Start WebSocket connection in a separate thread
threading.Thread(target=websocket_thread, daemon=True).start()

# Streamlit UI
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Stock Analysis Dashboard")

# Process any pending messages
process_message_queue()

# Create two columns
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Chat Interface")
    
    # Chat input
    query = st.text_input("Enter your stock analysis query...", key="query_input")
    if st.button("Send") or query:
        if query:  # Only send if there's a query
            send_query(query)
            st.rerun()
    
    # Chat messages
    st.subheader("Messages")
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.get('messages', []):
            if msg['is_user']:
                st.chat_message("user").write(msg['content'])
            else:
                st.chat_message("assistant").write(msg['content'])
    
    # Tools section
    st.subheader("Tools")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("YouTube Fetcher", use_container_width=True):
            execute_tool('youtube-fetcher')
        if st.button("Transcript Analyzer", use_container_width=True):
            execute_tool('transcript-analyzer')
    with col2:
        if st.button("Yahoo Finance", use_container_width=True):
            execute_tool('yahoo-tool')
        if st.button("Process Analysis", use_container_width=True):
            execute_tool('process-analysis')

with col2:
    st.subheader("Logs")
    log_container = st.container()
    with log_container:
        for log in st.session_state.get('logs', []):
            if log['type'] == 'error':
                st.error(f"[{log['timestamp']}] {log['message']}")
            elif log['type'] == 'warning':
                st.warning(f"[{log['timestamp']}] {log['message']}")
            elif log['type'] == 'success':
                st.success(f"[{log['timestamp']}] {log['message']}")
            else:
                st.info(f"[{log['timestamp']}] {log['message']}")

# Add some custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
    }
    .stTextInput>div>div>input {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True) 