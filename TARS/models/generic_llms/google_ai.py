from config.config import google_ai_settings
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

google_llm = ChatGoogleGenerativeAI(model=google_ai_settings.model, temperature=google_ai_settings.temperature, api_key=google_ai_settings.api_key)
