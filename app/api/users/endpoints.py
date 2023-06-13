from fastapi import APIRouter, Depends, Query, Form, UploadFile, File
from starlette import status
from starlette.responses import Response

from app.adapters.gallery import IGallery
from app.adapters.security import TokenPayload, JWTCookieBearer, IJWTCookie
from app.api.posts.schemas import CropArea
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
    },
    summary="Получить авторизованного пользователя."
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
    },
    summary="Проверить доступность имени пользователя."
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
    dependencies=[Depends(JWTCookieBearer)],
    summary="Получить пользователя по имени пользователя."
)
async def get(username: str, response: Response):
    async with UnitOfWork() as uow:
        user = await uow.users.get_by_username(username)
        await uow.commit()

    if not user:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseSchema(detail="Ошибка! Пользователь не найден.")

    return schemas.User.from_orm(user)


@router.get(
    path="/{username}/bookmarks",
    responses={
        status.HTTP_200_OK: {"model": list[p_schemas.Post]},
        status.HTTP_404_NOT_FOUND: {"model": ResponseSchema}
    },
    dependencies=[Depends(JWTCookieBearer)],
    summary="Получить закладки пользователя."
)
async def get_bookmarks(username: str):
    async with UnitOfWork() as uow:
        user = await uow.users.get_by_username_with_bookmarks(username)
        return list(map(p_schemas.Post.from_orm, user.bookmarks))


@router.patch(
    path="",
    responses={
        status.HTTP_200_OK: {"model": ResponseSchema},
        status.HTTP_404_NOT_FOUND: {"model": ResponseSchema}
    },
    dependencies=[],
    summary="Обновить пользователя."
)
async def save_changes(
        username: str = Form(None),
        name: str = Form(None),
        bio: str = Form(None),
        area: CropArea = Form(None),
        update_avatar: bool = Form(None, alias="updateAvatar"),
        file: UploadFile = File(None),
        gallery: IGallery = Depends(),
        payload: TokenPayload = Depends(JWTCookieBearer)
):
    async with UnitOfWork() as uow:
        user = await uow.users.get(payload.user_id)

        if file is not None:
            gallery.delete(payload.user_id, user.avatar_id)
            with gallery(await file.read()) as im:
                im.rotate(area.rotate).convert()
                im.crop((area.x, area.y, area.x + area.width, area.y + area.height)).resize(300)
                user.avatar_id = im.save(user.id, original=True, fmt='webp')

        if username is not None:
            user.username = username

        if name is not None:
            user.name = name

        if bio is not None:
            user.bio = bio

        await uow.commit()

    return ResponseSchema(detail="Изменения сохранены.")


@router.delete(
    path="/{user_id}",
    response_model=ResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": ResponseSchema},
        status.HTTP_404_NOT_FOUND: {"model": ResponseSchema},
    },
    summary="Удалить пользователя."
)
async def delete_user(
        user_id: int,
        response: Response,
        gallery: IGallery = Depends(),
        jwt_cookie: IJWTCookie = Depends(),
        payload: TokenPayload = Depends(JWTCookieBearer)
):
    async with UnitOfWork() as uow:
        user = await uow.users.get(payload.user_id)

        if not user:
            response.status_code = status.HTTP_404_NOT_FOUND
            return ResponseSchema(detail="Ошибка! Пользователь не найден.")

        if user.id != user_id:
            response.status_code = status.HTTP_406_NOT_ACCEPTABLE
            return ResponseSchema(detail="Ошибка! Недостаточно прав.")

        await uow.users.delete(user_id)

        await uow.commit()

    gallery.delete(user_id)
    jwt_cookie.remove(response)
    response.status_code = status.HTTP_403_FORBIDDEN
    return ResponseSchema(detail="Пользователь удалён.")
