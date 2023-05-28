from sqlalchemy import select, delete, and_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload

from app.domain import models


class UserRepository:
    def __init__(self, session):
        self.session = session

    def add(self, user):
        self.session.add(user)

    async def get(self, user_id: int) -> models.User | None:
        return (await self.session.execute(
            select(models.User).where(models.User.id == user_id)
        )).scalar()

    async def get_bookmarks_by_username(self, username: str) -> models.User | None:
        return (await self.session.execute(
            select(models.Post)
            .join_from(models.User, models.User.bookmarks)
            .where(models.User.username == username)
        )).unique().scalars()

    async def get_by_telegram_id(self, telegram_id: int) -> models.User | None:
        return (await self.session.execute(
            select(models.User).where(models.User.telegram_id == telegram_id)
        )).scalar()

    async def is_username_available(self, username: str) -> bool:
        return not bool((await self.session.execute(
            select(models.User.username).where(models.User.username == username)
        )).scalar())

    async def get_by_email(self, email: str) -> models.User | None:
        return (await self.session.execute(
            select(models.User).where(models.User.email == email)
        )).scalar()

    async def get_by_username(self, username: str) -> models.User | None:
        return (await self.session.execute(
            select(models.User).where(models.User.username == username)
        )).scalar()


class PostRepository:
    def __init__(self, session):
        self.session = session

    def add(self, post: models.Post):
        self.session.add(post)

    async def get(self, post_id: int) -> models.Post | None:
        return (await self.session.execute(
            select(models.Post).where(models.Post.id == post_id).options(
                joinedload(models.Post.pictures), joinedload(models.Post.user)
            )
        )).scalar()

    async def list(self, limit: int == 100, user_id: int | None = None) -> models.Post | None:
        stmt = select(models.Post).options(
            joinedload(models.Post.pictures), joinedload(models.Post.user)
        )

        if user_id is not None:
            stmt = stmt.where(models.Post.user_id == user_id)

        return (await self.session.execute(stmt.limit(limit))).unique().scalars()

    async def delete(self, post_id: int) -> models.Post:
        return (await self.session.execute(
            delete(models.Post).where(models.Post.id == post_id).returning(models.Post)
        )).scalar()

    async def remove_bookmark(self, user_id: int, post_id: int) -> models.Post:
        return await self.session.execute(
            delete(models.bookmarks_table).where(and_(
                models.bookmarks_table.c.post_id == post_id,
                models.bookmarks_table.c.user_id == user_id
            ))
        )


class VerifyCodesRepository:
    def __init__(self, session):
        self.session = session

    async def add(self, verify_code: models.VerifyCode):
        await self.session.execute(
            insert(models.VerifyCode)
            .values(
                email=verify_code.email,
                code=verify_code.code,
                expire_at=verify_code.expire_at
            ).on_conflict_do_update(
                index_elements=['email'],
                set_=dict(
                    code=verify_code.code,
                    expire_at=verify_code.expire_at
                )
            )
        )

    async def get(self, email: str) -> models.Post | None:
        return (await self.session.execute(
            select(models.VerifyCode).where(models.VerifyCode.email == email)
        )).scalar()

    async def delete(self, email: str):
        await self.session.execute(
            delete(models.VerifyCode).where(models.VerifyCode.email == email)
        )
