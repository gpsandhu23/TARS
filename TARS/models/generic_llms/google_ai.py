from TARS.config.config import google_ai_settings
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from pydantic import SecretStr

load_dotenv()

google_ai_llm = ChatGoogleGenerativeAI(model=google_ai_settings.google_ai_model, temperature=google_ai_settings.google_ai_temperature, google_api_key=SecretStr(google_ai_settings.google_ai_api_key))
