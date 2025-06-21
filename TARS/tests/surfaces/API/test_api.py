import unittest
from unittest import mock
from fastapi.testclient import TestClient
from TARS.surfaces.API.api import app, ChatRequest, FeedbackRequest
from unittest.mock import patch, MagicMock


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch('TARS.surfaces.API.api.run_core_agent')
    def test_chat_endpoint_success(self, mock_run_core_agent):
        # Mock the core agent to return a simple response
        mock_run_core_agent.return_value = iter(["Hello! How can I help you?"])
        
        response = self.client.post("/chat", json={"message": "Hello", "user_name": "TestUser"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("response", response.json())
        self.assertIn("run_id", response.json())
        self.assertIsInstance(response.json()["response"], str)
        self.assertIsInstance(response.json()["run_id"], str)

    def test_chat_endpoint_invalid_input(self):
        response = self.client.post("/chat", json={})
        self.assertEqual(response.status_code, 422)

    @patch('TARS.surfaces.API.api.run_core_agent')
    def test_chat_endpoint_error_handling(self, mock_run_core_agent):
        # Mock the core agent to raise an exception
        mock_run_core_agent.side_effect = Exception("Test Error")
        
        response = self.client.post("/chat", json={"message": "Hello", "user_name": "TestUser"})
        self.assertEqual(response.status_code, 200)  # API returns 200 even on error
        self.assertIn("error", response.json()["response"].lower())

    @patch('TARS.surfaces.API.api.run_core_agent')
    def test_chat_endpoint_empty_response(self, mock_run_core_agent):
        # Mock the core agent to return empty response
        mock_run_core_agent.return_value = iter([])
        
        response = self.client.post("/chat", json={"message": "Hello", "user_name": "TestUser"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("response", response.json())
        self.assertIn("didn't receive a proper response", response.json()["response"])

    def test_test_endpoint(self):
        response = self.client.get("/test")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Hola! Welcome to our API!"})

    # Feedback endpoint tests
    @patch('TARS.surfaces.API.api.langsmith_client')
    def test_feedback_endpoint_success(self, mock_langsmith_client):
        # First, create a chat to get a run_id
        with patch('TARS.surfaces.API.api.run_core_agent') as mock_run_core_agent:
            mock_run_core_agent.return_value = iter(["Test response"])
            
            chat_response = self.client.post("/chat", json={
                "message": "Hello", 
                "user_name": "TestUser"
            })
            self.assertEqual(chat_response.status_code, 200)
        
        # Mock LangSmith client response
        mock_feedback_result = MagicMock()
        mock_feedback_result.id = "test_feedback_id"
        mock_langsmith_client.create_feedback.return_value = mock_feedback_result
        
        # Submit feedback
        feedback_response = self.client.post("/feedback", json={
            "user_name": "TestUser",
            "satisfaction_score": 0.8,
            "comment": "Great response!"
        })
        
        self.assertEqual(feedback_response.status_code, 200)
        result = feedback_response.json()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Feedback submitted successfully")
        self.assertEqual(result["feedback_id"], "test_feedback_id")
        
        # Verify LangSmith was called correctly
        mock_langsmith_client.create_feedback.assert_called_once_with(
            key="user_satisfaction",
            score=0.8,
            run_id=mock.ANY,  # We don't know the exact run_id
            comment="Great response!"
        )

    def test_feedback_endpoint_invalid_score_too_high(self):
        response = self.client.post("/feedback", json={
            "user_name": "TestUser",
            "satisfaction_score": 1.5,  # Invalid: > 1.0
            "comment": "Test comment"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Satisfaction score must be between 0.0 and 1.0", response.json()["detail"])

    def test_feedback_endpoint_invalid_score_too_low(self):
        response = self.client.post("/feedback", json={
            "user_name": "TestUser",
            "satisfaction_score": -0.1,  # Invalid: < 0.0
            "comment": "Test comment"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Satisfaction score must be between 0.0 and 1.0", response.json()["detail"])

    def test_feedback_endpoint_missing_user_conversation(self):
        response = self.client.post("/feedback", json={
            "user_name": "UserWithoutChat",
            "satisfaction_score": 0.8,
            "comment": "Test comment"
        })
        self.assertEqual(response.status_code, 404)
        self.assertIn("No recent conversation found for this user", response.json()["detail"])

    def test_feedback_endpoint_invalid_input(self):
        response = self.client.post("/feedback", json={})
        self.assertEqual(response.status_code, 422)

    def test_feedback_endpoint_missing_user_name(self):
        response = self.client.post("/feedback", json={
            "satisfaction_score": 0.8,
            "comment": "Test comment"
        })
        self.assertEqual(response.status_code, 422)

    def test_feedback_endpoint_missing_satisfaction_score(self):
        response = self.client.post("/feedback", json={
            "user_name": "TestUser",
            "comment": "Test comment"
        })
        self.assertEqual(response.status_code, 422)

    @patch('TARS.surfaces.API.api.langsmith_client')
    def test_feedback_endpoint_langsmith_error(self, mock_langsmith_client):
        # First, create a chat to get a run_id
        with patch('TARS.surfaces.API.api.run_core_agent') as mock_run_core_agent:
            mock_run_core_agent.return_value = iter(["Test response"])
            
            chat_response = self.client.post("/chat", json={
                "message": "Hello", 
                "user_name": "TestUser"
            })
            self.assertEqual(chat_response.status_code, 200)
        
        # Mock LangSmith client to raise an exception
        mock_langsmith_client.create_feedback.side_effect = Exception("LangSmith error")
        
        # Submit feedback
        feedback_response = self.client.post("/feedback", json={
            "user_name": "TestUser",
            "satisfaction_score": 0.8,
            "comment": "Test comment"
        })
        
        self.assertEqual(feedback_response.status_code, 500)
        self.assertIn("Failed to submit feedback to LangSmith", feedback_response.json()["detail"])

    @patch('TARS.surfaces.API.api.langsmith_client')
    def test_feedback_endpoint_without_comment(self, mock_langsmith_client):
        # First, create a chat to get a run_id
        with patch('TARS.surfaces.API.api.run_core_agent') as mock_run_core_agent:
            mock_run_core_agent.return_value = iter(["Test response"])
            
            chat_response = self.client.post("/chat", json={
                "message": "Hello", 
                "user_name": "TestUser"
            })
            self.assertEqual(chat_response.status_code, 200)
        
        # Mock LangSmith client response
        mock_feedback_result = MagicMock()
        mock_feedback_result.id = "test_feedback_id"
        mock_langsmith_client.create_feedback.return_value = mock_feedback_result
        
        # Submit feedback without comment
        feedback_response = self.client.post("/feedback", json={
            "user_name": "TestUser",
            "satisfaction_score": 0.9
        })
        
        self.assertEqual(feedback_response.status_code, 200)
        result = feedback_response.json()
        self.assertEqual(result["status"], "success")
        
        # Verify LangSmith was called with empty comment
        mock_langsmith_client.create_feedback.assert_called_once_with(
            key="user_satisfaction",
            score=0.9,
            run_id=mock.ANY,
            comment=""
        )

    @patch('TARS.surfaces.API.api.langsmith_client')
    def test_feedback_endpoint_boundary_values(self, mock_langsmith_client):
        # First, create a chat to get a run_id
        with patch('TARS.surfaces.API.api.run_core_agent') as mock_run_core_agent:
            mock_run_core_agent.return_value = iter(["Test response"])
            
            chat_response = self.client.post("/chat", json={
                "message": "Hello", 
                "user_name": "TestUser"
            })
            self.assertEqual(chat_response.status_code, 200)
        
        # Mock LangSmith client response
        mock_feedback_result = MagicMock()
        mock_feedback_result.id = "test_feedback_id"
        mock_langsmith_client.create_feedback.return_value = mock_feedback_result
        
        # Test boundary values (0.0 and 1.0 should be valid)
        for score in [0.0, 1.0]:
            feedback_response = self.client.post("/feedback", json={
                "user_name": "TestUser",
                "satisfaction_score": score,
                "comment": f"Test score {score}"
            })
            
            self.assertEqual(feedback_response.status_code, 200)
            result = feedback_response.json()
            self.assertEqual(result["status"], "success")

    @patch('TARS.surfaces.API.api.exchange_code_for_access_token')
    @patch('TARS.surfaces.API.api.validate_access_token_and_retrieve_user_info')
    def test_github_oauth_callback_success(self, mock_validate_token, mock_exchange_code):
        mock_exchange_code.return_value = "mock_access_token"
        mock_validate_token.return_value = {"user": "mock_user"}
        
        response = self.client.get("/auth/github/callback", params={"code": "mock_code"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "user_info": {"user": "mock_user"}, "user_token": "mock_access_token"})

    def test_github_oauth_callback_missing_code(self):
        response = self.client.get("/auth/github/callback")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Missing 'code' in the callback request"})

    @patch('TARS.surfaces.API.api.exchange_code_for_access_token')
    def test_github_oauth_callback_exchange_failure(self, mock_exchange_code):
        mock_exchange_code.return_value = None
        
        response = self.client.get("/auth/github/callback", params={"code": "mock_code"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Failed to exchange 'code' for an access token"})

    @patch('TARS.surfaces.API.api.exchange_code_for_access_token')
    @patch('TARS.surfaces.API.api.validate_access_token_and_retrieve_user_info')
    def test_github_oauth_callback_user_info_failure(self, mock_validate_token, mock_exchange_code):
        mock_exchange_code.return_value = "mock_access_token"
        mock_validate_token.return_value = None
        
        response = self.client.get("/auth/github/callback", params={"code": "mock_code"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Failed to validate access token or retrieve user information"})
