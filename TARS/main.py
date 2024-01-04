from AI_module.agent import process_user_task
from dotenv import load_dotenv
import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Set up basic logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Initialize the chat_history
chat_history = []

# Slack App Initialization
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

def fetch_user_info(client, user_id):
    """Fetches user information from Slack."""
    user_info = client.users_info(user=user_id)
    return user_info, user_info['user']['real_name'] if user_info and user_info['ok'] else "Unknown"

def prepare_agent_input(event, user_real_name):
    """Prepares the agent input including any images."""
    agent_input = {'user name': user_real_name, 'message': event.get('text', '')}
    if 'files' in event:
        for file_info in event['files']:
            if file_info['mimetype'].startswith('image/'):
                agent_input['image_url'] = file_info['url_private']
    return agent_input

def process_message(event, client):
    """Process the message and respond accordingly."""
    try:
        user_id, channel_id = event.get('user'), event.get('channel')

        # Respond only to DMs and non-bot messages
        if 'channel_type' in event and event['channel_type'] == 'im' and 'bot_id' not in event:
            response = client.chat_postMessage(channel=channel_id, text="Processing your request, please wait...")
            ts = response['ts']

            user_info, user_real_name = fetch_user_info(client, user_id)
            agent_input = prepare_agent_input(event, user_real_name)
            agent_response_text = process_user_task(str(agent_input), chat_history)

            client.chat_update(channel=channel_id, ts=ts, text=agent_response_text)
    except Exception as e:
        logging.error("Error processing message: %s", str(e))

@app.event("message")
def message_handler(event, say, ack, client):
    """Handles incoming messages."""
    ack()
    logging.info("Message received: %s", event)

    # Process the message
    process_message(event, client)

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()