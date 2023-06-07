from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import FileResponse, Response

from app.adapters.gallery import IGallery, Source
from app.service_layer.unit_of_work import UnitOfWork

router = APIRouter(prefix="/pictures", tags=["Pictures"])


@router.get(
    path="/" + Source.optimized + "/{user_id}/{picture_id}",
    summary="Получить изображение."
)
async def get_picture(
        user_id: int,
        picture_id: str,
        response: Response,
        gallery: IGallery = Depends()
):
    try:
        return FileResponse(
            gallery.get_path(Source.optimized, user_id, picture_id),
            media_type="image/*",
            filename="picture.jpg"
        )
    except FileNotFoundError:
        response.status_code = status.HTTP_404_NOT_FOUND


@router.get(
    path="/" + Source.original + "/{user_id}/{picture_id}",
    summary="Получить оригинал изображения."
)
async def get_picture(
        user_id: int,
        picture_id: str,
        response: Response,
        gallery: IGallery = Depends()
):
    async with UnitOfWork() as uow:
        picture = await uow.pictures.get(picture_id)
        picture.post.downloads += 1
        await uow.commit()

    try:
        return FileResponse(
            gallery.get_path(Source.original, user_id, picture_id),
            media_type=f"image/{picture.format}",
            filename=f"{picture.post.user.username}_{str(picture.id).split('-')[-1]}.{picture.format}"
        )
    except FileNotFoundError:
        response.status_code = status.HTTP_404_NOT_FOUND
