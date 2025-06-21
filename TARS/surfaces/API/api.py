import logging
from datetime import datetime, timezone
import uuid

import aiohttp
import requests
from TARS.config.config import github_oauth_settings
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from TARS.graphs.core_agent import run_core_agent
from langsmith import traceable, Client
from langsmith.run_helpers import get_current_run_tree
from TARS.metrics.event_instrumentation import IncomingUserEvent
from pydantic import BaseModel
from starlette.responses import Response

# Load environment variables from .env file
load_dotenv()

# Setup logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Global storage for user run IDs (in production, use a proper database)
user_run_ids = {}
langsmith_client = Client()

def setup_routes():
    """Setup all API routes and their handlers."""
    app.post("/chat")(handle_chat_request)
    app.post("/chat_github")(handle_github_chat_request)
    app.post("/feedback")(handle_feedback_request)
    app.get("/test")(handle_test_request)
    app.get("/auth/github/callback")(handle_github_oauth_callback)


class ChatRequest(BaseModel):
    """
    Pydantic model for chat requests.
    """

    message: str
    user_name: str = "Unknown User"


class FeedbackRequest(BaseModel):
    """
    Pydantic model for feedback requests.
    """
    user_name: str
    satisfaction_score: float  # Score between 0.0 and 1.0
    comment: str = ""


def log_user_event(event: IncomingUserEvent):
    """
    Log the user event for metrics and analysis.

    Args:
        event: The IncomingUserEvent to be logged.
    """
    # Here you would implement the actual logging logic
    # This could involve sending the event to a database, logging service, etc.
    logger.info(f"User Event Logged: {event.model_dump()}")


@traceable(name="API Chat Endpoint")
async def handle_chat_request(request: ChatRequest):
    """
    Handle chat requests and forward them to the core agent.

    Args:
        request (ChatRequest): The validated chat request object.

    Returns:
        Response: The response from the core agent.
    """
    logger.info("=== API CHAT ENDPOINT START ===")
    
    try:
        logger.info(f"Received request: {request}")

        # Capture run ID for feedback tracking
        run_tree = get_current_run_tree()
        run_id = run_tree.id if run_tree else str(uuid.uuid4())
        user_run_ids[request.user_name] = run_id
        logger.info(f"Captured Run ID: {run_id} for user {request.user_name}")

        # Create and log the IncomingUserEvent
        user_event = IncomingUserEvent(
            user_id=request.user_name,  # Using user_name as user_id
            user_name=request.user_name,
            event_time=datetime.now(timezone.utc),
            capability_invoked="TARS",
            user_agent="API",
            response_satisfaction="none",
        )
        logger.info(f"Created user event: {user_event}")
        log_user_event(user_event)

        # Prepare input for run_core_agent
        user_input = {
            "user_name": user_event.user_name,
            "message": request.message,
        }
        
        logger.info(f"Prepared user input for core agent: {user_input}")

        # Get the generator from run_core_agent
        agent_response_generator = run_core_agent(
            user_name=user_input["user_name"],
            message=user_input["message"]
        )
        logger.info("Successfully got response generator from run_core_agent")

        # Collect all responses from the generator
        agent_response_text = ""
        response_count = 0
        logger.info("Starting to iterate through response generator...")
        
        for response_part in agent_response_generator:
            response_count += 1
            logger.info(f"Received response part #{response_count}: '{response_part}'")
            agent_response_text += response_part

        logger.info(f"Completed response collection. Total parts: {response_count}, Final response: '{agent_response_text}'")
        
        if not agent_response_text.strip():
            logger.warning("Empty response received from core agent!")
            return {"response": "I apologize, but I didn't receive a proper response. Please try again."}
        
        logger.info("=== API CHAT ENDPOINT SUCCESS ===")
        return {"response": agent_response_text, "run_id": run_id}
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        logger.info("=== API CHAT ENDPOINT ERROR ===")
        return {"response": f"An error occurred: {str(e)}"}


