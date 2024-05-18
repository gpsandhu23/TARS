import unittest
from graphs.agent import AgentManager
from langchain.prompts import ChatPromptTemplate


class TestAgentManager(unittest.TestCase):
    def setUp(self):
        self.agent_manager = AgentManager()

    def test_process_user_task_valid_input(self):
        # Note: process_user_task's output is not completely deterministic due to LLM usage
        valid_input = "What's the weather like today?"
        output = self.agent_manager.process_user_task(valid_input)
        self.assertIsInstance(output, str)

    def test_process_user_task_invalid_input(self):
        invalid_input = None
        with self.assertRaises(Exception):
            self.agent_manager.process_user_task(invalid_input)

    def test_define_prompt(self):
        prompt = self.agent_manager.define_prompt()
        self.assertTrue(isinstance(prompt, ChatPromptTemplate))

    def test_load_all_tools(self):
        tools = self.agent_manager.load_all_tools()
        self.assertTrue(len(tools) > 0)
