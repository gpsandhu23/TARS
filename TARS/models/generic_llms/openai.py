from langchain_openai import ChatOpenAI
from TARS.config.config import openai_settings
from dotenv import load_dotenv
from pydantic import SecretStr

load_dotenv()

openai_llm = ChatOpenAI(model=openai_settings.openai_model, temperature=openai_settings.openai_temperature, api_key=SecretStr(openai_settings.openai_api_key))
