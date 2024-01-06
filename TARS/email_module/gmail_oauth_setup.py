import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from dotenv import load_dotenv, set_key
import google.oauth2.credentials

# Construct the path to the .env file (two levels up)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')

# Check if the .env file exists
if not os.path.exists(dotenv_path):
    print(f"Error: .env file not found at {dotenv_path}")
else:
    load_dotenv(dotenv_path)
    print(f".env file loaded from {dotenv_path}")
    
load_dotenv(dotenv_path)

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
]

creds = None

print("Environment Variables Loaded:", os.getenv('CLIENT_ID'), os.getenv('CLIENT_SECRET'))

# Check for credentials in environment variables
if 'CLIENT_ID' in os.environ and 'CLIENT_SECRET' in os.environ:
    client_config = {
        "installed": {
            "client_id": os.getenv("CLIENT_ID"),
            "project_id": "",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": os.getenv("CLIENT_SECRET"),
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
        }
    }

    if 'TOKEN' in os.environ and 'REFRESH_TOKEN' in os.environ:
        creds_info = {
            'token': os.getenv('TOKEN'),
            'refresh_token': os.getenv('REFRESH_TOKEN'),
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': os.getenv('CLIENT_ID'),
            'client_secret': os.getenv('CLIENT_SECRET'),
            'scopes': SCOPES
        }
        creds = google.oauth2.credentials.Credentials.from_authorized_user_info(creds_info, SCOPES)

        print("Credentials Loaded from Environment Variables.")

    # Refresh the token if it's expired
    if creds and creds.expired and creds.refresh_token:
        print("Refreshing Expired Token.")
        creds.refresh(Request())

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        print("Initiating OAuth Flow.")
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        creds = flow.run_local_server(port=0)

        # Save the new credentials to the .env file
        set_key(dotenv_path, "TOKEN", creds.token)
        set_key(dotenv_path, "REFRESH_TOKEN", creds.refresh_token)

# Build the Gmail service
try:
    service = build('gmail', 'v1', credentials=creds)
    print("Gmail service built successfully.")
except Exception as e:
    print(f"An error occurred: {e}")