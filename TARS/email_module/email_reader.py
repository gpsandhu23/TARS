from googleapiclient.errors import HttpError
import base64
import email
import datetime

def fetch_unread_emails(service):
    """Fetch all unread emails from the user's inbox.

    Args:
        service: Authorized Gmail API service instance.

    Returns:
        List of unread email messages.
    """
    try:
        # List all unread messages
        response = service.users().messages().list(userId='me', labelIds=['UNREAD']).execute()
        messages = response.get('messages', [])

        all_messages = []
        for msg in messages:
            # Fetch the full message details for each unread message
            msg_detail = service.users().messages().get(userId='me', id=msg['id']).execute()
            all_messages.append(msg_detail)

        return all_messages

    except HttpError as error:
        print(f'An error occurred: {error}')
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
