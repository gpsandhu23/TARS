from datetime import datetime
from typing import Generator

from config.config import graph_config
from graphs.utils.nodes import (
    call_model,
    load_memory,
    memory_manager,
    should_continue,
    tool_node,
)
from graphs.utils.state import AgentState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

memory = MemorySaver()

# Define a new graph
workflow = StateGraph(AgentState, config_schema=graph_config)

# Define the nodes
workflow.add_node("load_memory", load_memory)
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)

# Set the entrypoint as 'load_memory'
workflow.set_entry_point("load_memory")

# Add edge from 'load_memory' to 'agent'
workflow.add_edge("load_memory", "agent")

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

# Compile the graph
graph = workflow.compile(checkpointer=memory)


def run_core_agent(user_message: str, user_id: str) -> Generator[str, None, None]:
    """
    Run the core agent with the given user message and manage memory.

    Args:
        user_message (str): The message from the user
        user_id (str): Unique identifier for the user

    Yields:
        str: Each piece of the response as it becomes available
    """
    # Store user message in memory
    memory_manager.add_interaction(
        user_id,
        {
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat(),
        },
    )

    config = {"configurable": {"thread_id": user_id}}
    events = graph.stream(
        {"messages": [("user", user_message)]}, config, stream_mode="values"
    )

    for event in events:
        if "messages" in event and event["messages"]:
            yield event["messages"][-1].content
