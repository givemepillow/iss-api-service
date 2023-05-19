from logging.config import fileConfig

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app import endpoints
from app.adapters.mailer import Mailer, MailerProtocol
fileConfig('logging.conf', disable_existing_loggers=False)

app = FastAPI(debug=True)


@app.on_event('startup')
async def on_startup():
    email = Mailer()

    app.dependency_overrides = {
        MailerProtocol: lambda: email,
    }


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["PUT", "DELETE", "PATCH", "GET", "POST"],
    allow_headers=["Cookie"],
)
app.include_router(endpoints.router)

uvicorn.run(app, host="localhost", port=8008)
