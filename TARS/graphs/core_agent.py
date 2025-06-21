from datetime import datetime
from typing import Generator, Tuple
import logging

from TARS.config.config import GraphConfig
from TARS.graphs.utils.nodes import (
    call_model,
    should_continue,
    tool_node,
)
from TARS.graphs.utils.state import AgentState
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph

# Setup logging
logger = logging.getLogger(__name__)

# Define a new graph
workflow = StateGraph(AgentState, config_schema=GraphConfig)

# Define the nodes
# workflow.add_node("load_memory", load_memory)
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)

# Set the entrypoint as 'agent'
workflow.set_entry_point("agent")


# Add conditional edges
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "action",
        "end": END,
    },
)

# Add edge from 'action' to 'agent'
workflow.add_edge("action", "agent")

# Compile the graph without custom checkpointer
graph = workflow.compile()
logger.info("Core agent graph compiled successfully")


def run_core_agent(user_name: str, message: str) -> Generator:
    """
    Run the core agent with the given user name and message.

    Args:
        user_name (str): The name of the user
        message (str): The message from the user

    Yields:
        The content of the agent's response.
    """
    logger.info(f"=== CORE AGENT START ===")
    logger.info(f"Input - user_name: {user_name}, message: {message}")

    if user_name is None:
        logger.error("Invalid input: user_name is None")
        raise ValueError("Invalid input: user_name is None")
    
    if message is None:
        logger.error("Invalid input: message is None")
        raise ValueError("Invalid input: message is None")
    
    try:
        logger.info("Inside run_core_agent try block")
        config: RunnableConfig = {"configurable": {"thread_id": user_name}}
        logger.info(f"Created config: {config}")
        
        def response_generator():
            try:
                logger.info("Starting graph stream...")
                events = graph.stream(
                    {"messages": [("user", message)]}, config=config, stream_mode="values"
                )
                logger.info("Successfully started graph stream")

                event_count = 0
                for event in events:
                    event_count += 1
                    logger.info(f"Processing event #{event_count}: {event}")
                    
                    if "messages" in event and event["messages"]:
                        last_message = event["messages"][-1]
                        logger.info(f"Extracting content from message: {last_message}")
                        content = last_message.content
                        logger.info(f"Yielding content: '{content}'")
                        yield content
                    else:
                        logger.warning(f"Event #{event_count} has no messages or empty messages: {event}")

                logger.info(f"Completed processing {event_count} events")
                logger.info("=== CORE AGENT SUCCESS ===")
            except Exception as e:
                logger.error(f"Error in run_core_agent: {str(e)}", exc_info=True)
                logger.info("=== CORE AGENT ERROR ===")
                yield f"An error occurred in the core agent: {str(e)}"

        return response_generator()
    except Exception as e:
        logger.error(f"Error in run_core_agent setup: {str(e)}", exc_info=True)
        logger.info("=== CORE AGENT SETUP ERROR ===")
        def error_generator():
            yield f"An error occurred in the core agent setup: {str(e)}"
        return error_generator()
