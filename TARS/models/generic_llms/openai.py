from langchain_openai import ChatOpenAI
from config.config import openai_settings
from dotenv import load_dotenv

load_dotenv()

openai_llm = ChatOpenAI(model=openai_settings.model, temperature=openai_settings.temperature, api_key=openai_settings.api_key)
