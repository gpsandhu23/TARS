import json
import sys
import os
import requests
import base64
import re

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Now you can use absolute import
from email_module.load_creds import authenticate_gmail_api
from email_module.email_reader import fetch_unread_emails
from email_module.email_reader import mark_email_as_read
from email_module.email_reader import get_mime_message
from email_module.email_reader import get_email_content

from dotenv import load_dotenv

# Lanchain imports
from langchain.agents import tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# OpenAI imports
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Create a simple custom tool to test the agent
@tool
def get_word_length(word: str) -> int:
    """Returns the length of a word."""
    return len(word)

handle_message_schema = [
            {
                "name": "handle_message",
                "description": "You are an AI named TARS created by GP (Gurpartap Sandhu) to help handle incoming messages",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "description": """
                            Summary of the message
                            """,
                        },
                        "action_needed": {
                            "type": "boolean",
                            "description": "Does this message warrany any action from me",
                        },
                        "urgency": {
                            "type": "string",
                            "description": """
                            What is the level of urgency of taking action based on this message.
                            If I need to do something urgently, it should be high
                            If I need to do something soon, it should be medium
                            If I need to eventually do something, it should be low
                            """,
                            "enum": ["high", "medium", "low", "unknown"]
                        },
                        "importance": {
                            "type": "string",
                            "description": """
                            What is the level of importance for this message.
                            """,
                            "enum": ["high", "medium", "low", "unknown"]
                        },
                        "action": {
                            "type": "string",
                            "description": "What action should be performed, if any",
                        },
                        "action_instructions": {
                            "type": "string",
                            "description": "What are the step by step instructions to perform the recommended action, if any",
                        },
                    },
                    "required": ["summary", "action_needed", "urgency", "importance", "action", "action_instructions"],
                }
            }
        ]

def ai_gmail_handler(classifier_input):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{input}")
        ]
    )
    model = ChatOpenAI(model = "gpt-4-1106-preview", temperature=0).bind(functions=handle_message_schema)
    runnable = prompt | model
    # Invoke the runnable with the classifier input
    message_action = runnable.invoke({"input": classifier_input})
    content = message_action.content
    function_call = message_action.additional_kwargs.get('function_call')

    # Check if there's a function call and adjust content accordingly
    if function_call is not None:
        content = function_call.get('arguments', content)

    # Convert the string to a JSON object
    try:
        json_object = json.loads(content)
    except json.JSONDecodeError:
        print("Failed to parse JSON. Here's the raw content:")
        return content

    # Pretty print the JSON object
    # print(json.dumps(json_object, indent=4))
    return json_object

@tool
def handle_all_unread_gmail() -> list:
    """Handle all unread messages in the inbox and return their details."""
    service = authenticate_gmail_api()
    unread_messages = fetch_unread_emails(service)

    all_message_details = []  # List to store details for each email

    for message in unread_messages:
        msg_id = message['id']
        mime_msg = get_mime_message(service, 'me', msg_id)

        headers = mime_msg.items()
        sender = next(value for name, value in headers if name == 'From')
        subject = next(value for name, value in headers if name == 'Subject')
        content = get_email_content(mime_msg)

        classifier_input = "Sender: " + str(sender) + " Subject: " + str(subject) + " Email content: " + str(content)
        ai_response = ai_gmail_handler(classifier_input)

        # Extract details from ai_response
        email_details = {
            'sender': sender,
            'subject': subject,
            'summary': ai_response.get('summary', 'N/A'),
            'action_needed': ai_response.get('action_needed', 'N/A'),
            'importance': ai_response.get('importance', 'N/A'),
            'urgency': ai_response.get('urgency', 'N/A'),
            'action': ai_response.get('action', 'N/A'),
            'action_instructions': ai_response.get('action_instructions', 'N/A')
        }

        print(email_details)
        # Add the details to the list
        all_message_details.append(email_details)

        # Mark the email as read
        mark_email_as_read(service, 'me', msg_id)

    return all_message_details

@tool
def read_image_tool(image_path: str, prompt: str) -> str:
    """Read an image and return insight requested in the prompt."""
    client = OpenAI()

    # Retrieve your Slack bot token from the environment variable
    slack_token = os.environ.get("SLACK_BOT_TOKEN")

    # Function to download image from Slack and convert to base64
    def fetch_image_from_slack(url: str) -> str:
        headers = {"Authorization": f"Bearer {slack_token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode('utf-8')
        else:
            raise Exception(f"Failed to download image from Slack. Status code: {response.status_code}")

    # Check if the image path is a Slack URL using regex for more precise matching
    slack_url_pattern = r'https?://files\.slack\.com/.*'
    is_slack_url = re.match(slack_url_pattern, image_path) is not None

    if is_slack_url and slack_token:
        # Fetching the image from Slack and converting to base64
        image_base64 = fetch_image_from_slack(image_path)

        # Correctly formatting the base64 data URL
        image_data_url = f"data:image/jpeg;base64,{image_base64}"

        content_block = {
            "type": "image_url",
            "image_url": {
                "url": image_data_url
            }
        }
    else:
        content_block = {
            "type": "image_url",
            "image_url": {
                "url": image_path
            }
        }

    # Making the API request
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    content_block,
                ],
            }
        ],
        max_tokens=900,
    )

    return response.choices[0].message.content