from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Load secrets from .env
load_dotenv()


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file_encoding="utf-8", extra="ignore")


class SlackSettings(BaseConfig):
    slack_bot_token: Optional[str] = None
    slack_signing_secret: Optional[str] = None
    slack_app_token: Optional[str] = None


class OpenAISettings(BaseConfig):
    openai_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_temperature: float = 0.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class AnthropicSettings(BaseConfig):
    anthropic_model: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    anthropic_temperature: float = 0.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class GoogleAISettings(BaseConfig):
    google_ai_model: Optional[str] = None
    google_ai_api_key: Optional[str] = None
    google_ai_temperature: float = 0.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class GraphConfig(BaseConfig):
    agent_model_name: Optional[str] = "anthropic"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class GitHubOAuthSettings(BaseConfig):
    client_id: Optional[str] = None
    client_secret: Optional[str] = None

    model_config = SettingsConfigDict(env_prefix="GITHUB_", env_file=".env", env_file_encoding="utf-8", extra="ignore")


# Initialize the chat models based on settings
openai_settings = OpenAISettings()
anthropic_settings = AnthropicSettings()
google_ai_settings = GoogleAISettings()
graph_config = GraphConfig()

# Initialize Slack settings
slack_settings = SlackSettings()

# Initialize GitHub OAuth settings
github_oauth_settings = GitHubOAuthSettings()
