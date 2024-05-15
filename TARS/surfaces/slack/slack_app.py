from graphs.agent import AgentManager
from config.config import slack_settings
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from langsmith import traceable

class SlackBot:
    def __init__(self):
        self.setup_logging()
        self.chat_history = []
        self.agent_manager = AgentManager()  # Create an instance of AgentManager from agent.py
        self.initialize_slack_app()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        logging.info("Logger initialized.")

    def initialize_slack_app(self):
        try:
            self.app = App(
                token=slack_settings.slack_bot_token,
                signing_secret=slack_settings.slack_signing_secret
            )
            self.app.event("message")(self.process_message)
            logging.info("Slack app initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Slack App: {e}")
            raise

    def fetch_user_info(self, client, user_id):
        try:
            user_info = client.users_info(user=user_id)
            return user_info, user_info['user']['real_name'] if user_info and user_info['ok'] else "Unknown"
        except Exception as e:
            logging.error(f"Failed to fetch user info: {e}")
            return None, "Unknown"

    def prepare_agent_input(self, event, user_real_name):
        agent_input = {'user_name': user_real_name, 'message': event.get('text', '')}
        agent_input.update(self.extract_images(event))
        return agent_input

    def extract_images(self, event):
        images = {}
        if 'files' in event:
            for file_info in event['files']:
                if file_info['mimetype'].startswith('image/'):
                    images['image_url'] = file_info['url_private']
        return images

    @traceable(name="Slack Message")
    def process_message(self, event, client):
        user_id, channel_id = event.get('user'), event.get('channel')
        if self.is_direct_message(event):
            return self.handle_direct_message(event, client, user_id, channel_id)

    def is_direct_message(self, event):
        return 'channel_type' in event and event['channel_type'] == 'im' and 'bot_id' not in event

    def handle_direct_message(self, event, client, user_id, channel_id):
        response = client.chat_postMessage(channel=channel_id, text="Processing your request, please wait...")
        ts = response['ts']
        user_info, user_real_name = self.fetch_user_info(client, user_id)
        agent_input = self.prepare_agent_input(event, user_real_name)
        agent_response_text = self.agent_manager.process_user_task(str(agent_input), self.chat_history)
        self.send_response(client, channel_id, ts, agent_response_text)
        return agent_response_text

    def send_response(self, client, channel_id, ts, text):
        if len(text) > 4000:
            first_part, remaining_parts = text[:4000], text[4000:]
            client.chat_update(channel=channel_id, ts=ts, text=first_part)
            client.chat_postMessage(channel=channel_id, text=remaining_parts)
        else:
            client.chat_update(channel=channel_id, ts=ts, text=text)

    def start(self):
        handler = SocketModeHandler(self.app, slack_settings.slack_app_token)
        handler.start()

if __name__ == "__main__":
    bot = SlackBot()
    bot.start()
