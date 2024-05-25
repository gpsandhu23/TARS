import unittest
from unittest import mock
from fastapi.testclient import TestClient
from surfaces.API.api import app
from graphs.agent import AgentManager

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_chat_endpoint_success(self):
        response = self.client.post("/chat", json={"message": "Hello", "user_name": "TestUser"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("response", response.json())
        self.assertIsInstance(response.json()["response"], str)

    def test_chat_endpoint_invalid_input(self):
        response = self.client.post("/chat", json={})
        self.assertEqual(response.status_code, 422)

    def test_chat_endpoint_error_handling(self):
        with unittest.mock.patch.object(AgentManager, 'process_user_task', side_effect=Exception("Test Error")):
            response = self.client.post("/chat", json={"message": "Hello", "user_name": "TestUser"})
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json(), {"detail": "Internal Server Error"})

    def test_github_oauth_callback_success(self):
        with mock.patch('surfaces.API.api.exchange_code_for_access_token', return_value="mock_access_token"), \
             mock.patch('surfaces.API.api.validate_access_token_and_retrieve_user_info', return_value={"user": "mock_user"}):
            response = self.client.get("/auth/github/callback", params={"code": "mock_code"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "success", "user_info": {"user": "mock_user"}})

    def test_github_oauth_callback_missing_code(self):
        response = self.client.get("/auth/github/callback")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Missing 'code' in the callback request"})

    def test_github_oauth_callback_exchange_failure(self):
        with mock.patch('surfaces.API.api.exchange_code_for_access_token', return_value=None):
            response = self.client.get("/auth/github/callback", params={"code": "mock_code"})
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json(), {"detail": "Failed to exchange 'code' for an access token"})

    def test_github_oauth_callback_user_info_failure(self):
        with mock.patch('surfaces.API.api.exchange_code_for_access_token', return_value="mock_access_token"), \
             mock.patch('surfaces.API.api.validate_access_token_and_retrieve_user_info', return_value=None):
            response = self.client.get("/auth/github/callback", params={"code": "mock_code"})
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json(), {"detail": "Failed to validate access token or retrieve user information"})
