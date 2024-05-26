from googleapiclient.errors import HttpError
import base64
import email
import datetime

def fetch_unread_emails(service):
    """Fetch all unread emails from the user's inbox with their ID and received date.

    Args:
        service: Authorized Gmail API service instance.

    Returns:
        List of dictionaries containing the email ID, and received date of unread email messages.
    """
    try:
        # List all unread messages
        response = service.users().messages().list(userId='me', labelIds=['UNREAD']).execute()

        # Debugging: Check the type of response and print it
        print(f"Response type: {type(response)}")
        print(f"Response content: {response}")

        # Ensure response is a dictionary before calling get
        if not isinstance(response, dict):
            print("Response is not a dictionary.")
            return []

        messages = response.get('messages', [])
        all_messages = []
        for msg in messages:
            # Fetch only the headers of the message
            msg_detail = service.users().messages().get(userId='me', id=msg['id'], format='metadata', 
                                                        metadataHeaders=['Date']).execute()
            
            # Extract the headers
            headers = msg_detail.get('payload', {}).get('headers', [])
            date_header = next((header['value'] for header in headers if header['name'] == 'Date'), None)
            
            # Append a dictionary with the email ID and received date to the list
            all_messages.append({
                'id': msg['id'],
                'received_date': date_header
            })

        return all_messages

    except Exception as e:
        print(f'An error occurred: {e}')
        return []
    
def mark_email_as_read(service, user_id, msg_id):
    """Marks an email as read by removing the 'UNREAD' label."""
    try:
        service.users().messages().modify(userId=user_id, id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()
    except HttpError as error:
        print(f'An error occurred: {error}')

def get_mime_message(service, user_id, msg_id):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()
        msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
        mime_msg = email.message_from_bytes(msg_str)
        return mime_msg
    except HttpError as error:
        print(f'An error occurred: {error}')

def get_email_content(mime_msg):
    content = ""
    if mime_msg.is_multipart():
        for part in mime_msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if "attachment" not in content_disposition and content_type == "text/plain":
                byte_content = part.get_payload(decode=True)
                try:
                    # Try decoding with utf-8
                    content = byte_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        # If utf-8 fails, try decoding with ISO-8859-1
                        content = byte_content.decode('iso-8859-1')
                    except UnicodeDecodeError:
                        # If both fail, decode with utf-8 and replace errors
                        content = byte_content.decode('utf-8', errors='replace')
                break
    else:
        content_type = mime_msg.get_content_type()
        if content_type == "text/plain":
            byte_content = mime_msg.get_payload(decode=True)
            try:
                content = byte_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content = byte_content.decode('iso-8859-1')
                except UnicodeDecodeError:
                    content = byte_content.decode('utf-8', errors='replace')
    return content

def get_upcoming_events(service, days=7):
    """
    Fetch the upcoming events from the primary Google Calendar for the next 'x' number of days.

    Args:
        service: Authorized Google Calendar API service instance.
        days (int): The number of days from today for which to retrieve events.

    Returns:
        List of upcoming calendar events within the specified number of days.
    """
    now = datetime.datetime.utcnow()
    time_min = now.isoformat() + 'Z'  # 'Z' indicates UTC time
    time_max = (now + datetime.timedelta(days=days)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary', 
        timeMin=time_min, 
        timeMax=time_max, 
        singleEvents=True, 
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    return events