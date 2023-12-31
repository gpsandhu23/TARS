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
    
    # Common variables used in both text and file handling
    user_id = event.get('user')
    channel_id = event.get('channel')

    # Check if the message is a DM and not from a bot
    if 'channel_type' in event and event['channel_type'] == 'im' and 'bot_id' not in event:
        # Send an initial response
        response = client.chat_postMessage(channel=channel_id, text="Processing your request, please wait...")
        ts = response['ts']  # Timestamp of the message
        
        # Fetch user info from Slack API
        user_info = client.users_info(user=user_id)
        user_real_name = user_info['user']['real_name'] if user_info and user_info['ok'] else "Unknown"
        
        # Initialize agent_input with user name and any text
        agent_input = {'user name': user_real_name, 'message': event.get('text', '')}
        
        # If there are files, check for images and modify agent_input accordingly
        if 'files' in event:
            files = event['files']
            for file_info in files:
                if file_info['mimetype'].startswith('image/'):
                    # Include the image URL in the agent input
                    file_url_private = file_info['url_private']
                    agent_input['image_url'] = file_url_private  # Adding the image URL to agent_input
        
        # Convert agent_input to string
        agent_input_str = str(agent_input)
        print("agent_input_str", agent_input_str)

        # Call the process_user_task function and pass the agent input and the current chat history
        agent_response_text = process_user_task(agent_input_str, chat_history)

        # Send the response back to the user in Slack
        client.chat_update(channel=channel_id, ts=ts, text=agent_response_text)


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()