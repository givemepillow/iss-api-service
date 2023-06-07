from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.adapters.orm import Base

bookmarks_table = sa.Table(
    "bookmarks",
    Base.metadata,
    sa.Column("user_id", sa.ForeignKey("users.id", ondelete="CASCADE")),
    sa.Column("post_id", sa.ForeignKey("posts.id", ondelete="CASCADE")),
    sa.UniqueConstraint("user_id", "post_id")
)

views_table = sa.Table(
    "views",
    Base.metadata,
    sa.Column("user_id", sa.ForeignKey("users.id", ondelete="CASCADE")),
    sa.Column("post_id", sa.ForeignKey("posts.id", ondelete="CASCADE")),
    sa.UniqueConstraint("user_id", "post_id")
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, compare=True)
    username: Mapped[str] = mapped_column(sa.String(25), nullable=False)
    email: Mapped[str] = mapped_column(sa.String(75), nullable=True)
    telegram_id: Mapped[int] = mapped_column(sa.BigInteger, nullable=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=True)
    bio: Mapped[str] = mapped_column(sa.String(200), nullable=True)
    avatar_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), default=sa.func.now(tz='UTC'))
    posts: Mapped[list[Post]] = relationship(
        back_populates="user",
        cascade="all, delete",
        lazy='noload',
        innerjoin=True
    )
    bookmarks: Mapped[set[Post]] = relationship(
        collection_class=set,
        back_populates="in_bookmarks",
        secondary=bookmarks_table,
        cascade="all, delete",
        lazy='noload',
        innerjoin=False
    )
    viewed: Mapped[set[Post]] = relationship(
        collection_class=set,
        back_populates="views",
        secondary=views_table,
        cascade="all, delete",
        lazy='noload',
        innerjoin=False
    )
    messages: Mapped[list[Message]] = relationship(
        back_populates='user',
        lazy='noload'
    )
    __table_args__ = (
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other: User):
        return self.id == other.id


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(sa.String(25), nullable=False)
    description: Mapped[str] = mapped_column(sa.String(2500), nullable=True)
    aspect_ratio: Mapped[float] = mapped_column(sa.Float(3), nullable=False)
    downloads: Mapped[int] = mapped_column(server_default='0')

    user_id: Mapped[int] = mapped_column(sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    in_bookmarks: Mapped[set[User]] = relationship(
        collection_class=set,
        back_populates="bookmarks",
        secondary=bookmarks_table,
        cascade="all, delete",
        lazy='noload',
        innerjoin=False
    )
    views: Mapped[set[User]] = relationship(
        collection_class=set,
        secondary=views_table,
        back_populates="viewed",
        cascade="all, delete",
        lazy='noload',
        innerjoin=False
    )

    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), default=sa.func.now(tz='UTC'))

    pictures: Mapped[list[Picture]] = relationship(
        back_populates="post",
        cascade="all, delete",
        lazy='noload',
        innerjoin=True
    )
    user: Mapped[User] = relationship(
        back_populates="posts",
        lazy='noload',
        innerjoin=True
    )

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other: User):
        return self.id == other.id


class Picture(Base):
    __tablename__ = "pictures"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True)
    format: Mapped[str] = mapped_column(sa.String(4), nullable=False)
    size: Mapped[int] = mapped_column(nullable=False)
    height: Mapped[int] = mapped_column(nullable=False)
    width: Mapped[int] = mapped_column(nullable=False)

    post_id: Mapped[int] = mapped_column(sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    post: Mapped[Post] = relationship(
        back_populates="pictures",
        cascade="all, delete",
        lazy='noload',
        innerjoin=True
    )


class VerifyCode(Base):
    __tablename__ = "verify_codes"

    email: Mapped[str] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(sa.String(length=4))
    attempts: Mapped[int] = mapped_column(sa.SmallInteger, default=5, nullable=False)
    expire_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), default=sa.func.now(tz='UTC'))


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(sa.String(length=1000), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), default=sa.func.now(tz='UTC'))

    post_id: Mapped[int] = mapped_column(sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    user: Mapped[User] = relationship(
        back_populates='messages',
        lazy='joined',
        innerjoin=True
    )
