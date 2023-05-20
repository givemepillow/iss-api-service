from datetime import datetime

from fastapi import APIRouter, UploadFile, Depends
from fastapi.params import Form, File
from app import schemas
from app.adapters.gallery import GalleryProtocol
from app.service_layer import dto, services
from app.service_layer.unit_of_work import UnitOfWork

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.post("/", status_code=201)
async def create_post(
        title: str = Form(""),
        description: str = Form(""),
        save_originals: list[bool] = Form(..., alias="saveOriginals"),
        areas: list[schemas.CropArea] = Form(...),
        files: list[UploadFile] = File(...),
        gallery: GalleryProtocol = Depends(),
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

    await services.publish_post(new_post, gallery, UnitOfWork())

    return schemas.Response(message="post published")


@router.get("/", status_code=200)
async def list_posts(
        from_date: datetime | None,
        number: int | None,
) -> list[schemas.Post]:
    async with UnitOfWork() as uow:
        return uow.posts.list(from_date, number)
