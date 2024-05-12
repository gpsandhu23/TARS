from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import AgentExecutor
import logging
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Setup logging
logging.basicConfig(level=logging.INFO)


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

        invoke_params = str({"input": user_task, "chat_history": chat_history})

        # Define the LLM to use
        llm1 = ChatOpenAI(model="gpt-4-turbo", temperature=0)
        llm2 = ChatAnthropic(model="claude-3-opus-20240229", temperature=0)

        result = llm1.invoke(invoke_params)

        # # Update chat history
        # chat_history.extend([
        #     HumanMessage(content=user_task),
        #     AIMessage(content=result["output"]),
        # ])
        return str(result)
    except Exception as e:
        logging.error(f"Error in process_user_task: {e}")
        return "An error occurred while processing the task."