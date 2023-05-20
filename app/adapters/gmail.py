import base64
import os.path
from email.message import EmailMessage
from logging import Logger

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
]


class GmailProvider:  # Нужен DI конфига!
    def __init__(self, logger: Logger):
        self.logger = logger
        self.creds = None
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())

        self.service = build('gmail', 'v1', credentials=self.creds)

    def send(self, to: str, subject: str, content: str):
        message = EmailMessage()
        message.set_content(content)
        message['To'] = to
        message['Subject'] = subject
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}
        try:
            # pylint: disable=E1101
            self.service.users().messages().send(userId="me", body=create_message).execute()
        except HttpError as error:
            self.logger.error(error)
            return False
        return True
