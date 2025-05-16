import streamlit as st
import json
import websocket
import threading
import time
import requests
from datetime import datetime
from queue import Queue
import queue

# Constants
API_BASE_URL = 'https://cwd-dq7n.onrender.com'
WS_URL = 'wss://cwd-dq7n.onrender.com/ws'

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'message_queue' not in st.session_state:
    st.session_state.message_queue = Queue()

def add_log(message, type='info'):
    timestamp = datetime.now().strftime('%H:%M:%S')
    st.session_state.logs.append({
        'timestamp': timestamp,
        'message': message,
        'type': type
    })

def add_chat_message(message, is_user=False):
    st.session_state.messages.append({
        'message': message,
        'is_user': is_user
    })

def process_queue():
    try:
        while True:
            try:
                message = st.session_state.message_queue.get_nowait()
                if message['type'] == 'log':
                    add_log(message['message'], message['log_type'])
                elif message['type'] == 'chat':
                    add_chat_message(message['message'], message['is_user'])
            except queue.Empty:
                break
    except Exception as e:
        st.error(f"Error processing queue: {str(e)}")

def queue_log(message, type='info'):
    st.session_state.message_queue.put({
        'type': 'log',
        'message': message,
        'log_type': type
    })

def queue_chat_message(message, is_user=False):
    st.session_state.message_queue.put({
        'type': 'chat',
        'message': message,
        'is_user': is_user
    })

def on_message(ws, message):
    try:
        data = json.loads(message)
        if data['type'] == 'chat_response':
            queue_chat_message(json.dumps(data['data'], indent=2))
            queue_log('Chat response received', 'success')
        elif data['type'] == 'process_started':
            queue_log(f"Process started: {data['data']}", 'info')
        elif data['type'] == 'output':
            queue_log(data['data'], 'info')
        elif data['type'] == 'warning':
            queue_log(data['data'], 'warning')
        elif data['type'] == 'error':
            queue_log(f"Error: {data['data']}", 'error')
        elif data['type'] == 'process_complete':
            queue_log(f"Process completed: {data['data']}", 'success')
    except Exception as e:
        queue_log(f"Error processing message: {str(e)}", 'error')

def on_error(ws, error):
    queue_log(f"WebSocket error: {str(error)}", 'error')

def on_close(ws, close_status_code, close_msg):
    queue_log("WebSocket disconnected. Reconnecting...", 'error')
    time.sleep(3)
    connect_websocket()

def on_open(ws):
    queue_log("WebSocket connected", 'success')

def connect_websocket():
    ws = websocket.WebSocketApp(WS_URL,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close,
                              on_open=on_open)
    ws.run_forever()

def start_websocket_thread():
    websocket_thread = threading.Thread(target=connect_websocket)
    websocket_thread.daemon = True
    websocket_thread.start()

# Initialize WebSocket connection
if 'websocket_started' not in st.session_state:
    start_websocket_thread()
    st.session_state.websocket_started = True

# Process any pending messages from the WebSocket thread
process_queue()

# Streamlit UI
st.title("Stock Analysis Dashboard")

# Create two columns for chat and logs
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Chat Interface")
    
    # Chat input
    query = st.text_input("Enter your stock analysis query...", key="query_input")
    if st.button("Send") or query:
        if query:
            add_chat_message(query, True)
            add_log(f"Sending query: {query}")
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/chat",
                    json={"query": query},
                    headers={"Content-Type": "application/json"}
                )
                data = response.json()
                if data.get('status') == 'processing':
                    add_log('Query processing started...', 'info')
            except Exception as e:
                add_log(f"Error: {str(e)}", 'error')
                add_chat_message('Error processing query. Please try again.')
            
            # Clear the input
            st.session_state.query_input = ""
    
    # Display chat messages
    for msg in st.session_state.messages:
        if msg['is_user']:
            st.chat_message("user").write(msg['message'])
        else:
            st.chat_message("assistant").write(msg['message'])
    
    # Tool buttons
    st.subheader("Tools")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("YouTube Fetcher"):
            add_log("Executing YouTube Fetcher...")
            try:
                response = requests.post(f"{API_BASE_URL}/execute/youtube-fetcher")
                data = response.json()
                if data.get('status') == 'processing':
                    add_log("YouTube Fetcher process started...", 'info')
            except Exception as e:
                add_log(f"Error executing YouTube Fetcher: {str(e)}", 'error')
        
        if st.button("Transcript Analyzer"):
            add_log("Executing Transcript Analyzer...")
            try:
                response = requests.post(f"{API_BASE_URL}/execute/transcript-analyzer")
                data = response.json()
                if data.get('status') == 'processing':
                    add_log("Transcript Analyzer process started...", 'info')
            except Exception as e:
                add_log(f"Error executing Transcript Analyzer: {str(e)}", 'error')
    
    with col2:
        if st.button("Yahoo Finance"):
            add_log("Executing Yahoo Finance...")
            try:
                response = requests.post(f"{API_BASE_URL}/execute/yahoo-tool")
                data = response.json()
                if data.get('status') == 'processing':
                    add_log("Yahoo Finance process started...", 'info')
            except Exception as e:
                add_log(f"Error executing Yahoo Finance: {str(e)}", 'error')
        
        if st.button("Process Analysis"):
            add_log("Executing Process Analysis...")
            try:
                response = requests.post(f"{API_BASE_URL}/execute/process-analysis")
                data = response.json()
                if data.get('status') == 'processing':
                    add_log("Process Analysis started...", 'info')
            except Exception as e:
                add_log(f"Error executing Process Analysis: {str(e)}", 'error')

with col2:
    st.subheader("Logs")
    # Display logs
    for log in st.session_state.logs:
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