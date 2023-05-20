from contextlib import asynccontextmanager
from logging import getLogger
from logging.config import fileConfig

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api import post, user, auth
from app.lifespan import lifespan

fileConfig('logging.conf', disable_existing_loggers=False)

app = FastAPI(debug=False, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["PUT", "DELETE", "PATCH", "GET", "POST"],
    allow_headers=["Cookie"],
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(post.router)

uvicorn.run(app, host="localhost", port=8008)
