from fastapi import APIRouter, Depends, Query
from starlette import status
from starlette.responses import Response

from app.adapters.security import TokenPayload, JWTCookieBearer
from app.api.users import schemas
from app.api.posts import schemas as p_schemas
from app.api.schemas import ResponseSchema
from app.service_layer.unit_of_work import UnitOfWork

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    path="/me",
    responses={
        status.HTTP_200_OK: {"model": schemas.Me},
        status.HTTP_404_NOT_FOUND: {"model": ResponseSchema}
    }
)
async def get_me(response: Response, payload: TokenPayload = Depends(JWTCookieBearer)):
    async with UnitOfWork() as uow:
        user = await uow.users.get(payload.user_id)

        if not user:
            response.status_code = status.HTTP_404_NOT_FOUND
            return ResponseSchema(detail="Ошибка! Пользователь не найден.")

        return schemas.Me.from_orm(user)


@router.get(
    path="/username",
    responses={
        status.HTTP_200_OK: {"model": schemas.UsernameAvailable},
    }
)
async def is_username_available(username: str = Query(...)):
    async with UnitOfWork() as uow:
        available = await uow.users.is_username_available(username)
        await uow.commit()
    return schemas.UsernameAvailable(available=available)


@router.get(
    path="/{username}",
    responses={
        status.HTTP_200_OK: {"model": schemas.User},
        status.HTTP_404_NOT_FOUND: {"model": ResponseSchema}
    },
    dependencies=[Depends(JWTCookieBearer)]
)
async def get(username: str, response: Response):
    async with UnitOfWork() as uow:
        user = await uow.users.get_by_username(username)
        await uow.commit()

    if not user:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseSchema(detail="Ошибка! Пользователь не найден.")

    return user


@router.get(
    path="/{username}/bookmarks",
    responses={
        status.HTTP_200_OK: {"model": list[p_schemas.Post]},
        status.HTTP_404_NOT_FOUND: {"model": ResponseSchema}
    },
    dependencies=[Depends(JWTCookieBearer)]
)
async def get_bookmarks(username: str):
    async with UnitOfWork() as uow:
        posts = await uow.users.get_bookmarks_by_username(username)
        return list(map(p_schemas.Post.from_orm, posts))
