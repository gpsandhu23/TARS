from typing import TypedDict, Literal, List, Any, Generator

from langgraph.graph import StateGraph, END
from graphs.utils.nodes import call_model, should_continue, tool_node
from graphs.utils.state import AgentState
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()


# Define the config
class GraphConfig(TypedDict):
    model_name: Literal["anthropic", "openai"]


# Define a new graph
workflow = StateGraph(AgentState, config_schema=GraphConfig)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.set_entry_point("agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    # This means these are the edges taken after the `agent` node is called.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
    # Finally we pass in a mapping.
    # The keys are strings, and the values are other nodes.
    # END is a special node marking that the graph should finish.
    # What will happen is we will call `should_continue`, and then the output of that
    # will be matched against the keys in this mapping.
    # Based on which one it matches, that node will then be called.
    {
        # If `tools`, then we call the tool node.
        "continue": "action",
        # Otherwise we finish.
        "end": END,
    },
)

# We now add a normal edge from `tools` to `agent`.
# This means that after `tools` is called, `agent` node is called next.
workflow.add_edge("action", "agent")

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable
graph = workflow.compile(checkpointer=memory)

def run_core_agent(user_message: str, user_id: str) -> Generator[str, None, None]:
    """
    Run the core agent with the given user message and chat history.
    Yields each piece of the response as it becomes available.
    """
    config = {"configurable": {"thread_id": user_id}}
    events = graph.stream(
        {"messages": [("user", user_message)]}, config, stream_mode="values"
    )
    for event in events:
        print(f"event: {event}")
        print(f"type(event): {type(event)}")
        print(f"event['messages']: {event['messages']}")
        print(f"type(event['messages']): {type(event['messages'])}")
        print(f"event['messages'][-1]: {event['messages'][-1]}")
        print(f"type(event['messages'][-1]): {type(event['messages'][-1])}")
        print(f"event['messages'][-1].content: {event['messages'][-1].content}")
        print(f"type(event['messages'][-1].content): {type(event['messages'][-1].content)}")
        print(f"event['messages'][-1].content: {event['messages'][-1].content}")
        print(f"type(event['messages'][-1].content): {type(event['messages'][-1].content)}")
        yield event["messages"][-1].content