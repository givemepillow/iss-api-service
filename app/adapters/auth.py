from datetime import datetime, timedelta
from enum import StrEnum, auto
from typing import final

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer

import jwt
from jwt import ExpiredSignatureError
from pydantic import BaseModel
from starlette.status import HTTP_403_FORBIDDEN

from app.config import Configuration

config = Configuration()  # TODO: избавиться!

COOKIE_KEY: final = "iss_access_token"


class Scope(StrEnum):
    primary_user: str = auto()
    signup: str = auto()


class TokenPayload(BaseModel):
    exp: datetime
    iat: datetime
    sub: int | None
    email: str
    scope: str


class JWTCookie(HTTPBearer):  # TODO: DI конфига - нужно передавать параметры, а не весь объект.
    COOKIE_KEY: final = "iss_access_token"

    async def __call__(self, request: Request) -> TokenPayload:
        credentials = request.cookies.get(self.COOKIE_KEY)

        if not credentials:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
            )
        try:
            token = jwt.decode(
                credentials,
                key=config.jwt.secret,
                algorithms=[config.jwt.alg]
            )
        except jwt.exceptions.DecodeError:
            raise HTTPException(status_code=403, detail="Invalid token.")
        except ExpiredSignatureError:
            raise HTTPException(status_code=403, detail="Token is expired.")
        return TokenPayload(**token)


class Token:
    def __init__(
            self,
            scopes: list[Scope],
            seconds: int,
            sub: int | None = None,
            email: str | None = None
    ):
        self.payload = TokenPayload(
            exp=datetime.utcnow() + timedelta(seconds=seconds),
            iat=datetime.utcnow(),
            sub=sub,
            email=email,
            scope=' '.join(scopes)
        ).dict()

    def __str__(self):
        return jwt.encode(
            self.payload,
            key=config.jwt.secret,
            algorithm=config.jwt.alg
        )
