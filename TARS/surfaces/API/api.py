from fastapi import FastAPI, HTTPException, Depends, Request, Header
from pydantic import BaseModel
from graphs.agent import AgentManager
import requests
import logging
from langsmith import traceable
from config.config import github_oauth_settings
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    user_name: str = "Unknown User"

def get_agent_manager():
    return AgentManager()

async def verify_github_token(request:Request, x_github_token: str = Header(None)):
    headers = dict(request.headers)
    logging.info(f"Received API request to chat headers: {headers}")
    body = await request.json()
    logging.info(f"Received API request to chat: {body}")
    if x_github_token is None:
        raise HTTPException(status_code=400, detail="X-GitHub-Token header is missing")

    # Validate that the token belongs to a particular username
    response = requests.get('https://api.github.com/user', headers={'Authorization': f'token {x_github_token}'})
    response.raise_for_status()  # Raise exception if the request failed
    user_data = response.json()
    logging.info(f"GitHub user data: {user_data}")
    if user_data['login'] != 'gpsandhu23':  # only limit this for my user for now
        raise HTTPException(status_code=403, detail="Token does not belong to the expected user")

    return x_github_token, user_data['login']

@app.post("/chat")
@traceable(name="Chat API")
async def chat_endpoint(request: Request, x_github_token: str = Depends(verify_github_token), agent_manager: AgentManager = Depends(get_agent_manager)) -> dict:
    """
    Endpoint to process chat messages using an agent.
    Args:
        request (Request): The request object containing the chat data.
        x_github_token (str): The GitHub access token.
        agent_manager (AgentManager): The agent manager instance.

    Returns:
        dict: A dictionary containing the agent's response.
    """
    headers = dict(request.headers)
    logging.info(f"Received API request to chat headers: {headers}")
    body = await request.json()
    logging.info(f"Received API request to chat body: {body}")
    messages = body.get('messages', [])
    if messages:
        message = messages[0].get('content', '')
    else:
        message = ''
    token, user_name = x_github_token
    logging.info(f"User name: {user_name}")
    logging.info(f"User message: {message}")
    try:
        chat_history = []  # Eventually, fetch this from a persistent storage
        agent_input = str({'user_name': user_name, 'message': message})
        logging.info(f"Processing chat request: {agent_input}")
        agent_response = agent_manager.process_user_task(agent_input, chat_history)
        logging.info(f"Agent response: {agent_response}")

        # Format the response for GHCP
        response = {
            "data": {
                "id": "chatcmpl-123",
                "object": "chat.completion.chunk",
                "created": 1694268190,  # Placeholder
                "model": "gpt-3.5-turbo-0125",  # Placeholder
                "system_fingerprint": "fp_44709d6fcb",  # Placeholder
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "role": "assistant",
                            "content": agent_response
                        },
                        "logprobs": None,
                        "finish_reason": None  # Placeholder
                    }
                ]
            }
        }
        logging.info(f"Returning response: {response}")

        return response

    except Exception as e:
        logging.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# add a new endpoint to test the API
@app.get("/test")
async def test_endpoint():
    return {"message": "Hola! Welcome to our API!"}

@app.get("/auth/github/callback")
async def github_oauth_callback(request: Request):
    """
    Endpoint to handle the GitHub OAuth callback.
    Args:
        request (Request): The request object containing the callback data.

    Returns:
        dict: A dictionary containing the status of the OAuth process.
    """
    headers = dict(request.headers)
    logging.info(f"Received API request to auth/github/callback headers: {headers}")
    # Extract the code and state from the callback request
    code = request.query_params.get('code')
    state = request.query_params.get('state')

    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' in the callback request")

    # Exchange the code for a GitHub access token
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
    from httpx import AsyncClient
    url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code
    }

    
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, data=payload)
        logging.info(f"GitHub OAuth response status: {response.status_code}")
        logging.info(f"GitHub OAuth response body: {response.text}")
        response_data = response.json()
        if 'access_token' in response_data:
            return response_data['access_token']
        else:
            return None

async def validate_access_token_and_retrieve_user_info(access_token: str) -> dict:
    """
    Validate the GitHub access token and retrieve user information.
    Args:
        access_token (str): The GitHub access token.

    Returns:
        dict: A dictionary containing the user's GitHub information, or None if validation fails.
    """
    from httpx import AsyncClient
    url = "https://api.github.com/user"
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/json"
    }
    
    async with AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None
