from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import Response

from app import schemas
from app.adapters.security import JWTCookie
from app.service_layer.unit_of_work import UnitOfWork

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/username", responses={
    200: {"model": schemas.Response},
    409: {"model": schemas.Response}
}, dependencies=[Depends(JWTCookie)])
async def usernames_available(username: str, response: Response):
    async with UnitOfWork() as uow:
        if await uow.users.is_username_available(username):
            response.status_code = status.HTTP_200_OK
            return schemas.Response(message="username available")
    response.status_code = status.status.HTTP_409_CONFLICT
    return schemas.Response(message="username already taken")


@router.get("/users/{user_id}", responses={
    200: {"model": schemas.User},
    404: {"model": schemas.Response}
})
async def get_user(user_id: int, response: Response):
    async with UnitOfWork() as uow:
        if not (user := await uow.users.get(user_id)):
            response.status_code = status.HTTP_404_NOT_FOUND
            return schemas.Response(message="user not found")
    return schemas.User.from_orm(user)
