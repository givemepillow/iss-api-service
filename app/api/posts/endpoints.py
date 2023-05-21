from datetime import datetime

from fastapi import APIRouter, UploadFile, Depends
from fastapi.params import Form, File, Query
from starlette import status
from starlette.responses import Response

from app.adapters.security import TokenPayload, JWTCookie
from app.api.posts import schemas
from app.adapters.gallery import GalleryProtocol
from app.api.schemas import ResponseSchema
from app.service_layer import dto, services
from app.service_layer.unit_of_work import UnitOfWork

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.post(
    path="/",
    status_code=200,
    response_model=ResponseSchema
)
async def create_post(
        title: str = Form(""),
        description: str = Form(""),
        save_originals: list[bool] = Form(..., alias="saveOriginals"),
        areas: list[schemas.CropArea] = Form(...),
        files: list[UploadFile] = File(...),
        gallery: GalleryProtocol = Depends()
):
    new_post = dto.NewPost(
        title=title,
        description=description,
        user_id=0,
        pictures=[]
    )

    for file, area, save_original in zip(files, areas, save_originals):
        new_post.pictures.append(dto.NewPicture(
            file_bytes=await file.read(),
            crop_box=(area.x, area.y, area.x + area.width, area.y + area.height),
            save_original=save_original
        ))
        await file.close()

    await services.publish_post(new_post, gallery)

    return ResponseSchema(message="post published")


@router.get(
    path="/",
    status_code=200,
    response_model=list[schemas.Post]
)
async def list_posts(
        from_date: datetime = Query(None),
        number: int | None = Query(None),
        # payload: TokenPayload = Depends(JWTCookie)
):
    async with UnitOfWork() as uow:
        posts = await uow.posts.list(from_date, number)
        await uow.commit()
    return list(posts)


@router.get(
    path="/{post_id}",
    status_code=200,
    responses={
        status.HTTP_200_OK: {"model": schemas.Post},
        status.HTTP_404_NOT_FOUND: {"model": ResponseSchema},
    }
)
async def get_post(post_id: int, response: Response):
    async with UnitOfWork() as uow:
        post = await uow.posts.get(post_id)
        await uow.commit()
    if not post:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseSchema(message="post not found")
    return post


@router.delete(
    path="/{post_id}",
    response_model=ResponseSchema,
    responses={
        status.HTTP_200_OK: {"model": ResponseSchema},
        status.HTTP_404_NOT_FOUND: {"model": ResponseSchema},
    }
)
async def delete_post(post_id: int, response: Response, gallery: GalleryProtocol = Depends()):
    async with UnitOfWork() as uow:
        post = await uow.posts.delete(post_id)
        await uow.commit()

    if not post:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseSchema(message="post not found")

    for pic in post.pictures:
        gallery.delete(post.user_id, str(pic.id))
    return ResponseSchema(message="post deleted")
