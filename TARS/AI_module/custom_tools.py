import json
import sys
import os
import requests
import base64
import re
import time
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from langchain.agents import tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Add the parent directory to sys.path for absolute imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import from email_module
from email_module.load_creds import authenticate_gmail_api, authenticate_calendar_api
from email_module.gmail_reader import fetch_unread_emails, mark_email_as_read, get_mime_message, get_email_content, get_upcoming_events

# Custom tool definition
@tool
def get_word_length(word: str) -> int:
    """
    Calculates and returns the length of a given word.

    Args:
        word (str): The word for which the length needs to be calculated.

    Returns:
        int: The length of the word.
    """
    return len(word)

# Schema for handle_message
handle_message_schema = [
    {
        "name": "handle_message",
        "description": "You are an AI named TARS created by GP (Gurpartap Sandhu) to help handle incoming messages",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "description": "Summary of the message",
                },
                "action_needed": {
                    "type": "boolean",
                    "description": "Does this message warrant any action from me",
                },
                "urgency": {
                    "type": "string",
                    "description": "What is the level of urgency of taking action based on this message.",
                    "enum": ["high", "medium", "low", "unknown"]
                },
                "importance": {
                    "type": "string",
                    "description": "What is the level of importance for this message.",
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

# AI Gmail Handler function
def ai_gmail_handler(classifier_input):
    """
    Processes the classifier input to determine actions and details about an email using a ChatOpenAI model.

    Args:
        classifier_input (str): The input string containing details about the email to be classified.

    Returns:
        dict: A dictionary containing the processed information of the email.
    """
    try:
        prompt = ChatPromptTemplate.from_messages([("human", "{input}")])
        model = ChatOpenAI(model="gpt-4-1106-preview", temperature=0).bind(functions=handle_message_schema)
        runnable = prompt | model
        message_action = runnable.invoke({"input": classifier_input})
        content = message_action.content
        function_call = message_action.additional_kwargs.get('function_call')

        if function_call is not None:
            content = function_call.get('arguments', content)

        # Check if content is a string and can be parsed as JSON
        if isinstance(content, str):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If content is a string but not JSON, wrap it in a JSON-like structure
                return {
                    "error": "Content is a string but not JSON",
                    "raw_content": content
                }
        else:
            # If not a string, log and return a default dictionary
            logging.error("Content is not in the expected format. Returning default dictionary.")
            return {"error": "Content not in expected format", "raw_content": str(content)}

    except Exception as e:
        logging.error(f"Error in ai_gmail_handler: {e}")
        return {"error": "Exception occurred in ai_gmail_handler", "exception_message": str(e)}


# Tool to handle all unread Gmails
@tool
def handle_all_unread_gmail() -> list:
    """
    Processes all unread emails in the Gmail inbox and returns a list containing details of each email.

    Returns:
        list: A list of dictionaries, each containing details of an unread email such as sender, subject, summary, 
              action needed, importance, urgency, action, and action instructions.
    """
    try:
        service = authenticate_gmail_api()
        unread_messages = fetch_unread_emails(service)
        all_message_details = []

        for message in unread_messages:
            msg_id = message['id']
            received_date = message['received_date']
            mime_msg = get_mime_message(service, 'me', msg_id)

            headers = mime_msg.items()
            sender = next(value for name, value in headers if name == 'From')
            subject = next(value for name, value in headers if name == 'Subject')
            content = get_email_content(mime_msg)

            classifier_input = "Sender: " + str(sender) + " Subject: " + str(subject) + " Email content: " + str(content)
            ai_response = ai_gmail_handler(classifier_input)
            print(type(ai_response))

            email_details = {
                'sender': sender,
                'subject': subject,
                'received_date': received_date,
                'id': msg_id,
                'summary': ai_response.get('summary', 'N/A'),
                'action_needed': ai_response.get('action_needed', 'N/A'),
                'importance': ai_response.get('importance', 'N/A'),
                'urgency': ai_response.get('urgency', 'N/A'),
                'action': ai_response.get('action', 'N/A'),
                'action_instructions': ai_response.get('action_instructions', 'N/A')
            }

            logging.info(email_details)
            all_message_details.append(email_details)
            mark_email_as_read(service, 'me', msg_id)

        return all_message_details
    except Exception as e:
        logging.error(f"Error in handle_all_unread_gmail: {e}")
        return []

@tool
def fetch_emails_by_sender_name(sender_name: str) -> list[dict[str, str]]:
    """
    Fetch emails by a specific sender's name.

    Args:
        sender_name (str): The name of the sender.

    Returns:
        A list of dictionaries, each containing details of emails from senders matching the specified name, or None if an error occurs.
    """
    try:
        # Authenticate and create a Gmail API service instance
        service = authenticate_gmail_api()

        # Search for messages from the specified sender name
        query = f'from:{sender_name}'
        response = service.users().messages().list(userId='me', q=query).execute()

        emails = []
        if 'messages' in response:
            for message in response['messages']:
                email_id = message['id']

                # Fetch the full message details using the email ID
                raw_message = service.users().messages().get(userId='me', id=email_id, format='raw').execute()
                
                # Convert raw_message to a MIME message
                mime_msg = get_mime_message(service, 'me', email_id)

                # Extract headers for sender and subject
                headers = mime_msg.items()
                sender = next((value for name, value in headers if name == 'From'), 'No Sender')
                subject = next((value for name, value in headers if name == 'Subject'), 'No Subject')
                
                # Get email content
                content = get_email_content(mime_msg)

                # Compile email details
                email_details = {
                    'id': email_id,
                    'sender': sender,
                    'subject': subject,
                    'content': content
                }

                emails.append(email_details)

        return emails

    except Exception as e:
        print(f'An error occurred: {e}')
        return None

# Example usage
emails_from_sender_name = fetch_emails_by_sender_name('John Doe')

# Image reading tool
@tool
def read_image_tool(image_path: str, prompt: str) -> str:
    """
    Processes an image (from a given path or Slack URL) and returns insights based on the provided prompt using OpenAI's GPT-4 vision model.

    Args:
        image_path (str): The path or URL of the image to be processed.
        prompt (str): The prompt describing the insight required from the image.

    Returns:
        str: The response from the model providing the requested insight.
    """
    try:
        client = OpenAI()
        slack_token = os.environ.get("SLACK_BOT_TOKEN")

        # Function to download image from Slack and convert to base64
        def fetch_image_from_slack(url: str) -> str:
            headers = {"Authorization": f"Bearer {slack_token}"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return base64.b64encode(response.content).decode('utf-8')
            else:
                raise Exception(f"Failed to download image from Slack. Status code: {response.status_code}")

        slack_url_pattern = r'https?://files\.slack\.com/.*'
        is_slack_url = re.match(slack_url_pattern, image_path) is not None

        if is_slack_url and slack_token:
            image_base64 = fetch_image_from_slack(image_path)
            image_data_url = f"data:image/jpeg;base64,{image_base64}"
            content_block = {"type": "image_url", "image_url": {"url": image_data_url}}
        else:
            content_block = {"type": "image_url", "image_url": {"url": image_path}}

        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}, content_block],
                }
            ],
            max_tokens=900,
        )

        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error in read_image_tool: {e}")
        return "Error processing image"

