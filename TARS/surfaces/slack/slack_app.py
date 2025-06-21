from typing import Dict, Any, Tuple, Optional
# from graphs.agent import AgentManager
from TARS.config.config import slack_settings
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from langsmith import traceable, Client
from TARS.graphs.core_agent import run_core_agent
from TARS.metrics.event_instrumentation import IncomingUserEvent
from datetime import datetime, timezone



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
        # self.agent_manager: AgentManager = AgentManager()
        self.initialize_slack_app()
        self.user_run_ids = {}  # user_id -> run_id
        self.langsmith_client = Client()  # Initialize LangSmith client

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
            self.app.event("reaction_added")(self.handle_reaction)  # Add reaction handler
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
                    break  # Return the first image found
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

            # Create and log the IncomingUserEvent
            user_event = IncomingUserEvent(
                user_id=user_id,
                user_name=self.fetch_user_info(client, user_id)[1],  # Using the real name
                event_time=datetime.now(timezone.utc),
                capability_invoked="TARS",
                user_agent="Slack",
                response_satisfaction="none"
            )
            self.log_user_event(user_event)
            
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
        response = client.chat_postMessage(channel=channel_id, text="Working on it...")
        ts = response.data['ts']
        user_info, user_real_name = self.fetch_user_info(client, user_id)
        agent_input = self.prepare_agent_input(event, user_real_name)

        # Get the generator from run_core_agent
        agent_response_generator = run_core_agent(user_name=user_real_name, message=agent_input['message'])

        # Collect all responses from the generator
        agent_response_text = ""
        first_response = True
        
        for response_part in agent_response_generator:
            if first_response:
                # First yield is (content, run_id)
                if isinstance(response_part, tuple) and len(response_part) == 2:
                    content, run_id = response_part
                    # Store the run_id in memory for this user
                    self.user_run_ids[user_id] = run_id
                    logging.info(f"Stored run_id '{run_id}' for user '{user_id}'")
                    logging.info(f"Current user_run_ids: {self.user_run_ids}")
                    agent_response_text += content
                else:
                    # Fallback if not a tuple
                    agent_response_text += response_part
                first_response = False
            else:
                # Subsequent yields are just content
                agent_response_text += response_part
            
            # Optionally, you can update the message in real-time as parts come in
            self.send_response(client, channel_id, ts, agent_response_text)

        # Send the final complete response
        self.send_response(client, channel_id, ts, agent_response_text)
        return agent_response_text
    
    def log_user_event(self, event: IncomingUserEvent) -> None:
        """
        Log the user event for metrics and analysis.

        Args:
            event: The IncomingUserEvent to be logged.
        """
        # Here you would implement the actual logging logic
        # This could involve sending the event to a database, logging service, etc.
        logging.info(f"User Event Logged: {event.model_dump()}")
        print(f"User Event Logged: {event.model_dump()}")

    def update_user_event_satisfaction(self, user_id: str, satisfaction: str) -> None:
        """
        Update the satisfaction of the most recent user event.

        Args:
            user_id: The ID of the user.
            satisfaction: The satisfaction level ("thumbs_up" or "thumbs_down").
        """
        # Implement logic to update the satisfaction of the most recent event
        # This could involve updating a database record, for example
        pass

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

    def handle_reaction(self, event: Dict[str, Any], client: Any) -> None:
        """
        Handle reaction events for feedback collection.

        Args:
            event: The Slack reaction event dictionary.
            client: The Slack client object.
        """
        logging.info(f"=== REACTION HANDLER START ===")
        logging.info(f"Received reaction event: {event}")
        
        user_id = event.get('user')
        reaction = event.get('reaction')
        
        logging.info(f"Extracted user_id: {user_id}")
        logging.info(f"Extracted reaction: {reaction}")
        
        # Log ALL reactions for debugging
        logging.info(f"Processing reaction: '{reaction}' (type: {type(reaction)})")
        
        # Only process thumbs up/down reactions
        if reaction not in ['+1', '-1']:
            logging.info(f"Reaction '{reaction}' not in ['+1', '-1'], ignoring")
            logging.info(f"Available user_run_ids: {list(self.user_run_ids.keys())}")
            return
            
        logging.info(f"Processing valid reaction: {reaction}")
        
        # Get the run_id for this user
        run_id = self.user_run_ids.get(user_id)
        logging.info(f"Looking up run_id for user {user_id}: {run_id}")
        
        if not run_id:
            logging.warning(f"No run_id found for user {user_id}")
            logging.info(f"Available user_run_ids: {list(self.user_run_ids.keys())}")
            return
            
        # Map reaction to score
        score = 1 if reaction == '+1' else 0
        feedback_key = "user_satisfaction"
        
        logging.info(f"Creating feedback - key: {feedback_key}, score: {score}, run_id: {run_id}")
        
        try:
            # Create feedback in LangSmith
            logging.info(f"Calling langsmith_client.create_feedback with:")
            logging.info(f"  - key: {feedback_key}")
            logging.info(f"  - score: {score}")
            logging.info(f"  - run_id: {run_id}")
            logging.info(f"  - comment: User reacted with {reaction}")
            
            feedback_result = self.langsmith_client.create_feedback(
                key=feedback_key,
                score=score,
                run_id=run_id,
                comment=f"User reacted with {reaction}"
            )
            
            logging.info(f"LangSmith create_feedback returned: {feedback_result}")
            logging.info(f"Feedback logged successfully for user {user_id}: {feedback_key}={score}")
        except Exception as e:
            logging.error(f"Failed to create feedback: {e}", exc_info=True)
            logging.error(f"Exception type: {type(e)}")
            logging.error(f"Exception args: {e.args}")
        
        logging.info("=== REACTION HANDLER END ===")

    def start(self) -> None:
        """
        Start the Slack bot using SocketModeHandler.
        """
        handler = SocketModeHandler(self.app, slack_settings.slack_app_token)
        handler.start()

if __name__ == "__main__":
    bot = SlackBot()
    bot.start()
