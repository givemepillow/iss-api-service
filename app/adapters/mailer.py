from logging import Logger
from typing import Protocol

from app.adapters.gmail import GmailProvider


class MailerProtocol(Protocol):
    def __init__(self): pass

    async def send(self, subject: str, content: str, email: str):
        raise NotImplementedError


class Mailer:
    def __init__(self, logger: Logger, provider: GmailProvider):
        self.logger = logger
        self.logger.info("initialization...")
        self.provider = provider

    async def send(self, subject: str, content: str, email: str):
        return self.provider.send(email, subject, content)
