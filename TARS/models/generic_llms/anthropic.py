from config.config import anthropic_settings
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

load_dotenv()

anthropic_llm = ChatAnthropic(model=anthropic_settings.model, temperature=anthropic_settings.temperature, api_key=anthropic_settings.api_key)
