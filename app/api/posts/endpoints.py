from datetime import datetime

from fastapi import APIRouter, UploadFile, Depends
from fastapi.params import Form, File, Query
from sqlalchemy.exc import IntegrityError
from starlette import status
from starlette.responses import Response

from app.adapters.security import TokenPayload, JWTCookieBearer
from app.api.posts import schemas
from app.adapters.gallery import GalleryProtocol
from app.api.schemas import ResponseSchema
from app.service_layer import dto, services
from app.service_layer.unit_of_work import UnitOfWork

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.post(
    path="",
    status_code=200,
    response_model=ResponseSchema
)
async def create_post(
        title: str = Form(""),
        description: str = Form(""),
        aspect_ratio: float = Form(..., alias="aspectRatio"),
        save_originals: list[bool] = Form(..., alias="saveOriginals"),
        areas: list[schemas.CropArea] = Form(...),
        files: list[UploadFile] = File(...),
        gallery: GalleryProtocol = Depends(),
        payload: TokenPayload = Depends(JWTCookieBearer)
):
    new_post = dto.NewPost(
        title=title,
        description=description,
        aspect_ratio=aspect_ratio,
        user_id=payload.user_id,
        pictures=[]
    )

    for file, area, save_original in zip(files, areas, save_originals):
        new_post.pictures.append(dto.NewPicture(
            file_bytes=await file.read(),
            crop_box=(area.x, area.y, area.x + area.width, area.y + area.height),
            save_original=save_original,
            rotate=area.rotate
        ))
        await file.close()
    await services.publish_post(new_post, gallery)

    return ResponseSchema(detail="Опубликовано.")


@router.get(
    path="",
    status_code=200,
    response_model=list[schemas.Post],
    response_model_by_alias=True
)
async def list_posts(
        limit: int = Query(100),
        user_id: int | None = Query(None),
        payload: TokenPayload = Depends(JWTCookieBearer)
):
    async with UnitOfWork() as uow:
        posts = await uow.posts.list(limit, user_id)
        await uow.commit()
    return list(map(schemas.Post.from_orm, posts))


@router.get(
    path="/{post_id}",
    status_code=200,
    responses={
        status.HTTP_200_OK: {"model": schemas.Post},
        status.HTTP_404_NOT_FOUND: {"model": ResponseSchema},
    },
    response_model_by_alias=True
)
async def get_post(
        post_id: int,
        response: Response,
        payload: TokenPayload = Depends(JWTCookieBearer)
):
    async with UnitOfWork() as uow:
        post = await uow.posts.get(post_id)

        if not post:
            response.status_code = status.HTTP_404_NOT_FOUND
            return ResponseSchema(detail="post not found")
        post.views += 1
        return schemas.Post.from_orm(post)


@router.delete(
    path="/{post_id}",
    response_model=ResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": ResponseSchema},
        status.HTTP_404_NOT_FOUND: {"model": ResponseSchema},
    }
)
async def delete_post(
        post_id: int,
        response: Response,
        gallery: GalleryProtocol = Depends(),
        payload: TokenPayload = Depends(JWTCookieBearer)
):
    async with UnitOfWork() as uow:
        post = await uow.posts.get(post_id)

        if not post:
            response.status_code = status.HTTP_404_NOT_FOUND
            return ResponseSchema(detail="Ошибка! Публикация не найдена.")

        for pic in post.pictures:
            gallery.delete(str(post.user_id), str(pic.id))

        await uow.posts.delete(post_id)
        await uow.commit()

    return ResponseSchema(detail="Публикация удалена.")


@router.post(
    path="/{post_id}/bookmark",
    responses={
        status.HTTP_200_OK: {"model": ResponseSchema},
        status.HTTP_404_NOT_FOUND: {"model": ResponseSchema}
    }
)
async def save_bookmark(post_id: int, response: Response, payload: TokenPayload = Depends(JWTCookieBearer)):
    try:
        async with UnitOfWork() as uow:

            if not (user := await uow.users.get(payload.user_id)):
                response.status_code = status.HTTP_404_NOT_FOUND
                return ResponseSchema(detail="Ошибка! Пользователь не найден.")

            if not (post := await uow.posts.get(post_id)):
                response.status_code = status.HTTP_404_NOT_FOUND
                return ResponseSchema(detail="Ошибка! Публикация не найдена.")

            user.bookmarks.append(post)
            await uow.commit()
    except IntegrityError:
        response.status_code = status.HTTP_409_CONFLICT
        return ResponseSchema(detail="Ошибка! Закладка уже добавлена.")

    return ResponseSchema(detail="Публикация сохранена в закладки.")


@router.delete(
    path="/{post_id}/bookmark",
    responses={
        status.HTTP_200_OK: {"model": ResponseSchema},
        status.HTTP_404_NOT_FOUND: {"model": ResponseSchema}
    }
)
async def remove_bookmark(post_id: int, payload: TokenPayload = Depends(JWTCookieBearer)):
    async with UnitOfWork() as uow:
        await uow.posts.remove_bookmark(payload.user_id, post_id)
        await uow.commit()

    return ResponseSchema(detail="Публикация убрана из закладок.")
