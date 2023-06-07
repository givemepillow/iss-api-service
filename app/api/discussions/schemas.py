from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, validator


class CommentUser(BaseModel):
    id: int
    username: str
    name: str | None
    avatar_id: str | None = Field(alias="avatarId")

    @validator('avatar_id', pre=True)
    def name_must_be_str(cls, v):
        return str(v)

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class InboundComment(BaseModel):
    text: str


class OutboundComment(BaseModel):
    id: int
    text: str
    user: CommentUser
    sent_at: datetime = Field(alias="sentAt")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
