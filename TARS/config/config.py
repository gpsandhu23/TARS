from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load secrets from .env
load_dotenv()


class BaseConfig(BaseSettings):
    class Config:
        env_file_encoding = "utf-8"


class SlackSettings(BaseConfig):
    slack_bot_token: str
    slack_signing_secret: str
    slack_app_token: str


class OpenAISettings(BaseConfig):
    openai_model: str
    openai_api_key: str
    openai_temperature: float = 0.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class AnthropicSettings(BaseConfig):
    anthropic_model: str
    anthropic_api_key: str
    anthropic_temperature: float = 0.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class GoogleAISettings(BaseConfig):
    google_ai_model: str
    google_ai_api_key: str
    google_ai_temperature: float = 0.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class GraphConfig(BaseConfig):
    agent_model_name: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class GitHubOAuthSettings(BaseConfig):
    client_id: str
    client_secret: str

    class Config:
        env_prefix = "GITHUB_"
        env_file = ".env"
        env_file_encoding = "utf-8"


# Initialize the chat models based on settings
openai_settings = OpenAISettings()
anthropic_settings = AnthropicSettings()
google_ai_settings = GoogleAISettings()
graph_config = GraphConfig()

# Initialize Slack settings
slack_settings = SlackSettings()

# Initialize GitHub OAuth settings
github_oauth_settings = GitHubOAuthSettings()
