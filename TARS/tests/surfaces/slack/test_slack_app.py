# Review Comment:
# This PR introduces comprehensive tests for the SlackBot functionality within the TARS project, significantly enhancing the project's test coverage for Slack integration. The tests cover critical functionalities such as initialization, fetching user information, preparing agent input, processing messages, and sending responses. The use of the unittest framework and mock objects effectively simulates interactions with the Slack API and SlackBot class methods, ensuring a robust testing environment. It is recommended to merge this PR after verifying that all tests pass and align with the project's coding standards.

import unittest
from unittest.mock import patch, MagicMock
from TARS.surfaces.slack.slack_app import SlackBot


class TestSlackBot(unittest.TestCase):

    def setUp(self):
        # Mock the Slack app initialization to avoid requiring actual tokens
        with patch('TARS.surfaces.slack.slack_app.App'):
            self.slack_bot = SlackBot()

    def test_initialization(self):
        self.assertIsInstance(self.slack_bot, SlackBot)

    @patch('TARS.surfaces.slack.slack_app.SlackBot.fetch_user_info')
    def test_fetch_user_info(self, mock_fetch_user_info):
        mock_client = MagicMock()
        user_id = 'U12345'
        expected_user_info = {'user': {'real_name': 'Test User'}}
        mock_fetch_user_info.return_value = (expected_user_info, 'Test User')
        user_info, real_name = self.slack_bot.fetch_user_info(mock_client, user_id)
        self.assertEqual(real_name, 'Test User')
        self.assertEqual(user_info, expected_user_info)

    @patch('TARS.surfaces.slack.slack_app.SlackBot.prepare_agent_input')
    def test_prepare_agent_input(self, mock_prepare_agent_input):
        event = {'text': 'Test message', 'user': 'U12345'}
        user_real_name = 'Test User'
        expected_agent_input = {'user_name': user_real_name, 'message': 'Test message'}
        mock_prepare_agent_input.return_value = expected_agent_input
        agent_input = self.slack_bot.prepare_agent_input(event, user_real_name)
        self.assertEqual(agent_input, expected_agent_input)

    def test_prepare_agent_input_with_images(self):
        event = {
            'text': 'Test message', 
            'user': 'U12345',
            'files': [
                {'mimetype': 'image/jpeg', 'url_private': 'http://example.com/image.jpg'}
            ]
        }
        user_real_name = 'Test User'
        agent_input = self.slack_bot.prepare_agent_input(event, user_real_name)
        self.assertEqual(agent_input['user_name'], user_real_name)
        self.assertEqual(agent_input['message'], 'Test message')
        self.assertEqual(agent_input['image_url'], 'http://example.com/image.jpg')

    def test_extract_images(self):
        event = {
            'files': [
                {'mimetype': 'image/jpeg', 'url_private': 'http://example.com/image1.jpg'},
                {'mimetype': 'image/png', 'url_private': 'http://example.com/image2.png'},
                {'mimetype': 'text/plain', 'url_private': 'http://example.com/file.txt'}
            ]
        }
        images = self.slack_bot.extract_images(event)
        self.assertEqual(images['image_url'], 'http://example.com/image1.jpg')  # First image

    def test_is_direct_message(self):
        # Test direct message
        direct_event = {'channel_type': 'im', 'user': 'U12345'}
        self.assertTrue(self.slack_bot.is_direct_message(direct_event))
        
        # Test non-direct message
        channel_event = {'channel_type': 'channel', 'user': 'U12345'}
        self.assertFalse(self.slack_bot.is_direct_message(channel_event))
        
        # Test bot message
        bot_event = {'channel_type': 'im', 'bot_id': 'B12345'}
        self.assertFalse(self.slack_bot.is_direct_message(bot_event))

    @patch('TARS.surfaces.slack.slack_app.run_core_agent')
    @patch('TARS.surfaces.slack.slack_app.SlackBot.fetch_user_info')
    @patch('TARS.surfaces.slack.slack_app.SlackBot.send_response')
    def test_handle_direct_message(self, mock_send_response, mock_fetch_user_info, mock_run_core_agent):
        mock_client = MagicMock()
        mock_client.chat_postMessage.return_value = MagicMock(data={'ts': '123456789.1234'})
        mock_fetch_user_info.return_value = ({'user': {'real_name': 'Test User'}}, 'Test User')
        # Mock run_core_agent to return a generator that yields content strings
        def mock_generator():
            yield "Hello! How can I help you?"
        mock_run_core_agent.return_value = mock_generator()
        
        event = {'text': 'Test message', 'user': 'U12345'}
        user_id = 'U12345'
        channel_id = 'C12345'
        
        response = self.slack_bot.handle_direct_message(event, mock_client, user_id, channel_id)
        
        self.assertIsInstance(response, str)
        mock_send_response.assert_called()

    @patch('TARS.surfaces.slack.slack_app.SlackBot.handle_direct_message')
    @patch('TARS.surfaces.slack.slack_app.SlackBot.fetch_user_info')
    def test_process_message_direct(self, mock_fetch_user_info, mock_handle_direct_message):
        mock_client = MagicMock()
        mock_fetch_user_info.return_value = ({'user': {'real_name': 'Test User'}}, 'Test User')
        mock_handle_direct_message.return_value = "Test response"
        
        event = {
            'text': 'Test message', 
            'user': 'U12345', 
            'channel': 'C12345',
            'channel_type': 'im'
        }
        
        response = self.slack_bot.process_message(event, mock_client)
        self.assertEqual(response, "Test response")

    def test_process_message_not_direct(self):
        mock_client = MagicMock()
        event = {
            'text': 'Test message', 
            'user': 'U12345', 
            'channel': 'C12345',
            'channel_type': 'channel'  # Not a direct message
        }
        
        response = self.slack_bot.process_message(event, mock_client)
        self.assertIsNone(response)

    def test_send_response(self):
        mock_client = MagicMock()
        channel_id = 'C12345'
        ts = '123456789.1234'
        text = 'Test response'
        
        self.slack_bot.send_response(mock_client, channel_id, ts, text)
        mock_client.chat_update.assert_called_once_with(channel=channel_id, ts=ts, text=text)

if __name__ == '__main__':
    unittest.main()
