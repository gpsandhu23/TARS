from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from graphs.agent import AgentManager
import logging
from langsmith import traceable
from config.config import GitHubOAuthSettings

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
        agent_input = str({'user_name': chat_request.user_name, 'message': chat_request.message})
        agent_response = agent_manager.process_user_task(agent_input, chat_history)
        return {"response": agent_response}
    except Exception as e:
        logging.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/auth/github/callback")
async def github_oauth_callback(request: Request):
    """
    Endpoint to handle the GitHub OAuth callback.
    Args:
        request (Request): The request object containing the callback data.

    Returns:
        dict: A dictionary containing the status of the OAuth process.
    """
    # Extract the code and state from the callback request
    code = request.query_params.get('code')
    state = request.query_params.get('state')

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing 'code' or 'state' in the callback request")

    # Exchange the code for a GitHub access token
    github_oauth_settings = GitHubOAuthSettings()
    access_token = await exchange_code_for_access_token(code, github_oauth_settings.client_id, github_oauth_settings.client_secret)

    if not access_token:
        raise HTTPException(status_code=500, detail="Failed to exchange 'code' for an access token")

    # Validate the access token and retrieve user information
    user_info = await validate_access_token_and_retrieve_user_info(access_token)

    if not user_info:
        raise HTTPException(status_code=500, detail="Failed to validate access token or retrieve user information")

    # Store the access token and user information for future use
    # This is a placeholder for storing the access token and user information
    # Actual implementation will depend on the application's requirements

    return {"status": "success", "user_info": user_info}

async def exchange_code_for_access_token(code: str, client_id: str, client_secret: str) -> str:
    """
    Exchange the GitHub OAuth 'code' for an access token.
    Args:
        code (str): The 'code' received from the GitHub OAuth callback.
        client_id (str): The GitHub OAuth app's client ID.
        client_secret (str): The GitHub OAuth app's client secret.

    Returns:
        str: The access token, or None if the exchange fails.
    """
    # Placeholder for the code exchange process
    # Actual implementation will depend on GitHub's OAuth documentation
    return "access_token_placeholder"

async def validate_access_token_and_retrieve_user_info(access_token: str) -> dict:
    """
    Validate the GitHub access token and retrieve user information.
    Args:
        access_token (str): The GitHub access token.

    Returns:
        dict: A dictionary containing the user's GitHub information, or None if validation fails.
    """
    # Placeholder for the access token validation and user information retrieval
    # Actual implementation will depend on GitHub's API documentation
    return {"user": "placeholder_user"}
