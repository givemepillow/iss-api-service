from abc import ABC

from starlette.websockets import WebSocket

from app.utils.interface import Interface


class Discussion:
    def __init__(self):
        self.discussions = {}

    async def join(self, websocket: WebSocket, post_id: int):
        self.discussions.setdefault(post_id, set()).add(websocket)

    async def leave(self, websocket: WebSocket, post_id: int):
        self.discussions[post_id].remove(websocket)

        if not self.discussions[post_id]:
            del self.discussions[post_id]

    async def send(self, post_id: int, comment: str):
        for w in self.discussions[post_id]:
            await w.send_text(comment)


class IDiscussion(Interface, Discussion):
    pass
