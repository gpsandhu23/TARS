import os
import logging
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.render import format_tool_to_openai_function
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import ToolsAgentOutputParser
from langchain.agents import AgentExecutor, load_tools
from langchain.tools import YahooFinanceNewsTool, YouTubeSearchTool
from langchain.agents.agent_toolkits import SlackToolkit

from models.generic_llms.openai import openai_llm
from models.generic_llms.anthropic import anthropic_llm

from .custom_tools import get_word_length, handle_all_unread_gmail, fetch_emails_by_sender_name, read_image_tool, fetch_dms_last_x_hours, fetch_calendar_events_for_x_days

# Setup logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Define the LLM to use
llm = openai_llm
# llm = anthropic_llm

# Combine all tools
custom_tools = [get_word_length, handle_all_unread_gmail, read_image_tool, fetch_dms_last_x_hours, fetch_calendar_events_for_x_days, fetch_emails_by_sender_name]
request_tools = load_tools(["requests_all"])
weather_tools = load_tools(["openweathermap-api"])
finance_tools = [YahooFinanceNewsTool()]
slack_tools = SlackToolkit().get_tools()
youtube_tools = [YouTubeSearchTool()]

tools = custom_tools + request_tools + weather_tools + finance_tools + slack_tools + youtube_tools

# Check what llm is being used and bind appropriate tools
if llm == openai_llm:
    llm_with_tools = llm.bind(functions=[format_tool_to_openai_function(t) for t in tools])
elif llm == anthropic_llm:
    llm_with_tools = llm.bind_tools(tools)


# Define the chat prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant named TARS. You have a geeky, clever, sarcastic, and edgy sense of humor. You were created by GP to help me be more efficient."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Define the agent
agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_function_messages(x["intermediate_steps"]),
        "chat_history": lambda x: x["chat_history"],
    }
    | prompt
    | llm_with_tools
    | ToolsAgentOutputParser(tools=tools)
)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def process_user_task(user_task, chat_history=None):
    """
    Process the user task using the agent. Update the chat history if provided.
    
    :param user_task: The task input by the user.
    :param chat_history: The current chat history. If None, an empty list is used.
    :return: The output from the agent.
    """
    try:
        # Initialize chat_history as an empty list if None is provided
        if chat_history is None:
            chat_history = []

        invoke_params = {"input": user_task, "chat_history": chat_history}

        result = agent_executor.invoke(invoke_params)

        # Update chat history
        chat_history.extend([
            HumanMessage(content=user_task),
            AIMessage(content=result["output"]),
        ])
        return result["output"]
    except Exception as e:
        logging.error(f"Error in process_user_task: {e}")
        return "An error occurred while processing the task."
    
# output = process_user_task("Where are my socks?")
# print(output)