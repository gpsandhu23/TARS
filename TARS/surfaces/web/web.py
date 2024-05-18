import sys
import os
from langsmith import traceable
import streamlit as st
from graphs.agent import AgentManager
import requests
from urllib.parse import urlencode

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Title of the web app
st.title('TARS Web Interface')

# Create an instance of AgentManager
agent_manager = AgentManager()

# Chat history to maintain state during the session
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Text input for user message
user_input = st.text_input("Enter your message:", key="user_input")

# Function to handle messages
@traceable(name="Web Message")
def handle_message(user_input):
    if user_input:
        # Prepare the agent input
        agent_input = {'user_name': 'Web User', 'message': user_input}
        # Process the user task
        response = agent_manager.process_user_task(agent_input, st.session_state.chat_history)
        # Append to chat history
        st.session_state.chat_history.append((user_input, response))
        # Display the conversation
        for message, reply in st.session_state.chat_history:
            st.text_area("User", value=message, height=75, disabled=True)
            st.text_area("TARS", value=reply, height=75, disabled=True)
    return str(response)

# Button to send the message
if st.button("Send"):
    handle_message(user_input)

# GitHub OAuth integration
if 'auth_state' not in st.session_state:
    st.session_state.auth_state = None

if st.button('Login with GitHub'):
    # Generate a random state value for CSRF protection
    import secrets
    state = secrets.token_hex(16)
    st.session_state.auth_state = state
    # Prepare the GitHub OAuth URL
    params = {
        'client_id': os.getenv('GITHUB_CLIENT_ID'),
        'redirect_uri': 'http://localhost:8501/auth',
        'state': state,
        'scope': 'read:user user:email',
    }
    url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    # Redirect the user to GitHub for authentication
    st.experimental_rerun(url)

# Display authenticated user information
if st.session_state.auth_state:
    st.write(f"Authenticated as: {st.session_state.auth_state}")
