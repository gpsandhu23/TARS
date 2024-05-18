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
