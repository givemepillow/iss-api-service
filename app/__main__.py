from contextlib import asynccontextmanager
from logging import getLogger
from logging.config import fileConfig

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app import api
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

app.include_router(api.authorization_router)
app.include_router(api.posts_router)
app.include_router(api.users_router)
app.include_router(api.pictures_router)

uvicorn.run(app, host="localhost", port=8008)
