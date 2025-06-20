from TARS.config.config import anthropic_settings
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
from pydantic import SecretStr

load_dotenv()

anthropic_llm = ChatAnthropic(model_name=anthropic_settings.anthropic_model, temperature=anthropic_settings.anthropic_temperature, api_key=SecretStr(anthropic_settings.anthropic_api_key), timeout=60, stop=None)
