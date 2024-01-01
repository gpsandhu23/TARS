import os
import logging
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.render import format_tool_to_openai_function
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents import AgentExecutor, load_tools
from langchain.tools import YahooFinanceNewsTool, YouTubeSearchTool
from langchain.agents.agent_toolkits import SlackToolkit
from .custom_tools import get_word_length, handle_all_unread_gmail, read_image_tool, fetch_dms_last_x_hours

# Setup logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Define the LLM to use
llm = ChatOpenAI(model="gpt-4-1106-preview", temperature=0)

# Combine all tools
custom_tools = [get_word_length, handle_all_unread_gmail, read_image_tool, fetch_dms_last_x_hours]
request_tools = load_tools(["requests_all"])
weather_tools = load_tools(["openweathermap-api"])
finance_tools = [YahooFinanceNewsTool()]
slack_tools = SlackToolkit().get_tools()
youtube_tools = [YouTubeSearchTool()]

tools = custom_tools + request_tools + weather_tools + finance_tools + slack_tools + youtube_tools
llm_with_tools = llm.bind(functions=[format_tool_to_openai_function(t) for t in tools])

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
    | OpenAIFunctionsAgentOutputParser()
)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def process_user_task(user_task, chat_history):
    """
    Process the user task using the agent and update the chat history.
    
    :param user_task: The task input by the user.
    :param chat_history: The current chat history.
    :return: The output from the agent.
    """
    try:
        result = agent_executor.invoke({"input": user_task, "chat_history": chat_history})
        chat_history.extend([
            HumanMessage(content=user_task),
            AIMessage(content=result["output"]),
        ])
        return result["output"]
    except Exception as e:
        logging.error(f"Error in process_user_task: {e}")
        return "An error occurred while processing the task."