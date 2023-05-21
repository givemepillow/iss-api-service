from datetime import datetime, timedelta
from enum import StrEnum, auto
from typing import Protocol

from fastapi import Request, HTTPException

import jwt
from jwt import ExpiredSignatureError
from pydantic import BaseModel
from starlette.responses import Response
from starlette.status import HTTP_403_FORBIDDEN


class Scope(StrEnum):
    primary_user: str = auto()
    signup: str = auto()


class TokenPayload(BaseModel):
    exp: datetime
    iat: datetime
    scope: str
    email: str | None = None
    telegram_id: int | None = None
    user_id: int | None = None


class JWTCookieProtocol(Protocol):
    def __init__(self): pass

    async def __call__(self, request: Request) -> TokenPayload:
        raise NotImplementedError

    def set(
            self,
            response: Response,
            scopes: list[Scope],
            max_age: int,
            user_id: int | None,
            email: str | None,
            telegram_id: int | None
    ):
        raise NotImplementedError


class JWTCookieBearer(Protocol):
    def __init__(self): pass

    async def __call__(self, request: Request) -> TokenPayload:
        raise NotImplementedError


class JWTCookie:

    def __init__(self, secret: str, alg: str):
        self.secret = secret
        self.alg = alg
        self.cookie_key = "iss_access_token"

    async def __call__(self, request: Request) -> TokenPayload:
        credentials = request.cookies.get(self.cookie_key)

        if not credentials:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="not authenticated")
        try:
            token = jwt.decode(
                credentials,
                key=self.secret,
                algorithms=[self.alg]
            )
        except jwt.exceptions.DecodeError:
            raise HTTPException(status_code=403, detail="invalid token.")
        except ExpiredSignatureError:
            raise HTTPException(status_code=403, detail="token is expired.")
        return TokenPayload(**token)

    def _issue(
            self,
            scopes: list[Scope],
            seconds: int,
            user_id: int | None = None,
            email: str | None = None,
            telegram_id: int | None = None
    ) -> str:
        return jwt.encode(
            payload=TokenPayload(
                exp=datetime.utcnow() + timedelta(seconds=seconds),
                iat=datetime.utcnow(),
                user_id=user_id,
                email=email,
                telegram_id=telegram_id,
                scope=' '.join(scopes)
            ).dict(),
            key=self.secret,
            algorithm=self.alg
        )

    def set(
            self,
            response: Response,
            scopes: list[Scope],
            max_age: int,
            user_id: int | None = None,
            email: str | None = None,
            telegram_id: int | None = None

    ):
        access_token = self._issue(
            scopes=scopes,
            user_id=user_id,
            telegram_id=telegram_id,
            email=email,
            seconds=max_age
        )
        response.set_cookie(key=self.cookie_key, value=access_token, max_age=max_age, samesite="none", secure=True)
