from datetime import datetime

from pydantic import BaseModel, Field


class Me(BaseModel):
    id: int
    username: str
    name: str
    bio: str | None
    email: str | None
    telegram_id: int | None
    registered_at: datetime = Field(alias="registeredAt")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class UsernameAvailable(BaseModel):
    available: bool


class User(BaseModel):
    id: int
    username: str
    name: str
    bio: str

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
