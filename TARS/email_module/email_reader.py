from googleapiclient.errors import HttpError

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