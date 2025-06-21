import unittest
from unittest.mock import patch, MagicMock
from TARS.graphs.core_agent import run_core_agent


class TestCoreAgent(unittest.TestCase):
    def setUp(self):
        pass

    @patch('TARS.graphs.core_agent.graph')
    def test_run_core_agent_valid_input(self, mock_graph):
        # Mock the graph stream to return a simple response
        mock_events = [
            {"messages": [MagicMock(content="Test response")]}
        ]
        mock_graph.stream.return_value = mock_events
        
        # Test with valid input
        user_name = "test_user_123"
        message = "What's the weather like today?"
        
        # Get the generator and run_id
        response_generator, run_id = run_core_agent(user_name, message)
        
        # Collect all responses
        responses = list(response_generator)
        
        # Verify the response
        self.assertTrue(len(responses) > 0)
        self.assertIsInstance(responses[0], str)
        self.assertEqual(responses[0], "Test response")
        # Verify run_id is returned (may be None in test environment)
        self.assertIsInstance(run_id, (str, type(None)))

    def test_run_core_agent_invalid_input(self):
        # Test with None input
        with self.assertRaises(ValueError):
            run_core_agent(None, "test_user")

    @patch('TARS.graphs.core_agent.graph')
    def test_run_core_agent_empty_response(self, mock_graph):
        # Mock the graph stream to return empty events
        mock_graph.stream.return_value = []
        
        user_name = "test_user_123"
        message = "Test message"
        
        # Get the generator and run_id
        response_generator, run_id = run_core_agent(user_name, message)
        
        # Collect all responses
        responses = list(response_generator)
        
        # Should handle empty response gracefully
        self.assertEqual(len(responses), 0)
        # Verify run_id is returned (may be None in test environment)
        self.assertIsInstance(run_id, (str, type(None)))

    @patch('TARS.graphs.core_agent.graph')
    def test_run_core_agent_exception_handling(self, mock_graph):
        # Mock the graph to raise an exception
        mock_graph.stream.side_effect = Exception("Test error")
        
        user_name = "test_user_123"
        message = "Test message"
        
        # Get the generator and run_id
        response_generator, run_id = run_core_agent(user_name, message)
        
        # Collect all responses
        responses = list(response_generator)
        
        # Should return error message
        self.assertTrue(len(responses) > 0)
        self.assertIn("error", responses[0].lower())
        # Verify run_id is None when there's an error
        self.assertIsNone(run_id)
