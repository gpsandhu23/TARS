import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

CLIENT_SECRET_FILE = '/Users/gurpartapsandhu/Downloads/client_secret_262946363607-sp223gi0lkj04iah35bh3quopj43qjrv.apps.googleusercontent.com.json'
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
]

creds = None

# Check if the token.json file exists
if os.path.exists('token.json'):
    with open('token.json', 'r') as token:
        creds_json = json.load(token)
        creds = google.oauth2.credentials.Credentials.from_authorized_user_info(creds_json, SCOPES)

# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        creds_to_save = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        json.dump(creds_to_save, token)

service = build('gmail', 'v1', credentials=creds)