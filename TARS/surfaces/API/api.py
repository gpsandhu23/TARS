from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from graphs.agent import process_user_task
import logging
from langsmith import traceable

# Setup logging
logging.basicConfig(level=logging.INFO)


app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    user_name: str = "Unknown User"

@app.post("/chat")
@traceable(name="Chat API")
async def chat_endpoint(chat_request: ChatRequest) -> dict:
    """
    Endpoint to process chat messages using an agent.
    Args:
    chat_request (ChatRequest): The chat request containing the message and user name.

    Returns:
    dict: A dictionary containing the agent's response.
    """
    try:
        chat_history = []  # Simulate chat history as an empty list for simplicity
        agent_input = {'user_name': chat_request.user_name, 'message': chat_request.message}
        agent_response = process_user_task(str(agent_input), chat_history)
        return {"response": agent_response}
    except Exception as e:
        logging.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
