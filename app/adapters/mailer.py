from logging import Logger

from app.adapters.gmail import GmailProvider
from app.utils.interface import Interface


class Mailer:
    def __init__(self, logger: Logger, provider: GmailProvider):
        self.logger = logger
        self.logger.info("initialization...")
        self.provider = provider

    async def send(self, subject: str, content: str, email: str):
        return self.provider.send(email, subject, content)


class IMailer(Interface, Mailer):
    pass
