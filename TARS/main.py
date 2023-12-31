from AI_module.agent import process_user_task
from dotenv import load_dotenv
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Load environment variables
load_dotenv()

# Initialize the chat_history
chat_history = []

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

@app.event("message")
def message_handler(event, say, ack, client):
    ack()
    print("Message received", event)
    # Check if the message is a DM and not from a bot
    if 'channel_type' in event and event['channel_type'] == 'im' and 'bot_id' not in event:
        user_id = event['user']
        message_text = event['text']
        channel_id = event['channel']

        # Send an initial response
        response = client.chat_postMessage(channel=channel_id, text="Processing your request, please wait...")
        ts = response['ts']  # Timestamp of the message
        
        # Fetch user info from Slack API
        user_info = client.users_info(user=user_id)
        
        # Check if the request was successful
        if user_info and user_info['ok']:
            user_real_name = user_info['user']['real_name']
        else:
            user_real_name = "Unknown"

        agent_input = str({'user name': user_real_name, 'message': message_text})
        # Call the process_user_task function and pass the message text and the current chat history
        agent_response_text = process_user_task(agent_input, chat_history)

        # Send the response back to the user in Slack
        client.chat_update(channel=channel_id, ts=ts, text=agent_response_text)

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()