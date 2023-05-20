from __future__ import annotations
import json
import uuid
from datetime import datetime

from fastapi import Form
from pydantic import BaseModel, EmailStr, Field


class SignInEmail(BaseModel):
    email: EmailStr


class SignInCode(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=4)


class SignUp(BaseModel):
    username: str = Field(min_length=3, max_length=25)
    name: str | None


class Response(BaseModel):
    message: str


class User(BaseModel):
    id: int
    username: str
    email: str
    name: str
    bio: str
    registered_at: str


class Picture(BaseModel):
    id: uuid.UUID
    size: int
    height: int
    width: int
    format: str


class Post(BaseModel):
    id: int
    title: str
    description: str
    created_at: datetime
    pictures: list[Picture]
    user: User


class CropArea(BaseModel):
    height: int
    width: int
    rotate: int
    x: int
    y: int

    @classmethod
    def from_form(cls, areas: list[str] = Form(...)) -> list[CropArea]:
        return [cls(**json.loads(a)) for a in areas]

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


