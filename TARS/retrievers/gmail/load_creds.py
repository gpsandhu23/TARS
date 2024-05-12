import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load environment variables from .env file
load_dotenv()

def authenticate_gmail_api():
    """Authenticate with the Gmail API using credentials from environment variables."""
    # Load credentials from environment variables
    creds_data = {
        'token': os.getenv('TOKEN'),
        'refresh_token': os.getenv('REFRESH_TOKEN'),
        'token_uri': os.getenv('TOKEN_URI'),
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'scopes': os.getenv('SCOPES').split()
    }

    creds = Credentials.from_authorized_user_info(creds_data)
    service = build('gmail', 'v1', credentials=creds)
    return service

def authenticate_calendar_api():
    """Authenticate with the Google Calendar API using credentials from environment variables."""
    creds_data = {
        'token': os.getenv('TOKEN'),
        'refresh_token': os.getenv('REFRESH_TOKEN'),
        'token_uri': os.getenv('TOKEN_URI'),
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'scopes': os.getenv('SCOPES').split()
    }

    creds = Credentials.from_authorized_user_info(creds_data)
    service = build('calendar', 'v3', credentials=creds, cache_discovery=False)
    return service