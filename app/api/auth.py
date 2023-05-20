from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import Response

from app import schemas
from app.adapters.mailer import MailerProtocol
from app.adapters.security import JWTCookieProtocol, Scope, JWTCookie, TokenPayload
from app.domain import models
from app.service_layer import services
from app.service_layer.unit_of_work import UnitOfWork

router = APIRouter(prefix="/authorization", tags=["Authorization"])


@router.post("/email", status_code=200)
async def authorization_email(
        email_data: schemas.SignInEmail,
        mailer: MailerProtocol = Depends(),
):
    await services.verify_email(email_data.email, mailer, UnitOfWork())
    return schemas.Response(message="code sent")


@router.post("/code", responses={
    200: {"model": schemas.Response},
    401: {"model": schemas.Response},
    404: {"model": schemas.Response}
}, response_model=schemas.Response)
async def authorization_code(
        response: Response,
        data: schemas.SignInCode,
        jwt_cookie: JWTCookieProtocol = Depends()
):
    if not await services.confirm_code(data.code, data.email, UnitOfWork()):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return schemas.Response(message="code does not match")

    async with UnitOfWork() as uow:
        user = await uow.users.get_by_email(data.email)

    if user:
        jwt_cookie.set(response, scopes=[Scope.primary_user], email=data.email, max_age=60 * 60 * 24)
        response.status_code = status.HTTP_200_OK
        return schemas.Response(message="success")

    jwt_cookie.set(response, scopes=[Scope.primary_user], email=data.email, max_age=60 * 30)
    response.status_code = status.HTTP_404_NOT_FOUND
    return schemas.Response(message="new user")


@router.post("/signup", responses={
    200: {"model": schemas.Response}
})
async def signup(
        response: Response,
        data: schemas.SignUp,
        jwt_cookie: JWTCookieProtocol = Depends(),
        payload: TokenPayload = Depends(JWTCookie)
):
    if Scope.signup not in payload.scope:
        response.status_code = status.HTTP_403_FORBIDDEN
        schemas.Response(message="non registration scope")

    user = models.User(
        username=data.username,
        name=data.name,
        email=payload.email
    )

    async with UnitOfWork() as uow:
        uow.users.add(user)
        await uow.commit()

    jwt_cookie.set(response, scopes=[Scope.primary_user], email=user.email, max_age=60 * 60 * 24)
    response.status_code = status.HTTP_200_OK
    return schemas.Response(message="success")
