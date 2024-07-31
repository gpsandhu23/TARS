import unittest
from unittest.mock import patch, MagicMock
from TARS.models.generic_llms.anthropic import anthropic_llm

class TestAnthropicLLM(unittest.TestCase):

    @patch('TARS.models.generic_llms.anthropic.ChatAnthropic')
    def test_initialization(self, mock_chat_anthropic):
        # Test initialization with correct settings
        mock_chat_anthropic.assert_called_with(model=anthropic_llm.model, temperature=anthropic_llm.temperature, api_key=anthropic_llm.api_key)

    @patch('TARS.models.generic_llms.anthropic.ChatAnthropic')
    def test_response_handling(self, mock_chat_anthropic):
        # Mock API call to simulate different responses
        mock_chat_anthropic_instance = MagicMock()
        mock_chat_anthropic.return_value = mock_chat_anthropic_instance
        mock_chat_anthropic_instance.invoke.return_value = "Test response"
        
        response = anthropic_llm.invoke("Test input")
        self.assertEqual(response, "Test response")

if __name__ == '__main__':
    unittest.main()
