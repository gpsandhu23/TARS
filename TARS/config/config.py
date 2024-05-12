from pydantic_settings import BaseSettings
from langchain.chat_models import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import os
from dotenv import load_dotenv

load_dotenv()

class SlackSettings(BaseSettings):
    slack_bot_token: str
    slack_signing_secret: str
    slack_app_token: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

class OpenAISettings(BaseSettings):
    model: str = "gpt-4-turbo"
    api_key: str
    temperature: float = 0.0

    class Config:
        env_prefix = "OPENAI_"
        env_file = ".env"
        env_file_encoding = 'utf-8'

class AnthropicSettings(BaseSettings):
    model: str = "claude-3-opus-20240229"
    api_key: str
    temperature: float = 0.0

    class Config:
        env_prefix = "ANTHROPIC_"
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Initialize the chat models based on settings
openai_settings = OpenAISettings()
anthropic_settings = AnthropicSettings()

# Initialize Slack settings
slack_settings = SlackSettings()
