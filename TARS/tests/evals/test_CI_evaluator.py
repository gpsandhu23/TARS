import unittest
from unittest.mock import patch, MagicMock
from evals.CI_evaluator import evaluate_single_prediction, process_evaluations

class TestCIEvaluator(unittest.TestCase):

    @patch('evals.CI_evaluator.process_user_task')
    @patch('evals.CI_evaluator.load_evaluator')
    def test_evaluate_single_prediction_success(self, mock_load_evaluator, mock_process_user_task):
        # Setup mock response
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate_strings.return_value = {"score": 0.8}
        mock_load_evaluator.return_value = mock_evaluator
        mock_process_user_task.return_value = "Test prediction"

        # Test evaluate_single_prediction
        input_text = "Test input"
        reference = "Test reference"
        result = evaluate_single_prediction(input_text, reference)
        self.assertEqual(result, {"score": 0.8})

    @patch('evals.CI_evaluator.process_user_task')
    @patch('evals.CI_evaluator.load_evaluator')
    def test_evaluate_single_prediction_error_handling(self, mock_load_evaluator, mock_process_user_task):
        # Setup mock response to simulate an error
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate_strings.side_effect = Exception("Evaluation error")
        mock_load_evaluator.return_value = mock_evaluator
        mock_process_user_task.return_value = "Test prediction"

        # Test evaluate_single_prediction with error handling
        input_text = "Test input"
        reference = "Test reference"
        with self.assertRaises(Exception):
            evaluate_single_prediction(input_text, reference)

    @patch('evals.CI_evaluator.evaluate_single_prediction')
    def test_process_evaluations(self, mock_evaluate_single_prediction):
        # Setup mock response
        mock_evaluate_single_prediction.return_value = {"score": 0.8}

        # Test process_evaluations with a mock file path
        file_path = "mock_file_path.jsonl"
        with patch('builtins.open', unittest.mock.mock_open(read_data='{"input": "Test input", "ideal": "Test ideal"}\n')) as mock_file:
            process_evaluations(file_path)
            mock_file.assert_called_with(file_path, 'r')
            mock_evaluate_single_prediction.assert_called_with("Test input", "Test ideal")
