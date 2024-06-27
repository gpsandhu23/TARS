import unittest
from unittest.mock import patch, MagicMock
from TARS.models.generic_llms.google_ai import google_llm

class TestGoogleLLM(unittest.TestCase):

    @patch('TARS.models.generic_llms.google_ai.ChatGoogleGenerativeAI')
    def test_initialization(self, mock_chat_google):
        # Test initialization with correct settings
        mock_chat_google.assert_called_with(model=google_llm.model, temperature=google_llm.temperature, api_key=google_llm.api_key)

    @patch('TARS.models.generic_llms.google_ai.ChatGoogleGenerativeAI')
    def test_response_handling(self, mock_chat_google):
        # Mock API call to simulate different responses
        mock_chat_google_instance = MagicMock()
        mock_chat_google.return_value = mock_chat_google_instance
        mock_chat_google_instance.invoke.return_value = "Test response"
        
        response = google_llm.invoke("Test input")
        self.assertEqual(response, "Test response")

if __name__ == '__main__':
    unittest.main()