async def verify_github_token(request: Request, x_github_token: str = Header(None)):
    """
    Verify the GitHub token provided in the request header.

    Args:
        request (Request): The incoming request object.
        x_github_token (str, optional): The GitHub token from the request header.

    Returns:
        str: The verified GitHub token.

    Raises:
        HTTPException: If the token is missing or invalid.
    """
    headers = dict(request.headers)
    logging.info(f"Received API request to chat headers: {headers}")
    body = await request.json()
    logging.info(f"Received API request to chat: {body}")
    if x_github_token is None:
        raise HTTPException(status_code=400, detail="X-GitHub-Token header is missing")

    # Validate that the token belongs to a particular username
    response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"token {x_github_token}"},
    )
    response.raise_for_status()  # Raise exception if the request failed
    user_data = response.json()
    logging.info(f"GitHub user data: {user_data}")
    if user_data["login"] not in [
        "gpsandhu23",
        "gsandhu_adobe",
    ]:  # only limit this for my user for now
        raise HTTPException(
            status_code=403, detail="Token does not belong to the expected user"
        )

    return x_github_token


@traceable(name="API GitHub Chat Endpoint")
async def handle_github_chat_request(
    request: Request, github_token: str = Depends(verify_github_token)
):
    """
    Handle chat requests and forward them to GitHub Copilot.

    Args:
        request (Request): The incoming request object.
        github_token (str): The verified GitHub token.

    Returns:
        Response: The response from GitHub Copilot.
    """
    async with aiohttp.ClientSession() as session:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {github_token}",
        }
        logging.info(f"Request headers: {headers}")
        body = await request.json()
        logging.info(f"Received API request to chat: {body}")

        # Extract messages from the body
        messages = body.get("messages", [])
        if messages:
            # Get the most recent message (the last one in the list)
            recent_message = messages[-1]
            message_content = recent_message.get("content", "")
            logging.info(f"Most recent message: {message_content}")
        else:
            message_content = ""
            logging.info("No messages found")

        # Prepare the body for the API call to GitHub Copilot
        request_body = {
            "stream": True,
            "messages": [{"role": "user", "content": message_content}],
            "max_tokens": 5000,
            "temperature": 0.5,
        }

        # Post the chat request to GitHub Copilot and log the response
        async with session.post(
            "https://api.githubcopilot.com/chat/completions",
            headers=headers,
            json=request_body,
        ) as capi_response:
            response_body = await capi_response.read()
            logging.info(f"Received API response status: {capi_response.status}")
            logging.info(f"Received API response headers: {capi_response.headers}")
            logging.info(f"Received API response body: {response_body}")

            # Return the response from GitHub Copilot directly to the client
            return Response(
                content=response_body,
                media_type="application/json",
                status_code=capi_response.status,
            )


@traceable(name="API Test Endpoint")
async def handle_test_request():
    """
    A simple test endpoint to check if the API is working.

    Returns:
        dict: A dictionary containing a welcome message.
    """
    return {"message": "Hola! Welcome to our API!"}


@traceable(name="API GitHub OAuth Callback")
async def handle_github_oauth_callback(request: Request):
    """
    Handle the GitHub OAuth callback.

    Args:
        request (Request): The request object containing the callback data.

    Returns:
        dict: A dictionary containing the status of the OAuth process and user information.

    Raises:
        HTTPException: If there's an error during the OAuth process.
    """
    headers = dict(request.headers)
    logging.info(f"Received API request to auth/github/callback headers: {headers}")
    # Extract the code and state from the callback request
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code:
        raise HTTPException(
            status_code=400, detail="Missing 'code' in the callback request"
        )

    # Exchange the code for a GitHub access token
    access_token = await exchange_code_for_access_token(
        code, github_oauth_settings.client_id, github_oauth_settings.client_secret
    )

    if not access_token:
        raise HTTPException(
            status_code=500, detail="Failed to exchange 'code' for an access token"
        )

    # Validate the access token and retrieve user information
    user_info = await validate_access_token_and_retrieve_user_info(access_token)

    if not user_info:
        raise HTTPException(
            status_code=500,
            detail="Failed to validate access token or retrieve user information",
        )

    # Store the access token and user information for future use
    # This is a placeholder for storing the access token and user information
    # Actual implementation will depend on the application's requirements

    return {"status": "success", "user_info": user_info, "user_token": access_token}