# Tool to fetch DMs from Slack
@tool
def fetch_dms_last_x_hours(hours: int) -> list:
    """
    Fetches direct messages from the user's Slack account for the past specified number of hours.

    Args:
        hours (int): The number of hours in the past from which to retrieve direct messages.

    Returns:
        list: A list of dictionaries, each containing details of a direct message, including sender's user ID, 
              timestamp, and text of the message. Returns None if an error occurs.
    """
    try:
        slack_user_token = os.environ.get("SLACK_USER_TOKEN")
        client = WebClient(token=slack_user_token)
        hours_ago = time.time() - hours * 60 * 60
        dms_last_x_hours = []

        conversations = client.conversations_list(types='im')
        for conversation in conversations['channels']:
            conversation_id = conversation['id']
            history = client.conversations_history(channel=conversation_id, oldest=str(hours_ago))
            for message in history['messages']:
                dms_last_x_hours.append({
                    "user": message.get('user', 'Unknown'),
                    "timestamp": message.get('ts', 'Unknown Timestamp'),
                    "text": message.get('text', 'No Text')
                })

        return dms_last_x_hours
    except SlackApiError as e:
        logging.error(f"Error fetching DMs: {e.response['error']}")
        return None

@tool
def fetch_calendar_events_for_x_days(days: int) -> list:
    """
    Fetch the upcoming events from the primary Google Calendar for the next 'x' number of days.

    Args:
        days (int): The number of days from today for which to retrieve events.

    Returns:
        List of upcoming calendar events within the specified number of days.
    """
    service = authenticate_calendar_api()
    events = get_upcoming_events(service, days)

    return events