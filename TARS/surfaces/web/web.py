import sys
import os
import streamlit as st
import requests
from urllib.parse import urlencode

# Title of the web app
st.title('TARS Web Interface')

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
        'client_id': "Iv23liMdY6VduLyR6gfb",
        'state': state
    }
    url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    # Redirect the user to GitHub for authentication
    st.query_params(redirect=url)
