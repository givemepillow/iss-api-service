from __future__ import annotations

from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import Config
from app.adapters import repository

config = Config()

ASYNC_ENGINE = create_async_engine(
    config.postgres.dsn,
    echo=True
)
DEFAULT_SESSION_FACTORY = async_sessionmaker(
    ASYNC_ENGINE,
    expire_on_commit=False,
    class_=AsyncSession,
)


class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker = DEFAULT_SESSION_FACTORY):
        self.session: AsyncSession = session_factory()
        self.users = repository.UserRepository(self.session)
        self.posts = repository.PostRepository(self.session)
        self.verify_codes = repository.VerifyCodesRepository(self.session)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args):
        await self.rollback()
        await self.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()

    async def close(self):
        await self.session.close()
