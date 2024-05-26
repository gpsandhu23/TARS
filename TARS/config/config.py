from pydantic_settings import BaseSettings
from typing import ClassVar
import os
from dotenv import load_dotenv

# Load secrets from .env
load_dotenv()

# Determine the environment and load the appropriate config file
environment = os.getenv('ENVIRONMENT', 'local')  # Default to 'local' if not set
config_file = f"config.{environment}"
load_dotenv(config_file)

class BaseConfig(BaseSettings):
    class Config:
        env_file = config_file
        env_file_encoding = 'utf-8'


class SlackSettings(BaseConfig):
    slack_bot_token: str
    slack_signing_secret: str
    slack_app_token: str


class OpenAISettings(BaseConfig):
    env_prefix: ClassVar[str] = "OPENAI_"
    model: str = "gpt-4o"
    api_key: str
    temperature: float = 0.0

    class Config:
        env_prefix = "OPENAI_"
        env_file = ".env"
        env_file_encoding = 'utf-8'


class AnthropicSettings(BaseConfig):
    env_prefix: ClassVar[str] = "ANTHROPIC_"
    model: str = "claude-3-opus-20240229"
    api_key: str
    temperature: float = 0.0

    class Config:
        env_prefix = "ANTHROPIC_"
        env_file = ".env"
        env_file_encoding = 'utf-8'


class GoogleAISettings(BaseConfig):
    model: str = "gemini-pro"
    api_key: str
    temperature: float = 0.0

    class Config:
        env_prefix = "GOOGLE_"
        env_file = ".env"
        env_file_encoding = 'utf-8'


class LLMSettings(BaseConfig):
    llm_type: str = "openai"  # 'openai', 'google', or 'anthropic'


class GitHubOAuthSettings(BaseConfig):
    client_id: str
    client_secret: str

    class Config:
        env_prefix = "GITHUB_"
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Initialize the chat models based on settings
openai_settings = OpenAISettings()
anthropic_settings = AnthropicSettings()
google_ai_settings = GoogleAISettings()
llm_settings = LLMSettings()

# Initialize Slack settings
slack_settings = SlackSettings()

# Initialize GitHub OAuth settings
github_oauth_settings = GitHubOAuthSettings()
