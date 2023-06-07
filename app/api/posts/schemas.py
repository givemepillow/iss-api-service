import json
from datetime import datetime
from uuid import UUID

from fastapi import Form
from pydantic import BaseModel, Field


class User(BaseModel):
    id: int
    username: str | None
    name: str | None
    avatar_id: UUID | None = Field(alias="avatarId")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other: "User"):
        return self.id == other.id


class Picture(BaseModel):
    id: UUID
    size: int
    height: int
    width: int
    format: str

    class Config:
        orm_mode = True


class Post(BaseModel):
    id: int
    title: str
    description: str
    user: User
    downloads: int
    views: list[User] = Field(default_factory=list)
    in_bookmarks: list[User] = Field(default_factory=list)
    aspect_ratio: float = Field(alias="aspectRatio")
    created_at: datetime = Field(alias="createdAt")
    pictures: list[Picture] = Field(default_factory=list)

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        validate_assignment = True


class CropArea(BaseModel):
    height: int
    width: int
    rotate: int
    x: int
    y: int

    @classmethod
    def from_form(cls, areas: list[str] = Form(...)) -> list["CropArea"]:
        return [cls(**json.loads(a)) for a in areas]

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value
