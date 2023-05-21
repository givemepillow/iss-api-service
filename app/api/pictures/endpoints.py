from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import FileResponse, Response

from app.adapters.gallery import GalleryProtocol, Source

router = APIRouter(prefix="/pictures", tags=["Pictures"])


@router.get("/{source}/{user_id}/{picture_id}")
async def get_picture(
        source: Source,
        user_id: int,
        picture_id: UUID,
        response: Response,
        gallery: GalleryProtocol = Depends()
):
    try:
        return FileResponse(
            gallery.path(source, str(user_id), str(picture_id)),
            media_type="image/*",
            filename="picture.jpg"
        )
    except FileNotFoundError:
        response.status_code = status.HTTP_404_NOT_FOUND
