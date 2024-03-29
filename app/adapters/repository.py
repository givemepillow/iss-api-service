from datetime import datetime

from sqlalchemy import select, delete
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

    # async def get_by_telegram_user_id(self, telegram_user_id: int) -> models.User | None:
    #     return (await self.session.execute(
    #         select(models.User).where(models.User.telegram_user_id == telegram_user_id)
    #     )).scalar()

    async def is_username_available(self, username: str) -> bool:
        return not bool((await self.session.execute(
            select(models.User.username).where(models.User.username == username)
        )).scalar())

    async def get_by_email(self, email: str) -> models.User | None:
        return (await self.session.execute(
            select(models.User).where(models.User.email == email)
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

    async def list(self, from_date: datetime | None, number: int | None) -> models.Post | None:
        return (await self.session.execute(
            select(models.Post).options(
                joinedload(models.Post.pictures), joinedload(models.Post.user)
            )
        )).unique().scalars()

    async def delete(self, post_id: int) -> models.Post:
        return (await self.session.execute(
            delete(models.Post).where(models.Post.id == post_id).returning(models.Post)
        )).scalar()


class VerifyCodesRepository:
    def __init__(self, session):
        self.session = session

    def add(self, verify_code: models.VerifyCode):
        self.session.add(verify_code)

    async def get(self, email: str) -> models.Post | None:
        return (await self.session.execute(
            select(models.VerifyCode).where(models.VerifyCode.email == email)
        )).scalar()

    async def delete(self, email: str):
        await self.session.execute(
            delete(models.VerifyCode).where(models.VerifyCode.email == email)
        )
