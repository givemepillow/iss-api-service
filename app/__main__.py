import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocket

from app import api
from app.utils.config import Config
from app.lifespan import lifespan

app = FastAPI(debug=False, lifespan=lifespan)

config = Config()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.app.origins,
    allow_credentials=True,
    allow_methods=["PUT", "DELETE", "PATCH", "GET", "POST"],
    allow_headers=["Cookie"],
)

app.include_router(api.authorization_router)
app.include_router(api.posts_router)
app.include_router(api.users_router)
app.include_router(api.pictures_router)
app.include_router(api.discussions_router)
app.include_router(api.avatars_router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")


uvicorn.run(app, host=config.app.host, port=config.app.port)
