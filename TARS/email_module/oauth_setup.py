import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from dotenv import load_dotenv, set_key

# Path to the .env file in the parent directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

CLIENT_SECRET_FILE = '/Users/gurpartapsandhu/Downloads/client_secret_262946363607-sp223gi0lkj04iah35bh3quopj43qjrv.apps.googleusercontent.com.json'
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
]

creds = None

# Check for credentials in environment variables
if all(key in os.environ for key in ['TOKEN', 'REFRESH_TOKEN', 'TOKEN_URI', 'CLIENT_ID', 'CLIENT_SECRET']):
    creds_info = {
        'token': os.getenv('TOKEN'),
        'refresh_token': os.getenv('REFRESH_TOKEN'),
        'token_uri': os.getenv('TOKEN_URI'),
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'scopes': SCOPES
    }
    creds = google.oauth2.credentials.Credentials.from_authorized_user_info(creds_info, SCOPES)

# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=0)

    # Update the .env file with the new credentials
    os.environ['TOKEN'] = creds.token
    set_key(dotenv_path, "TOKEN", creds.token)

    if creds.refresh_token:
        os.environ['REFRESH_TOKEN'] = creds.refresh_token
        set_key(dotenv_path, "REFRESH_TOKEN", creds.refresh_token)

    os.environ['TOKEN_URI'] = creds.token_uri
    set_key(dotenv_path, "TOKEN_URI", creds.token_uri)
    os.environ['CLIENT_ID'] = creds.client_id
    set_key(dotenv_path, "CLIENT_ID", creds.client_id)
    os.environ['CLIENT_SECRET'] = creds.client_secret
    set_key(dotenv_path, "CLIENT_SECRET", creds.client_secret)

# Build the service
service = build('gmail', 'v1', credentials=creds)