@traceable(name="API Exchange Code for Access Token")
async def exchange_code_for_access_token(
    code: str, client_id: str, client_secret: str
) -> str:
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
    payload = {"client_id": client_id, "client_secret": client_secret, "code": code}

    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, data=payload)
        logging.info(f"GitHub OAuth response status: {response.status_code}")
        logging.info(f"GitHub OAuth response body: {response.text}")
        response_data = response.json()
        if "access_token" in response_data:
            return response_data["access_token"]
        else:
            return None


@traceable(name="API Validate Access Token and Retrieve User Info")
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
    headers = {"Authorization": f"token {access_token}", "Accept": "application/json"}

    async with AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None


@traceable(name="API Feedback Endpoint")
async def handle_feedback_request(request: FeedbackRequest):
    """
    Handle feedback requests and log them to LangSmith.

    Args:
        request (FeedbackRequest): The validated feedback request object.

    Returns:
        dict: Confirmation of feedback submission.
    """
    logger.info("=== API FEEDBACK ENDPOINT START ===")
    
    try:
        logger.info(f"Received feedback request: {request}")
        
        # Validate satisfaction score
        if not 0.0 <= request.satisfaction_score <= 1.0:
            raise HTTPException(
                status_code=400, 
                detail="Satisfaction score must be between 0.0 and 1.0"
            )
        
        # Get the run_id for this user
        run_id = user_run_ids.get(request.user_name)
        logger.info(f"Looking up run_id for user {request.user_name}: {run_id}")
        
        if not run_id:
            logger.warning(f"No run_id found for user {request.user_name}")
            logger.info(f"Available user_run_ids: {list(user_run_ids.keys())}")
            raise HTTPException(
                status_code=404,
                detail="No recent conversation found for this user. Please send a message first."
            )
        
        feedback_key = "user_satisfaction"
        
        logger.info(f"Creating feedback - key: {feedback_key}, score: {request.satisfaction_score}, run_id: {run_id}")
        
        try:
            # Create feedback in LangSmith
            logger.info(f"Calling langsmith_client.create_feedback with:")
            logger.info(f"  - key: {feedback_key}")
            logger.info(f"  - score: {request.satisfaction_score}")
            logger.info(f"  - run_id: {run_id}")
            logger.info(f"  - comment: {request.comment}")
            
            feedback_result = langsmith_client.create_feedback(
                key=feedback_key,
                score=request.satisfaction_score,
                run_id=run_id,
                comment=request.comment
            )
            
            logger.info(f"LangSmith create_feedback returned: {feedback_result}")
            logger.info(f"Feedback logged successfully for user {request.user_name}: {feedback_key}={request.satisfaction_score}")
            
            logger.info("=== API FEEDBACK ENDPOINT SUCCESS ===")
            return {
                "status": "success",
                "message": "Feedback submitted successfully",
                "feedback_id": str(feedback_result.id) if hasattr(feedback_result, 'id') else None
            }
            
        except Exception as e:
            logger.error(f"Failed to create feedback: {e}", exc_info=True)
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception args: {e.args}")
            raise HTTPException(
                status_code=500,
                detail="Failed to submit feedback to LangSmith"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in feedback endpoint: {str(e)}", exc_info=True)
        logger.info("=== API FEEDBACK ENDPOINT ERROR ===")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing feedback: {str(e)}"
        )


# Setup all routes
setup_routes()
