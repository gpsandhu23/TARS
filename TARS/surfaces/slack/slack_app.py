from typing import Dict, Any, Tuple, Optional
# from graphs.agent import AgentManager
from TARS.config.config import slack_settings
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from langsmith import traceable, Client
from langsmith.run_helpers import get_current_run_tree
from TARS.graphs.core_agent import run_core_agent
from TARS.metrics.event_instrumentation import IncomingUserEvent
from datetime import datetime, timezone
import uuid



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
            run_tree = get_current_run_tree()
            run_id = run_tree.id if run_tree else str(uuid.uuid4())
            self.user_run_ids[user_id] = run_id
            logging.info(f"Captured Run ID: {run_id} for user {user_id}")
            
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
        for response_part in agent_response_generator:
            # The agent now only yields content, not the run_id
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

    def get_reaction_score(self, reaction: str) -> Optional[float]:
        """
        Map emoji reactions to satisfaction scores.
        
        Args:
            reaction: The emoji reaction string.
            
        Returns:
            Score between 0.0 and 1.0, or None if reaction is not recognized.
        """
        # Positive reactions (scores 0.7-1.0)
        positive_reactions = {
            '+1': 1.0,           # thumbs up
            'thumbsup': 1.0,     # thumbs up
            'white_check_mark': 1.0,  # ✅
            'heavy_check_mark': 1.0,  # ✔️
            'heart': 1.0,        # ❤️
            'heart_eyes': 1.0,   # 😍
            'grinning': 0.8,     # 😀
            'smile': 0.8,        # 😄
            'smiley': 0.8,       # 😃
            'grin': 0.8,         # 😁
            'joy': 0.8,          # 😂
            'sunglasses': 0.8,   # 😎
            'clap': 0.8,         # 👏
            'fire': 0.8,         # 🔥
            'rocket': 0.8,       # 🚀
            'star': 0.8,         # ⭐
            'star2': 0.8,        # 🌟
            'ok_hand': 0.7,      # 👌
            'pray': 0.7,         # 🙏
            'muscle': 0.7,       # 💪
            'tada': 0.7,         # 🎉
            'party': 0.7,        # 🎊
            'trophy': 0.7,       # 🏆
            'medal': 0.7,        # 🏅
            'crown': 0.7,        # 👑
            '100': 0.7,          # 💯
            'bulb': 0.7,         # 💡
            'zap': 0.7,          # ⚡
            'sparkles': 0.7,     # ✨
            'rainbow': 0.7,      # 🌈
            'sunny': 0.7,        # ☀️
            'cherry_blossom': 0.7,  # 🌸
            'rose': 0.7,         # 🌹
            'tulip': 0.7,        # 🌷
            'four_leaf_clover': 0.7,  # 🍀
            'dart': 0.7,         # 🎯
            'target': 0.7,       # 🎯
            'checkered_flag': 0.7,  # 🏁
            'white_flag': 0.7,   # 🏳️
            'peace': 0.7,        # ☮️
            'v': 0.7,            # ✌️
            'raised_hands': 0.7, # 🙌
            'open_hands': 0.7,   # 👐
            'wave': 0.7,         # 👋
            'thumbsup_tone1': 1.0,  # 👍🏻
            'thumbsup_tone2': 1.0,  # 👍🏼
            'thumbsup_tone3': 1.0,  # 👍🏽
            'thumbsup_tone4': 1.0,  # 👍🏾
            'thumbsup_tone5': 1.0,  # 👍🏿
        }
        
        # Negative reactions (scores 0.0-0.3)
        negative_reactions = {
            '-1': 0.0,           # thumbs down
            'thumbsdown': 0.0,   # thumbs down
            'x': 0.0,            # ❌
            'heavy_multiplication_x': 0.0,  # ✖️
            'negative_squared_cross_mark': 0.0,  # ❎
            'crossed_flags': 0.0,  # 🚫
            'no_entry': 0.0,     # 🚫
            'no_entry_sign': 0.0,  # 🚫
            'prohibited': 0.0,   # 🚫
            'broken_heart': 0.1, # 💔
            'cry': 0.1,          # 😢
            'sob': 0.1,          # 😭
            'weary': 0.1,        # 😩
            'tired_face': 0.1,   # 😫
            'disappointed': 0.1, # 😞
            'disappointed_relieved': 0.1,  # 😥
            'frowning': 0.1,     # 😦
            'anguished': 0.1,    # 😧
            'fearful': 0.1,      # 😨
            'cold_sweat': 0.1,   # 😰
            'sweat': 0.1,        # 😓
            'confused': 0.2,     # 😕
            'confounded': 0.2,   # 😖
            'worried': 0.2,      # 😟
            'slight_frown': 0.2, # 🙁
            'frowning2': 0.2,    # ☹️
            'expressionless': 0.2,  # 😐
            'neutral_face': 0.2, # 😐
            'rolling_eyes': 0.2, # 🙄
            'unamused': 0.2,     # 😒
            'pensive': 0.2,      # 😔
            'sleepy': 0.2,       # 😪
            'dizzy_face': 0.2,   # 😵
            'flushed': 0.2,      # 😳
            'scream': 0.2,       # 😱
            'angry': 0.3,        # 😠
            'rage': 0.3,         # 😡
            'imp': 0.3,          # 👿
            'skull': 0.3,        # 💀
            'poop': 0.0,         # 💩
            'hankey': 0.0,       # 💩
            'shit': 0.0,         # 💩
            'thumbsdown_tone1': 0.0,  # 👎🏻
            'thumbsdown_tone2': 0.0,  # 👎🏼
            'thumbsdown_tone3': 0.0,  # 👎🏽
            'thumbsdown_tone4': 0.0,  # 👎🏾
            'thumbsdown_tone5': 0.0,  # 👎🏿
        }
        
        # Neutral reactions (scores 0.4-0.6)
        neutral_reactions = {
            'thinking_face': 0.5,  # 🤔
            'thinking': 0.5,       # 🤔
            'hushed': 0.5,         # 😯
            'astonished': 0.5,     # 😲
            'open_mouth': 0.5,     # 😮
            'yum': 0.5,            # 😋
            'stuck_out_tongue': 0.5,  # 😛
            'stuck_out_tongue_winking_eye': 0.5,  # 😜
            'stuck_out_tongue_closed_eyes': 0.5,  # 😝
            'wink': 0.5,           # 😉
            'blush': 0.5,          # 😊
            'relaxed': 0.5,        # ☺️
            'innocent': 0.5,       # 😇
            'smirk': 0.5,          # 😏
            'kissing': 0.5,        # 😗
            'kissing_heart': 0.5,  # 😘
            'kissing_smiling_eyes': 0.5,  # 😙
            'kissing_closed_eyes': 0.5,   # 😚
            'relieved': 0.5,       # 😌
            'satisfied': 0.5,      # 😆
            'laughing': 0.5,       # 😆
            'sweat_smile': 0.5,    # 😅
            'upside_down_face': 0.5,  # 🙃
            'nerd_face': 0.5,      # 🤓
            'face_with_thermometer': 0.5,  # 🤒
            'face_with_head_bandage': 0.5,  # 🤕
            'money_mouth_face': 0.5,  # 🤑
            'zipper_mouth_face': 0.5,  # 🤐
            'face_with_rolling_eyes': 0.5,  # 🙄
            'face_with_symbols_on_mouth': 0.5,  # 🤬
            'exploding_head': 0.5,  # 🤯
            'cowboy_hat_face': 0.5,  # 🤠
            'partying_face': 0.5,   # 🥳
            'disguised_face': 0.5,  # 🥸
            'pleading_face': 0.5,   # 🥺
            'yawning_face': 0.5,    # 🥱
            'smiling_face_with_tear': 0.5,  # 🥲
            'saluting_face': 0.5,   # 🫡
            'face_with_diagonal_mouth': 0.5,  # 🫤
            'dotted_line_face': 0.5,  # 🫥
            'face_with_peeking_eye': 0.5,  # 🫣
            'face_with_hand_over_mouth': 0.5,  # 🤭
            'face_with_open_eyes_and_hand_over_mouth': 0.5,  # 🫢
            'face_with_hand_over_mouth_and_peeking_eye': 0.5,  # 🫣
            'face_with_finger_covering_closed_lips': 0.5,  # 🤫
            'shushing_face': 0.5,   # 🤫
            'face_with_symbols_on_mouth_and_peeking_eye': 0.5,  # 🫣
            'face_with_hand_over_mouth_and_peeking_eye': 0.5,  # 🫣
            'face_with_hand_over_mouth_and_peeking_eye': 0.5,  # 🫣
        }
        
        # Combine all reactions
        all_reactions = {**positive_reactions, **negative_reactions, **neutral_reactions}
        
        return all_reactions.get(reaction)

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
        
        # Get score for the reaction
        score = self.get_reaction_score(reaction)
        
        if score is None:
            logging.info(f"Reaction '{reaction}' not recognized, ignoring")
            logging.info(f"Available user_run_ids: {list(self.user_run_ids.keys())}")
            return
            
        logging.info(f"Processing valid reaction: {reaction} with score: {score}")
        
        # Get the run_id for this user
        run_id = self.user_run_ids.get(user_id)
        logging.info(f"Looking up run_id for user {user_id}: {run_id}")
        
        if not run_id:
            logging.warning(f"No run_id found for user {user_id}")
            logging.info(f"Available user_run_ids: {list(self.user_run_ids.keys())}")
            return
            
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
