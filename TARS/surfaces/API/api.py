from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from graphs.agent import AgentManager
import logging
from langsmith import traceable

# Setup logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    user_name: str = "Unknown User"

def get_agent_manager():
    return AgentManager()

@app.post("/chat")
@traceable(name="Chat API")
async def chat_endpoint(chat_request: ChatRequest, agent_manager: AgentManager = Depends(get_agent_manager)) -> dict:
    """
    Endpoint to process chat messages using an agent.
    Args:
        chat_request (ChatRequest): The chat request containing the message and user name.

    Returns:
        dict: A dictionary containing the agent's response.
    """
    logging.info(f"Received chat request from {chat_request.user_name}")
    try:
        chat_history = []  # Eventually, fetch this from a persistent storage
        agent_input = {'user_name': chat_request.user_name, 'message': chat_request.message}
        agent_response = agent_manager.process_user_task(agent_input, chat_history)
        return {"response": agent_response}
    except Exception as e:
        logging.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
