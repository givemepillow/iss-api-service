from fastapi import APIRouter, Depends

from starlette.responses import FileResponse, Response

from app.adapters.gallery import IGallery, Source

router = APIRouter(prefix="/avatars", tags=["Avatars"])


@router.get(
    path="/{source}/{user_id}/{avatar_id}",
    summary="Получить фото профиля."
)
async def get_avatar(response: Response, source: Source, user_id: int, avatar_id: str, gallery: IGallery = Depends()):
    r = FileResponse(
        gallery.get_path(source, user_id, avatar_id, is_avatar=True),
        headers=response.headers,
        media_type="image/webp",
        filename="avatar.webp"
    )
    print(f"{response.headers=}")
    return r
