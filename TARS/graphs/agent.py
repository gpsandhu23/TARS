import logging
import os
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import AgentExecutor, load_tools, create_tool_calling_agent
from langchain.tools import YahooFinanceNewsTool, YouTubeSearchTool
from langchain.agents.agent_toolkits import SlackToolkit

from config.config import llm_settings
from models.generic_llms.openai import openai_llm
from models.generic_llms.anthropic import anthropic_llm
from models.generic_llms.google_ai import google_llm

from .custom_tools import get_word_length, handle_all_unread_gmail, fetch_emails_by_sender_name, read_image_tool, fetch_dms_last_x_hours, fetch_calendar_events_for_x_days

class AgentManager:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        load_dotenv()
        llm_type = llm_settings.llm_type
        if llm_type == 'openai':
            self.llm = openai_llm
        elif llm_type == 'google':
            self.llm = google_llm
        elif llm_type == 'anthropic':
            self.llm = anthropic_llm
        else:
            raise ValueError(f"Unsupported LLM type: {llm_type}")
        self.tools = self.load_all_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.prompt = self.define_prompt()
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    def load_all_tools(self):
        custom_tools = [get_word_length, handle_all_unread_gmail, read_image_tool, fetch_dms_last_x_hours, fetch_calendar_events_for_x_days, fetch_emails_by_sender_name]
        request_tools = load_tools(["requests_all"])
        weather_tools = load_tools(["openweathermap-api"])
        finance_tools = [YahooFinanceNewsTool()]
        slack_tools = SlackToolkit().get_tools()
        youtube_tools = [YouTubeSearchTool()]
        return custom_tools + request_tools + weather_tools + finance_tools + slack_tools + youtube_tools

    def define_prompt(self):
        return ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant named TARS. You have a geeky, clever, sarcastic, and edgy sense of humor. You were created by GP to help me be more efficient."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    def process_user_task(self, user_task, chat_history=None):
        if user_task is None:
            raise ValueError("user_task cannot be None")
        try:
            if chat_history is None:
                chat_history = []
            invoke_params = {"input": user_task, "chat_history": chat_history}
            result = self.agent_executor.invoke(invoke_params)
            chat_history.extend([
                HumanMessage(content=user_task),
                AIMessage(content=result["output"]),
            ])
            return result["output"]
        except Exception as e:
            logging.error(f"Error in process_user_task: {e}")
            return "An error occurred while processing the task."
