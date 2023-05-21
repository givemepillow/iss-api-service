from __future__ import annotations

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.adapters.orm import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(sa.String(25), nullable=False)
    email: Mapped[str] = mapped_column(sa.String(75), nullable=True)
    telegram_id: Mapped[int] = mapped_column(sa.BigInteger, nullable=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=True)
    bio: Mapped[str] = mapped_column(sa.String(500), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), default=sa.func.now(tz='UTC'))
    posts: Mapped[list[Post]] = relationship(
        back_populates="user",
        cascade="all, delete",
        lazy='noload',
        innerjoin=True
    )
    __table_args__ = (
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(sa.String(25), nullable=False)
    description: Mapped[str] = mapped_column(sa.String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=sa.func.now(tz='UTC')
    )
    user_id: Mapped[int] = mapped_column(sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pictures: Mapped[list[Picture]] = relationship(
        cascade="all, delete",
        lazy='noload',
        innerjoin=True
    )
    user: Mapped[User] = relationship(
        back_populates="posts",
        lazy='noload',
        innerjoin=True
    )


class Picture(Base):
    __tablename__ = "pictures"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True)
    format: Mapped[str] = mapped_column(sa.String(4), nullable=False)
    size: Mapped[int] = mapped_column(nullable=False)
    height: Mapped[int] = mapped_column(nullable=False)
    width: Mapped[int] = mapped_column(nullable=False)
    post_id: Mapped[int] = mapped_column(sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)


class VerifyCode(Base):
    __tablename__ = "verify_codes"

    email: Mapped[str] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(sa.String(length=4))
    expire_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=sa.func.now(tz='UTC')
    )
