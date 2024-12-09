from functools import lru_cache

from config.config import (
    anthropic_settings,
    google_ai_settings,
    graph_config,
    openai_settings,
)
from graphs.utils.tools import tools
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode


@lru_cache(maxsize=4)
def _get_model(model_name: str):
    if graph_config.agent_model_name == "openai":
        model = ChatOpenAI(temperature=0, model_name=openai_settings.openai_model)
    elif graph_config.agent_model_name == "anthropic":
        model = ChatAnthropic(
            temperature=0, model_name=anthropic_settings.anthropic_model
        )
    elif graph_config.agent_model_name == "google":
        model = ChatGoogleGenerativeAI(
            temperature=0, model_name=google_ai_settings.google_ai_model
        )
    else:
        raise ValueError(f"Unsupported model type: {model_name}")

    model = model.bind_tools(tools)
    return model


# Define the function that determines whether to continue or not
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    # If there are no tool calls, then we finish
    if not last_message.tool_calls:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"


system_prompt = """Be a helpful assistant named TARS. You have a edgy, sarcastic, geeky sense of humor"""


# Define the function that calls the model
def call_model(state, config):
    messages = state["messages"]
    messages = [{"role": "system", "content": system_prompt}] + messages
    model_name = config.get("configurable", {}).get("model_name", "anthropic")
    model = _get_model(model_name)
    response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


def load_memory(state, config):
    memory = (
        "Past revelent memories from past conversations:"
        + " user is alergic to peanuts"
    )
    return {"messages": [memory]}


# Define the function to execute tools
tool_node = ToolNode(tools)
