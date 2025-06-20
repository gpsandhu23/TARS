from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List
import logging

from TARS.config.config import (
    anthropic_settings,
    google_ai_settings,
    graph_config,
    openai_settings,
)
from TARS.graphs.utils.tools import tools
from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores import Chroma
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

# Setup logging
logger = logging.getLogger(__name__)


class Memory(BaseModel):
    short_term: List[Dict[str, Any]]
    summary: str = ""
    last_summarized: datetime = None
    user_profile: Dict[str, Any] = {}


class MemoryManager:
    def __init__(self):
        logger.info("Initializing MemoryManager")
        self.memory_store = {}
        self.vectorstore = Chroma(
            collection_name="long_term_memory", embedding_function=OpenAIEmbeddings()
        )
        self.summary_threshold = 10  # Messages before summarizing
        logger.info("MemoryManager initialized successfully")

    def get_or_create_memory(self, user_id: str) -> Memory:
        logger.info(f"Getting or creating memory for user_id: {user_id}")
        if user_id not in self.memory_store:
            logger.info(f"Creating new memory for user_id: {user_id}")
            self.memory_store[user_id] = Memory(short_term=[])
        else:
            logger.info(f"Found existing memory for user_id: {user_id}")
        return self.memory_store[user_id]

    def add_interaction(self, user_id: str, message: Dict[str, Any]):
        logger.info(f"Adding interaction for user_id: {user_id}, message: {message}")
        memory = self.get_or_create_memory(user_id)
        memory.short_term.append(message)
        logger.info(f"Added message to short-term memory. Total messages: {len(memory.short_term)}")

        if len(memory.short_term) >= self.summary_threshold:
            logger.info("Reached summary threshold, summarizing...")
            self._summarize_and_store(user_id)

    def get_context(self, user_id: str, query: str) -> str:
        logger.info(f"Getting context for user_id: {user_id}, query: {query}")
        memory = self.get_or_create_memory(user_id)
        recent_context = memory.short_term[-5:] if memory.short_term else []
        logger.info(f"Recent context: {recent_context}")

        # Get relevant long-term memories
        logger.info("Getting relevant long-term memories...")
        relevant_docs = self.vectorstore.similarity_search(query, k=2)
        long_term_context = "\n".join(doc.page_content for doc in relevant_docs)
        logger.info(f"Long-term context: {long_term_context}")

        context = f"""Summary: {memory.summary}
Recent Context: {recent_context}
Relevant Past Information: {long_term_context}
User Profile: {memory.user_profile}"""
        
        logger.info(f"Final context: {context}")
        return context

    def _summarize_and_store(self, user_id: str):
        logger.info(f"Summarizing and storing memory for user_id: {user_id}")
        # Implementation would go here
        logger.info("Memory summarization completed")


memory_manager = MemoryManager()


@lru_cache(maxsize=4)
def _get_model(model_name: str):
    logger.info(f"Getting model for model_name: {model_name}")
    logger.info(f"Graph config agent_model_name: {graph_config.agent_model_name}")
    
    if graph_config.agent_model_name == "openai":
        logger.info("Initializing OpenAI model")
        model = ChatOpenAI(temperature=0, model_name=openai_settings.openai_model)
    elif graph_config.agent_model_name == "anthropic":
        logger.info("Initializing Anthropic model")
        model = ChatAnthropic(
            temperature=0, model_name=anthropic_settings.anthropic_model
        )
    elif graph_config.agent_model_name == "google":
        logger.info("Initializing Google AI model")
        model = ChatGoogleGenerativeAI(
            temperature=0, model_name=google_ai_settings.google_ai_model
        )
    else:
        logger.error(f"Unsupported model type: {graph_config.agent_model_name}")
        raise ValueError(f"Unsupported model type: {graph_config.agent_model_name}")

    logger.info("Binding tools to model")
    model = model.bind_tools(tools)
    logger.info("Model initialization complete")
    return model


def should_continue(state):
    logger.info(f"should_continue called with state: {state}")
    messages = state["messages"]
    last_message = messages[-1]
    logger.info(f"Last message: {last_message}")
    logger.info(f"Last message tool_calls: {last_message.tool_calls}")
    
    if not last_message.tool_calls:
        logger.info("No tool calls, returning 'end'")
        return "end"
    logger.info("Has tool calls, returning 'continue'")
    return "continue"


system_prompt = """You are TARS, an AI assistant with an edgy, sarcastic, geeky sense of humor. 
Use the provided context and memory to maintain consistent, personalized interactions."""


def call_model(state, config):
    logger.info("=== CALL MODEL START ===")
    logger.info(f"Input state: {state}")
    logger.info(f"Input config: {config}")
    
    try:
        messages = state["messages"]
        user_id = config.get("configurable", {}).get("thread_id", "default_user")
        logger.info(f"Processing for user_id: {user_id}")
        logger.info(f"Number of messages: {len(messages)}")

        # Get relevant context from memory
        logger.info("Getting context from memory...")
        context = memory_manager.get_context(user_id, messages[-1].content)
        logger.info(f"Retrieved context: {context}")

        # Filter out any existing system messages
        non_system_messages = [
            msg for msg in messages if not isinstance(msg, SystemMessage)
        ]
        logger.info(f"Non-system messages count: {len(non_system_messages)}")

        # Create a single system message with combined context
        full_messages = [
            SystemMessage(content=f"{system_prompt}\n\nContext: {context}")
        ] + non_system_messages
        logger.info(f"Created {len(full_messages)} full messages")

        model_name = config.get("configurable", {}).get("model_name", "anthropic")
        logger.info(f"Using model_name: {model_name}")
        
        logger.info("Getting model...")
        model = _get_model(model_name)
        logger.info("Model retrieved successfully")
        
        logger.info("Invoking model...")
        response = model.invoke(full_messages)
        logger.info(f"Model response: {response}")
        logger.info(f"Model response content: {response.content}")

        # Store the interaction in memory
        logger.info("Storing assistant response in memory...")
        memory_manager.add_interaction(
            user_id,
            {
                "role": "assistant",
                "content": response.content,
                "timestamp": datetime.now().isoformat(),
            },
        )
        logger.info("Successfully stored assistant response in memory")

        result = {"messages": [response]}
        logger.info(f"Returning result: {result}")
        logger.info("=== CALL MODEL SUCCESS ===")
        return result
        
    except Exception as e:
        logger.error(f"Error in call_model: {str(e)}", exc_info=True)
        logger.info("=== CALL MODEL ERROR ===")
        raise


def load_memory(state, config):
    user_id = config.get("configurable", {}).get("thread_id", "default_user")
    context = memory_manager.get_context(user_id, "")
    return {"messages": [SystemMessage(content=context)]}


# Define the function to execute tools
tool_node = ToolNode(tools)
