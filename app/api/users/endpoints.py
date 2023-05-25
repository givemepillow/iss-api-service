from fastapi import APIRouter, Depends, Query
from starlette import status
from starlette.responses import Response

from app.adapters.security import TokenPayload, JWTCookieBearer
from app.api.users import schemas
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
        user = await uow.users.get_by_email(payload.email)
        await uow.commit()

    if not user:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseSchema(detail="Ошибка! Пользователь не найден.")

    return user


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
