from contextlib import asynccontextmanager
from logging import getLogger

from fastapi import FastAPI

from app.adapters.security import JWTCookie, JWTCookieProtocol, TokenPayload, JWTCookieBearer
from app.adapters.gallery import Gallery, GalleryProtocol
from app.adapters.gmail import GmailProvider
from app.adapters.mailer import Mailer, MailerProtocol
from app.config import Config


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = Config()
    mail_provider = GmailProvider(getLogger("GmailProvider"))
    mailer = Mailer(getLogger("Mailer"), mail_provider)
    gallery = Gallery(getLogger("Gallery"), "data")
    jwt_cookie = JWTCookie(config.jwt.secret, config.jwt.alg)

    app.dependency_overrides = {
        GalleryProtocol: lambda: gallery,
        MailerProtocol: lambda: mailer,
        JWTCookieProtocol: lambda: jwt_cookie,
        JWTCookieBearer: jwt_cookie
    }
    yield
