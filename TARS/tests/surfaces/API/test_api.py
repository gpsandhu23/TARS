import unittest
from unittest import mock
from fastapi.testclient import TestClient
from TARS.surfaces.API.api import app, ChatRequest
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
        self.assertIsInstance(response.json()["response"], str)

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
        self.assertEqual(response.json(), {"message": "API is working!"})

    @patch('TARS.surfaces.API.api.exchange_code_for_access_token')
    @patch('TARS.surfaces.API.api.validate_access_token_and_retrieve_user_info')
    def test_github_oauth_callback_success(self, mock_validate_token, mock_exchange_code):
        mock_exchange_code.return_value = "mock_access_token"
        mock_validate_token.return_value = {"user": "mock_user"}
        
        response = self.client.get("/auth/github/callback", params={"code": "mock_code"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "user_info": {"user": "mock_user"}})

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
