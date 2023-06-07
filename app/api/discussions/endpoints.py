from typing import cast

import orjson
from fastapi import APIRouter, Depends
from starlette.requests import Request
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.adapters.discussion import IDiscussion
from app.adapters.security import IJWTCookie, JWTCookieBearer
from app.api.discussions import schemas
from app.domain import models

from app.service_layer.unit_of_work import UnitOfWork

router = APIRouter(prefix="/discussions", tags=["Discussions"])


@router.get(
    path="/{post_id}/messages",
    dependencies=[Depends(JWTCookieBearer)],
    summary="Получить сообщения обсуждения."
)
async def get_messages(post_id: int):
    async with UnitOfWork() as uow:
        comments = await uow.comments.list(post_id)
        outbound_comments = list(map(schemas.OutboundComment.from_orm, comments))
        await uow.commit()

    return outbound_comments


@router.websocket(path="/{post_id}")
async def join_discussion(
        post_id: int,
        w: WebSocket,
        discussion: IDiscussion = Depends(),
        jwt_cookie: IJWTCookie = Depends()
):
    payload = await jwt_cookie(cast(Request, w))
    await w.accept()
    await discussion.join(w, post_id)
    try:
        while True:
            inbound_comment = schemas.InboundComment(**(await w.receive_json()))

            message = models.Message(
                text=inbound_comment.text,
                post_id=post_id,
                user_id=payload.user_id
            )

            async with UnitOfWork() as uow:
                user = await uow.users.get(payload.user_id)
                user.messages.append(message)
                await uow.commit()

            outbound_comment = schemas.OutboundComment(
                id=message.id,
                text=message.text,
                sent_at=message.sent_at,
                user=schemas.CommentUser.from_orm(user)
            )

            await discussion.send(post_id, orjson.dumps(outbound_comment.dict(by_alias=True)).decode())

    except WebSocketDisconnect:
        pass
    finally:
        await discussion.leave(w, post_id)
