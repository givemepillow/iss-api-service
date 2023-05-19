import json
from datetime import datetime
from logging import getLogger
from uuid import uuid4

from fastapi import APIRouter, status, Response, Depends, Form, UploadFile, File
from starlette.responses import JSONResponse

from app import schemas
from app.adapters.auth import JWTCookie, Scope, TokenPayload, Token
from app.adapters.gallery import ImageManager
from app.adapters.mailer import MailerProtocol
from app.domain import models
from app.service_layer.unit_of_work import UnitOfWork

router = APIRouter()
logger = getLogger(__name__)


@router.post("/authorization/email", status_code=200)
async def verify_email(
        email_data: schemas.SignInEmail,
        mailer: MailerProtocol = Depends(),
):
    await mailer.send_code(email_data.email)
    return {"message": "code sent"}


@router.post("/authorization/code", responses={
    200: {"model": schemas.Response},
    401: {"model": schemas.Response}
})
async def confirm_code(
        response: Response,
        confirm_data: schemas.SignInCode,
        mailer: MailerProtocol = Depends(),
):
    if not mailer.confirm_code(confirm_data.email, confirm_data.code):
        return JSONResponse(dict(message="code does not match"), status.HTTP_401_UNAUTHORIZED)

    async with UnitOfWork() as uow:
        user = await uow.users.get_by_email(confirm_data.email)

    if user:
        week = 60 * 60 * 24 * 7  # 1 неделя
        access_token = Token(scopes=[Scope.primary_user], email=confirm_data.email, seconds=week)
        response.set_cookie(key=JWTCookie.COOKIE_KEY, value=str(access_token), max_age=week)
        return schemas.User.from_orm(user)
    else:
        half_hour = 60 * 30  # 30 мин
        access_token = Token(scopes=[Scope.signup], email=confirm_data.email, seconds=half_hour)
        response.set_cookie(key=JWTCookie.COOKIE_KEY, value=str(access_token), max_age=half_hour)
        return JSONResponse(dict(message="new user"), status.HTTP_404_NOT_FOUND)


@router.post("/signup", responses={
    200: {"model": schemas.Response}
})
async def complete_registration(
        response: Response,
        complete_data: schemas.SignUp,
        payload: TokenPayload = Depends(JWTCookie())
):
    if Scope.signup not in payload.scope:
        Response(status_code=status.HTTP_403_FORBIDDEN)

    user = models.User(
        username=complete_data.username,
        name=complete_data.name,
        email=payload.email
    )

    async with UnitOfWork() as uow:
        uow.users.add(user)
        await uow.commit()

    week = 60 * 60 * 24 * 7  # 1 неделя
    access_token = Token(scopes=[Scope.primary_user], email=user.email, seconds=week)
    response.set_cookie(key=JWTCookie.COOKIE_KEY, value=str(access_token), max_age=week)
    return JSONResponse(dict(message="user created"), status.HTTP_200_OK)


@router.get("/usernames/available", responses={
    200: {"model": schemas.Response},
    409: {"model": schemas.Response}
}, dependencies=[Depends(JWTCookie())])
async def is_username_available(username: str):
    async with UnitOfWork() as uow:
        if await uow.users.is_username_available(username):
            return JSONResponse(dict(message="username already taken"), status.HTTP_200_OK)
    return JSONResponse(dict(message="username already taken"), status.HTTP_409_CONFLICT)


@router.get(
    "/users/{user_id}",
    status_code=200,
    responses={
        200: {"model": schemas.User},
        404: {"model": schemas.Response}
    }
)
async def get_user(user_id: int):
    async with UnitOfWork() as uow:
        if not (user := await uow.users.get(user_id)):
            return JSONResponse(dict(message="user not found"), status.HTTP_404_NOT_FOUND)
    return schemas.User.from_orm(user)


@router.post(
    "/posts",
    status_code=201,
    # dependencies=[Depends(JWTBearer())]
)
async def publish_post(
        title: str = Form(None),
        description: str = Form(None),
        areas: list[str] = Form(..., media_type="application/json;charset=utf-8"),
        files: list[UploadFile] = File(...)
):
    areas = [schemas.CropArea(**json.loads(area)) for area in areas]

    post = models.Post(user_id=0, title=title, description=description)

    for file, area in zip(files, areas):
        post.pictures.append(models.Picture(
            id=uuid4(),
            size=100,
            height=100,
            width=100,
            format='jpg'
        ))

        image_bytes = await file.read()
        await file.close()

        image_manager = ImageManager(
            image_bytes,
            (area.x, area.y, area.x + area.width, area.y + area.height),
            area.height,
            area.width
        )

        image_manager.save(area.save_original)

    async with UnitOfWork() as uow:
        uow.posts.add(post)
        await uow.commit()


@router.get("/posts", status_code=200)
async def list_posts(
        from_date: datetime | None,
        number: int | None,
) -> list[schemas.Post]:
    async with UnitOfWork() as uow:
        return uow.posts.list(from_date, number)
