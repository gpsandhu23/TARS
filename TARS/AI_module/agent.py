from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.render import format_tool_to_openai_function
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain.agents import load_tools

# import tools
from tools import get_word_length, handle_all_unread_messages

# Load environment variables from .env file
load_dotenv()

# Define the LLM to use
llm = ChatOpenAI(model="gpt-4-1106-preview", temperature=0)

tools = [get_word_length, handle_all_unread_messages]
requests_tools = load_tools(["requests_all"])
tools = tools + requests_tools

llm_with_tools = llm.bind(functions=[format_tool_to_openai_function(t) for t in tools])

# Add memory and the prompt
MEMORY_KEY = "chat_history"
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an AI assistant named TARS. You have a geeky, clever, and edgy sense of humor.",
        ),
        MessagesPlaceholder(variable_name=MEMORY_KEY),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# Define the agent
agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_function_messages(
            x["intermediate_steps"]
        ),
        "chat_history": lambda x: x["chat_history"],
    }
    | prompt
    | llm_with_tools
    | OpenAIFunctionsAgentOutputParser()
)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

chat_history = []

while True:
    # Get user input
    user_task = input("Enter your query (or type 'exit' to quit): ")
    
    # Check if the user wants to exit
    if user_task.lower() == 'exit':
        break

    # Process the input using the agent
    result = agent_executor.invoke({"input": user_task, "chat_history": chat_history})
    
    # Append the conversation to the chat history
    chat_history.extend(
        [
            HumanMessage(content=user_task),
            AIMessage(content=result["output"]),
        ]
    )
    
    # Display the result
    print("Agent Response:", result["output"])