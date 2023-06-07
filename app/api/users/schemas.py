from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Me(BaseModel):
    id: int
    username: str
    name: str
    bio: str | None
    email: str | None
    telegram_id: int | None
    avatar_id: UUID | None = Field(alias="avatarId")
    registered_at: datetime = Field(alias="registeredAt")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class UsernameAvailable(BaseModel):
    available: bool


class User(BaseModel):
    id: int
    username: str
    name: str | None
    bio: str | None
    avatar_id: UUID | None = Field(alias="avatarId")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
