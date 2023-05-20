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
    sub: int | None
    email: str
    scope: str


class JWTCookieProtocol(Protocol):
    def __init__(self): pass

    async def __call__(self, request: Request) -> TokenPayload:
        raise NotImplementedError

    def set(
            self,
            response: Response,
            scopes: list[Scope],
            max_age: int,
            sub: int | None = None,
            email: str | None = None
    ) -> None:
        raise NotImplementedError


class JWTCookie:

    def __init__(self, secret: str, alg: str):
        self.secret = secret
        self.alg = alg
        self.cookie_key = "iss_access_token"

    async def __call__(self, request: Request) -> TokenPayload:
        credentials = request.cookies.get(self.cookie_key)

        if not credentials:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
            )
        try:
            token = jwt.decode(
                credentials,
                key=self.secret,
                algorithms=[self.alg]
            )
        except jwt.exceptions.DecodeError:
            raise HTTPException(status_code=403, detail="Invalid token.")
        except ExpiredSignatureError:
            raise HTTPException(status_code=403, detail="Token is expired.")
        return TokenPayload(**token)

    def _issue(
            self,
            scopes: list[Scope],
            seconds: int,
            sub: int | None = None,
            email: str | None = None
    ) -> str:
        return jwt.encode(
            payload=TokenPayload(
                exp=datetime.utcnow() + timedelta(seconds=seconds),
                iat=datetime.utcnow(),
                sub=sub,
                email=email,
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
            sub: int | None = None,
            email: str | None = None
    ) -> None:
        access_token = self._issue(scopes=scopes, sub=sub, email=email, seconds=max_age)
        response.set_cookie(key=self.cookie_key, value=access_token, max_age=max_age)
