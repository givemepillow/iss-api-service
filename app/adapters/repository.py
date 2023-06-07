from datetime import datetime

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

    async def get_by_username_with_bookmarks(self, username: str) -> models.User | None:
        return (await self.session.execute(
            select(models.User).options(
                joinedload(models.User.bookmarks).joinedload(models.Post.user),
                joinedload(models.User.bookmarks).joinedload(models.Post.pictures),
            ).where(models.User.username == username)
        )).scalar()

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

    async def delete(self, user_id: int) -> models.Post:
        return await self.session.execute(
            delete(models.User).where(models.User.id == user_id)
        )


class PostRepository:
    def __init__(self, session):
        self.session = session

    def add(self, post: models.Post):
        self.session.add(post)

    async def get(self, post_id: int) -> models.Post | None:
        return (await self.session.execute(
            select(models.Post).options(
                joinedload(models.Post.pictures),
                joinedload(models.Post.user),
                joinedload(models.Post.in_bookmarks),
                joinedload(models.Post.views)
            ).where(models.Post.id == post_id)
        )).scalar()

    async def get_by_picture(self, picture_id: int) -> models.Post | None:
        return (await self.session.execute(
            select(models.Post).join(
                models.Picture, models.Picture.id == picture_id).options(
                joinedload(models.Post.pictures), joinedload(models.Post.user)
            )
        )).scalar()

    async def list(
            self,
            limit: int,
            user_id: int | None = None,
            last_created_at: datetime | None = None,
    ) -> models.Post | None:
        stmt = select(models.Post).options(
            joinedload(models.Post.pictures),
            joinedload(models.Post.user)
        )

        if user_id is not None:
            stmt = stmt.where(models.Post.user_id == user_id)

        if last_created_at is not None:
            stmt = stmt.where(models.Post.created_at < last_created_at)

        stmt = stmt.order_by(models.Post.created_at.desc()).limit(limit)

        return (await self.session.execute(stmt)).unique().scalars()

    async def delete(self, post_id: int) -> models.Post:
        return await self.session.execute(
            delete(models.Post).where(models.Post.id == post_id)
        )

    async def remove_bookmark(self, user_id: int, post_id: int) -> models.Post:
        return await self.session.execute(
            delete(models.bookmarks_table).where(and_(
                models.bookmarks_table.c.post_id == post_id,
                models.bookmarks_table.c.user_id == user_id
            ))
        )


class PictureRepository:
    def __init__(self, session):
        self.session = session

    async def get(self, picture_id: str) -> models.Picture | None:
        return (await self.session.execute(
            select(models.Picture).where(models.Picture.id == picture_id).options(
                joinedload(models.Picture.post).joinedload(models.Post.user)
            )
        )).scalar()


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


class CommentRepository:
    def __init__(self, session):
        self.session = session

    # async def add(self, comment: models.Comment):
    #     return (await self.session.execute(
    #         insert(models.Comment).values(
    #             text=comment.text,
    #             sent_at=comment.sent_at,
    #             post_id=comment.post_id,
    #             user_id=comment.user_id
    #         ).returning(models.Comment).options(
    #             joinedload(models.Comment.user)
    #         )
    #     )).scalar()

    def add(self, message: models.Message):
        return self.session.add(message)

    # async def get(self, post_id: int) -> models.Post | None:
    #     return (await self.session.execute(
    #         select(models.Post).where(models.Post.id == post_id).options(
    #             joinedload(models.Post.pictures), joinedload(models.Post.user)
    #         )
    #     )).scalar()

    async def list(self, post_id: int) -> models.Post | None:
        stmt = select(models.Message).options(
            joinedload(models.Message.user)
        ).where(models.Message.post_id == post_id)

        return (await self.session.execute(stmt)).unique().scalars()
