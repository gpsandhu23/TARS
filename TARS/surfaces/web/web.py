import base64
import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

import streamlit as st
from graphs.core_agent import run_core_agent


def get_image_base64(image_file):
    return base64.b64encode(image_file.getvalue()).decode()


# Title of the web app
st.title("TARS Web Interface")

# Add a text input for user task
user_task = st.text_input("Enter your task")

# Add a file uploader for images
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

# Add a button to submit the task
if st.button("Submit Task"):
    if user_task:
        # Prepare the input for the core agent
        agent_input = {"message": user_task}

        # If an image was uploaded, add it to the input
        if uploaded_file is not None:
            image_base64 = get_image_base64(uploaded_file)
            agent_input["image_url"] = f"data:image/png;base64,{image_base64}"

        # Call the core agent with the user task and image (if any)
        response = run_core_agent(
            user_id="streamlit_user", user_message=str(agent_input)
        )

        # Since run_core_agent returns a generator, we need to iterate through it
        for response_part in response:
            st.write(response_part)

# Display the uploaded image
if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
