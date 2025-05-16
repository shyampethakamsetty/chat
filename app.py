import streamlit as st
import requests
import websocket
import json
import threading
from datetime import datetime

# Constants
API_BASE_URL = 'https://cwd-dq7n.onrender.com'
WS_URL = 'wss://cwd-dq7n.onrender.com/ws'

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'ws' not in st.session_state:
    st.session_state.ws = None

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

def on_message(ws, message):
    try:
        data = json.loads(message)
        if data['type'] == 'chat_response':
            add_chat_message(data['data'])
            add_log('Response received', 'success')
        elif data['type'] == 'process_started':
            add_log(f"Process started: {data['data']}", 'info')
        elif data['type'] == 'output':
            add_log(data['data'], 'info')
        elif data['type'] == 'warning':
            add_log(data['data'], 'warning')
        elif data['type'] == 'error':
            add_log(f"Error: {data['data']}", 'error')
        elif data['type'] == 'process_complete':
            add_log(f"Process completed: {data['data']}", 'success')
    except Exception as e:
        add_log(f"Error processing message: {str(e)}", 'error')

def on_error(ws, error):
    add_log(f"WebSocket error: {str(error)}", 'error')

def on_close(ws, close_status_code, close_msg):
    add_log("WebSocket disconnected. Reconnecting...", 'error')
    connect_websocket()

def on_open(ws):
    add_log("WebSocket connected", 'success')

def connect_websocket():
    if st.session_state.ws is None:
        ws = websocket.WebSocketApp(WS_URL,
                                  on_message=on_message,
                                  on_error=on_error,
                                  on_close=on_close,
                                  on_open=on_open)
        st.session_state.ws = ws
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

# Initialize WebSocket connection
if st.session_state.ws is None:
    connect_websocket()

# Streamlit UI
st.title("Stock Analysis Dashboard")

# Create two columns for chat and logs
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Chat Interface")
    
    # Chat input
    query = st.text_input("Enter your stock analysis query...", key="query_input")
    if st.button("Send"):
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
                add_log(f"Request sent: {data}", 'info')
                
                if data.get('status') == 'processing':
                    add_log('Query processing started...', 'info')
                    add_chat_message("Processing your query...")
            except Exception as e:
                add_log(f"Error: {str(e)}", 'error')
                add_chat_message('Error processing query. Please try again.')
    
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
                    add_chat_message("YouTube Fetcher process started...")
            except Exception as e:
                add_log(f"Error executing YouTube Fetcher: {str(e)}", 'error')
                add_chat_message("Error executing YouTube Fetcher")
        
        if st.button("Transcript Analyzer"):
            add_log("Executing Transcript Analyzer...")
            try:
                response = requests.post(f"{API_BASE_URL}/execute/transcript-analyzer")
                data = response.json()
                if data.get('status') == 'processing':
                    add_log("Transcript Analyzer process started...", 'info')
                    add_chat_message("Transcript Analyzer process started...")
            except Exception as e:
                add_log(f"Error executing Transcript Analyzer: {str(e)}", 'error')
                add_chat_message("Error executing Transcript Analyzer")
    
    with col2:
        if st.button("Yahoo Finance"):
            add_log("Executing Yahoo Finance...")
            try:
                response = requests.post(f"{API_BASE_URL}/execute/yahoo-tool")
                data = response.json()
                if data.get('status') == 'processing':
                    add_log("Yahoo Finance process started...", 'info')
                    add_chat_message("Yahoo Finance process started...")
            except Exception as e:
                add_log(f"Error executing Yahoo Finance: {str(e)}", 'error')
                add_chat_message("Error executing Yahoo Finance")
        
        if st.button("Process Analysis"):
            add_log("Executing Process Analysis...")
            try:
                response = requests.post(f"{API_BASE_URL}/execute/process-analysis")
                data = response.json()
                if data.get('status') == 'processing':
                    add_log("Process Analysis started...", 'info')
                    add_chat_message("Process Analysis started...")
            except Exception as e:
                add_log(f"Error executing Process Analysis: {str(e)}", 'error')
                add_chat_message("Error executing Process Analysis")

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