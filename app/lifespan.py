from contextlib import asynccontextmanager
from logging import getLogger

from fastapi import FastAPI

from app.adapters.discussion import Discussion, IDiscussion
from app.adapters.security import JWTCookie, IJWTCookie, JWTCookieBearer
from app.adapters.gallery import Gallery, IGallery
from app.adapters.gmail import GmailProvider
from app.adapters.mailer import Mailer, IMailer
from app.utils.config import Config


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = Config()
    mail_provider = GmailProvider(getLogger("GmailProvider"))
    mailer = Mailer(getLogger("Mailer"), mail_provider)
    gallery = Gallery(getLogger("Gallery"), "data")
    jwt_cookie = JWTCookie(config.jwt.secret, config.jwt.alg)
    discussion = Discussion()

    app.dependency_overrides = {
        IGallery: lambda: gallery,
        IMailer: lambda: mailer,
        IJWTCookie: lambda: jwt_cookie,
        JWTCookieBearer: jwt_cookie,
        IDiscussion: lambda: discussion
    }
    yield
