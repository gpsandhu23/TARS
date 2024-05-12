from pydantic_settings import BaseSettings

class SlackSettings(BaseSettings):
    slack_bot_token: str
    slack_signing_secret: str
    slack_app_token: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

slack_settings = SlackSettings()
