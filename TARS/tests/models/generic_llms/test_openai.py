import unittest
from unittest.mock import patch, MagicMock
from TARS.models.generic_llms.openai import openai_llm

class TestOpenAILLM(unittest.TestCase):

    @patch('TARS.models.generic_llms.openai.ChatOpenAI')
    def test_initialization(self, mock_chat_openai):
        # Test initialization with correct settings
        mock_chat_openai.assert_called_with(model=openai_llm.model, temperature=openai_llm.temperature, api_key=openai_llm.api_key)

    @patch('TARS.models.generic_llms.openai.ChatOpenAI')
    def test_response_handling(self, mock_chat_openai):
        # Mock API call to simulate different responses
        mock_chat_openai_instance = MagicMock()
        mock_chat_openai.return_value = mock_chat_openai_instance
        mock_chat_openai_instance.invoke.return_value = "Test response"
        
        response = openai_llm.invoke("Test input")
        self.assertEqual(response, "Test response")

if __name__ == '__main__':
    unittest.main()
