from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List

from config.config import (
    anthropic_settings,
    google_ai_settings,
    graph_config,
    openai_settings,
)
from graphs.utils.tools import tools
from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores import Chroma
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel


class Memory(BaseModel):
    short_term: List[Dict[str, Any]]
    summary: str = ""
    last_summarized: datetime = None
    user_profile: Dict[str, Any] = {}


class MemoryManager:
    def __init__(self):
        self.memory_store = {}
        self.vectorstore = Chroma(
            collection_name="long_term_memory", embedding_function=OpenAIEmbeddings()
        )
        self.summary_threshold = 10  # Messages before summarizing

    def get_or_create_memory(self, user_id: str) -> Memory:
        if user_id not in self.memory_store:
            self.memory_store[user_id] = Memory(short_term=[])
        return self.memory_store[user_id]

    def add_interaction(self, user_id: str, message: Dict[str, Any]):
        memory = self.get_or_create_memory(user_id)
        memory.short_term.append(message)

        if len(memory.short_term) >= self.summary_threshold:
            self._summarize_and_store(user_id)

    def get_context(self, user_id: str, query: str) -> str:
        memory = self.get_or_create_memory(user_id)
        recent_context = memory.short_term[-5:] if memory.short_term else []

        # Get relevant long-term memories
        relevant_docs = self.vectorstore.similarity_search(query, k=2)
        long_term_context = "\n".join(doc.page_content for doc in relevant_docs)

        return f"""Summary: {memory.summary}
Recent Context: {recent_context}
Relevant Past Information: {long_term_context}
User Profile: {memory.user_profile}"""


memory_manager = MemoryManager()


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


def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return "end"
    return "continue"


system_prompt = """You are TARS, an AI assistant with an edgy, sarcastic, geeky sense of humor. 
Use the provided context and memory to maintain consistent, personalized interactions."""


def call_model(state, config):
    messages = state["messages"]
    user_id = config.get("configurable", {}).get("thread_id", "default_user")

    # Get relevant context from memory
    context = memory_manager.get_context(user_id, messages[-1].content)

    # Filter out any existing system messages
    non_system_messages = [
        msg for msg in messages if not isinstance(msg, SystemMessage)
    ]

    # Create a single system message with combined context
    full_messages = [
        SystemMessage(content=f"{system_prompt}\n\nContext: {context}")
    ] + non_system_messages

    model_name = config.get("configurable", {}).get("model_name", "anthropic")
    model = _get_model(model_name)
    response = model.invoke(full_messages)

    # Store the interaction in memory
    memory_manager.add_interaction(
        user_id,
        {
            "role": "assistant",
            "content": response.content,
            "timestamp": datetime.now().isoformat(),
        },
    )

    return {"messages": [response]}


def load_memory(state, config):
    user_id = config.get("configurable", {}).get("thread_id", "default_user")
    context = memory_manager.get_context(user_id, "")
    return {"messages": [SystemMessage(content=context)]}


# Define the function to execute tools
tool_node = ToolNode(tools)
