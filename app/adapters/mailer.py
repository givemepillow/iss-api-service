import asyncio
from asyncio import Task
from random import randint

from app.adapters.gmail import GmailProvider

from asyncio import Protocol


class MailerProtocol(Protocol):
    async def send_code(self, email: str) -> None:
        raise NotImplemented

    def confirm_code(self, email: str, code: str) -> bool:
        raise NotImplemented


class Mailer:  # TODO: DI провайдера почтового (provider)
    def __init__(self):
        self.codes: dict[str, str] = {}
        self.timeouts: dict[str, Task] = {}
        self.gmail = GmailProvider()

    async def send_code(self, email: str):
        self._cancel_timeout(email)
        self._remove_timeout(email)
        self.codes[email] = f"{randint(0, 9999):04d}"
        self.gmail.send(
            email,
            "Код подтверждения.",
            f"{self.codes[email]} — ваш код для авторизации на givemepillow.ru."
        )
        self.timeouts[email] = asyncio.create_task(self.code_timeout(email, delay=30))

    async def code_timeout(self, email, delay):
        print("start sleep")
        await asyncio.sleep(delay=delay)
        print("end sleep")
        self._remove_code(email)
        self._remove_timeout(email)

    def _remove_timeout(self, email):
        if email not in self.timeouts:
            return

        del self.timeouts[email]

    def _cancel_timeout(self, email):
        if email not in self.timeouts:
            return

        self.timeouts[email].cancel()

    def _remove_code(self, email):
        if email not in self.codes:
            return

        del self.codes[email]

    def confirm_code(self, email: str, code: str):
        if code != self.codes.get(email, -1):
            return False

        self._cancel_timeout(email)
        self._remove_timeout(email)
        self._remove_code(email)
        return True
