import unittest
from graphs.agent import AgentManager

class TestAgentManager(unittest.TestCase):
    def setUp(self):
        self.agent_manager = AgentManager()

    def test_process_user_task_valid_input(self):
        valid_input = "What's the weather like today?"
        expected_output = "I'm sorry, but I can't provide real-time data."
        output = self.agent_manager.process_user_task(valid_input)
        self.assertIn(expected_output, output)

    def test_process_user_task_invalid_input(self):
        invalid_input = ""
        with self.assertRaises(ValueError):
            self.agent_manager.process_user_task(invalid_input)

    def test_define_prompt(self):
        prompt = self.agent_manager.define_prompt()
        self.assertTrue(isinstance(prompt, str))
        self.assertIn("You are a helpful AI assistant named TARS.", prompt)

    def test_load_all_tools(self):
        tools = self.agent_manager.load_all_tools()
        self.assertTrue(isinstance(tools, list))
        self.assertGreater(len(tools), 0)
