import sys
import os
import streamlit as st
import requests
from urllib.parse import urlencode
from graphs.core_agent import run_core_agent
# Title of the web app
st.title('TARS Web Interface')

# Add a text input for user task
user_task = st.text_input("Enter your task")

# Add a button to submit the task
if st.button('Submit Task'):
    if user_task:
        # Call the core agent with the user task
        response = run_core_agent(user_task)
        st.write(response)
