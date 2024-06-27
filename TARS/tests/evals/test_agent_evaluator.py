import unittest
from unittest.mock import patch, MagicMock
from evals.agent_evaluator import evaluate_prediction

class TestAgentEvaluator(unittest.TestCase):

    @patch('evals.agent_evaluator.load_evaluator')
    def test_evaluate_prediction_success(self, mock_load_evaluator):
        # Setup mock response
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate_strings.return_value = {"score": 0.9}
        mock_load_evaluator.return_value = mock_evaluator

        # Test evaluate_prediction
        prediction = "This is a test prediction"
        input_question = "What is a test prediction?"
        result = evaluate_prediction(prediction, input_question)
        self.assertEqual(result, {"score": 0.9})

    @patch('evals.agent_evaluator.load_evaluator')
    def test_evaluate_prediction_invalid_input(self, mock_load_evaluator):
        # Setup mock response
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate_strings.side_effect = ValueError("Invalid input")
        mock_load_evaluator.return_value = mock_evaluator

        # Test evaluate_prediction with invalid input
        prediction = ""
        input_question = ""
        with self.assertRaises(ValueError):
            evaluate_prediction(prediction, input_question)

    @patch('evals.agent_evaluator.load_evaluator')
    def test_evaluate_prediction_edge_case(self, mock_load_evaluator):
        # Setup mock response for an edge case
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate_strings.return_value = {"score": 0.0}  # Edge case: lowest possible score
        mock_load_evaluator.return_value = mock_evaluator

        # Test evaluate_prediction with edge case input
        prediction = "Irrelevant prediction"
        input_question = "What is the meaning of life?"
        result = evaluate_prediction(prediction, input_question)
        self.assertEqual(result, {"score": 0.0})
