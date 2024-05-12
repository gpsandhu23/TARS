import streamlit as st
# from graphs.agent import process_user_task

# Title of the web app
st.title('TARS Web Interface')

# # Session state to store chat history
# if 'chat_history' not in st.session_state:
#     st.session_state['chat_history'] = []

# # Text input for user message
# user_input = st.text_input("Type your message:", key="user_input")

# # Button to send the message
# if st.button("Send"):
#     if user_input:
#         # Process the user's task and update the chat history
#         response = process_user_task(user_input, st.session_state['chat_history'])
        
#         # Display the conversation
#         st.session_state['chat_history'].append(f"You: {user_input}")
#         st.session_state['chat_history'].append(f"TARS: {response}")
        
#         # Clear the input box after sending the message
#         st.session_state['user_input'] = ""

# # Display chat history
# for message in st.session_state['chat_history']:
#     st.text(message)

