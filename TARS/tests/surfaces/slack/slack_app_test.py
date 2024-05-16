import unittest
from unittest.mock import patch, MagicMock
from surfaces.slack.slack_app import SlackBot

class TestSlackBot(unittest.TestCase):

    def setUp(self):
        self.slack_bot = SlackBot()

    def test_initialization(self):
        self.assertIsInstance(self.slack_bot, SlackBot)

    @patch('surfaces.slack.slack_app.SlackBot.fetch_user_info')
    def test_fetch_user_info(self, mock_fetch_user_info):
        mock_client = MagicMock()
        user_id = 'U12345'
        expected_user_info = {'user': {'real_name': 'Test User'}}
        mock_fetch_user_info.return_value = (expected_user_info, 'Test User')
        user_info, real_name = self.slack_bot.fetch_user_info(mock_client, user_id)
        self.assertEqual(real_name, 'Test User')
        self.assertEqual(user_info, expected_user_info)

    @patch('surfaces.slack.slack_app.SlackBot.prepare_agent_input')
    def test_prepare_agent_input(self, mock_prepare_agent_input):
        event = {'text': 'Test message', 'user': 'U12345'}
        user_real_name = 'Test User'
        expected_agent_input = {'user_name': user_real_name, 'message': 'Test message'}
        mock_prepare_agent_input.return_value = expected_agent_input
        agent_input = self.slack_bot.prepare_agent_input(event, user_real_name)
        self.assertEqual(agent_input, expected_agent_input)

    @patch('surfaces.slack.slack_app.SlackBot.process_message')
    def test_process_message(self, mock_process_message):
        event = {'text': 'Test message', 'user': 'U12345', 'channel': 'C12345'}
        mock_client = MagicMock()
        self.slack_bot.process_message(event, mock_client)
        mock_process_message.assert_called_once()

    @patch('surfaces.slack.slack_app.SlackBot.send_response')
    def test_send_response(self, mock_send_response):
        mock_client = MagicMock()
        channel_id = 'C12345'
        ts = '123456789.1234'
        text = 'Test response'
        self.slack_bot.send_response(mock_client, channel_id, ts, text)
        mock_send_response.assert_called_once_with(mock_client, channel_id, ts, text)

if __name__ == '__main__':
    unittest.main()
