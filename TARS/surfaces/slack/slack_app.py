from typing import Dict, Any, Tuple, Optional
from graphs.agent import AgentManager
from config.config import slack_settings
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from langsmith import traceable
from slack_sdk.web import SlackResponse

class SlackBot:
    """
    A Slack bot that processes messages and interacts with users.

    This class initializes a Slack app, sets up logging, and manages interactions
    with users through direct messages.
    """

    def __init__(self):
        """
        Initialize the SlackBot with logging, chat history, and Slack app setup.
        """
        self.setup_logging()
        self.chat_history: list = []
        self.agent_manager: AgentManager = AgentManager()
        self.initialize_slack_app()

    def setup_logging(self) -> None:
        """
        Set up basic logging configuration for the bot.
        """
        logging.basicConfig(level=logging.INFO)
        logging.info("Logger initialized.")

    def initialize_slack_app(self) -> None:
        """
        Initialize the Slack app with the necessary tokens and event handlers.

        Raises:
            Exception: If initialization fails.
        """
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

    def fetch_user_info(self, client: Any, user_id: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Fetch user information from Slack.

        Args:
            client: The Slack client object.
            user_id: The ID of the user to fetch information for.

        Returns:
            A tuple containing the user info dictionary and the user's real name.
        """
        try:
            user_info = client.users_info(user=user_id)
            return user_info, user_info['user']['real_name'] if user_info and user_info['ok'] else "Unknown"
        except Exception as e:
            logging.error(f"Failed to fetch user info: {e}")
            return None, "Unknown"

    def prepare_agent_input(self, event: Dict[str, Any], user_real_name: str) -> Dict[str, Any]:
        """
        Prepare the input for the agent based on the Slack event.

        Args:
            event: The Slack event dictionary.
            user_real_name: The real name of the user.

        Returns:
            A dictionary containing the prepared input for the agent.
        """
        agent_input = {'user_name': user_real_name, 'message': event.get('text', '')}
        agent_input.update(self.extract_images(event))
        return agent_input

    def extract_images(self, event: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract image URLs from the Slack event.

        Args:
            event: The Slack event dictionary.

        Returns:
            A dictionary containing image URLs if present.
        """
        images = {}
        if 'files' in event:
            for file_info in event['files']:
                if file_info['mimetype'].startswith('image/'):
                    images['image_url'] = file_info['url_private']
        return images

    @traceable(name="Slack Message")
    def process_message(self, event: Dict[str, Any], client: Any) -> Optional[str]:
        """
        Process incoming Slack messages.

        Args:
            event: The Slack event dictionary.
            client: The Slack client object.

        Returns:
            The agent's response text if it's a direct message, None otherwise.
        """
        user_id, channel_id = event.get('user'), event.get('channel')
        if self.is_direct_message(event):
            response = self.handle_direct_message(event, client, user_id, channel_id)
            return response

    def is_direct_message(self, event: Dict[str, Any]) -> bool:
        """
        Check if the event is a direct message to the bot.

        Args:
            event: The Slack event dictionary.

        Returns:
            True if it's a direct message, False otherwise.
        """
        return 'channel_type' in event and event['channel_type'] == 'im' and 'bot_id' not in event

    def handle_direct_message(self, event: Dict[str, Any], client: Any, user_id: str, channel_id: str) -> str:
        """
        Handle a direct message sent to the bot.

        Args:
            event: The Slack event dictionary.
            client: The Slack client object.
            user_id: The ID of the user who sent the message.
            channel_id: The ID of the channel where the message was sent.

        Returns:
            The agent's response text.
        """
        response = client.chat_postMessage(channel=channel_id, text="Processing your request, please wait...")
        ts = response['ts']
        user_info, user_real_name = self.fetch_user_info(client, user_id)
        agent_input = self.prepare_agent_input(event, user_real_name)
        agent_response_text = self.agent_manager.process_user_task(str(agent_input), self.chat_history)
        self.send_response(client, channel_id, ts, agent_response_text)
        return agent_response_text

    def send_response(self, client: Any, channel_id: str, ts: str, text: str) -> None:
        """
        Send a response message to Slack, handling long messages if necessary.

        Args:
            client: The Slack client object.
            channel_id: The ID of the channel to send the message to.
            ts: The timestamp of the message to update.
            text: The text of the response to send.
        """
        if len(text) > 4000:
            first_part, remaining_parts = text[:4000], text[4000:]
            client.chat_update(channel=channel_id, ts=ts, text=first_part)
            client.chat_postMessage(channel=channel_id, text=remaining_parts)
        else:
            client.chat_update(channel=channel_id, ts=ts, text=text)

    def start(self) -> None:
        """
        Start the Slack bot using SocketModeHandler.
        """
        handler = SocketModeHandler(self.app, slack_settings.slack_app_token)
        handler.start()

if __name__ == "__main__":
    bot = SlackBot()
    bot.start()
