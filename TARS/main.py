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
def message_handler(event, say, ack):
    ack()
    print("Message received", event)
    # Check if the message is a DM and not from a bot
    if 'channel_type' in event and event['channel_type'] == 'im' and 'bot_id' not in event:
        message_text = event['text']

        # Call the process_user_task function and pass the message text and the current chat history
        agent_response_text = process_user_task(message_text, chat_history)

        # Send the response back to the user in Slack
        say(agent_response_text)

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()