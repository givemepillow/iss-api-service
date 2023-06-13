import hashlib
import hmac

from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import Response

from app.api.authorization import schemas
from app.adapters.mailer import IMailer
from app.adapters.security import Scope, TokenPayload, JWTCookieBearer, IJWTCookie
from app.api.schemas import ResponseSchema
from app.utils.config import Settings, Config
from app.domain import models
from app.service_layer import services
from app.service_layer.unit_of_work import UnitOfWork

router = APIRouter(prefix="/authorization", tags=["Authorization"])


@router.post(
    path="/email",
    status_code=status.HTTP_200_OK,
    response_model=ResponseSchema,
    summary="Войти через электронную почту."
)
async def authorization_email(
        email_data: schemas.SignInEmail,
        mailer: IMailer = Depends()
):
    await services.verify_email(email_data.email, mailer)
    return ResponseSchema(detail="code sent")


@router.post(
    path="/code",
    responses={
        status.HTTP_200_OK: {"model": schemas.SignInSuccess},
        status.HTTP_401_UNAUTHORIZED: {"model": ResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": ResponseSchema}
    },
    summary="Отправить код подтверждения."
)
async def authorization_code(
        response: Response,
        data: schemas.SignInCode,
        jwt_cookie: IJWTCookie = Depends()
):
    if not await services.confirm_code(data.code, data.email):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ResponseSchema(detail="Ошибка! Неверный код подтверждения.")

    async with UnitOfWork() as uow:
        user = await uow.users.get_by_email(data.email)
        await uow.commit()

    response.status_code = status.HTTP_200_OK
    if user:
        jwt_cookie.set(
            response,
            scopes=[Scope.primary_user],
            email=data.email,
            max_age=60 * 60 * 24,
            user_id=user.id,
            telegram_id=user.telegram_id
        )
        return schemas.SignInSuccess(user_exists=True)

    jwt_cookie.set(
        response,
        scopes=[Scope.signup],
        email=data.email,
        max_age=60 * 10,
        user_id=None,
        telegram_id=None
    )
    return schemas.SignInSuccess(user_exists=False)


@router.post(
    path="/telegram",
    responses={
        status.HTTP_200_OK: {"model": schemas.SignInSuccess},
        status.HTTP_401_UNAUTHORIZED: {"model": ResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": ResponseSchema}
    },
    summary="Войти через Telegram."
)
async def authorization_telegram(
        response: Response,
        telegram_data: schemas.SignInTelegram,
        jwt_cookie: IJWTCookie = Depends(),
        config: Settings = Depends(Config)
):
    data_check = telegram_data.dict(exclude_unset=True, exclude_none=True)
    hash_string = data_check["hash"]
    del data_check["hash"]
    data_check_string = '\n'.join([
        f"{k}={v}" for k, v in sorted(data_check.items(), key=lambda x: x[0])
    ])
    signature = hmac.new(
        hashlib.sha256(config.telegram.token.encode()).digest(),
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()

    if signature != hash_string:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ResponseSchema(detail="Ошибка! Не удалось подтвердить аккаунт.")

    async with UnitOfWork() as uow:
        user = await uow.users.get_by_telegram_id(telegram_data.id)
        await uow.commit()

    response.status_code = status.HTTP_200_OK

    if user:
        jwt_cookie.set(
            response,
            scopes=[Scope.primary_user],
            email=user.email,
            max_age=60 * 60 * 24,
            user_id=user.id,
            telegram_id=user.telegram_id
        )
        return schemas.SignInSuccess(user_exists=True)

    jwt_cookie.set(
        response,
        scopes=[Scope.signup],
        email=None,
        max_age=60 * 10,
        user_id=None,
        telegram_id=telegram_data.id
    )
    return schemas.SignInSuccess(user_exists=False)


@router.post(
    path="/signup",
    responses={
        status.HTTP_200_OK: {"model": ResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": ResponseSchema}
    },
    summary="Зарегистрироваться."
)
async def signup(
        response: Response,
        data: schemas.SignUp,
        jwt_cookie: IJWTCookie = Depends(),
        payload: TokenPayload = Depends(JWTCookieBearer)
):
    user = models.User(
        username=data.username,
        name=data.name,
        email=payload.email,
        telegram_id=payload.telegram_id
    )

    async with UnitOfWork() as uow:
        uow.users.add(user)
        await uow.commit()

    jwt_cookie.set(
        response,
        scopes=[Scope.primary_user],
        user_id=user.id,
        email=user.email,
        telegram_id=payload.telegram_id,
        max_age=60 * 60 * 24,
    )
    response.status_code = status.HTTP_200_OK
    return ResponseSchema(detail="Регистрация завешена.")


@router.post(
    path="/logout",
    responses={
        status.HTTP_200_OK: {"model": ResponseSchema},
        status.HTTP_401_UNAUTHORIZED: {"model": ResponseSchema},
        status.HTTP_403_FORBIDDEN: {"model": ResponseSchema}
    },
    dependencies=[Depends(JWTCookieBearer)],
    summary="Выйти из системы."
)
async def authorization_logout(r: Response, jwt_cookie: IJWTCookie = Depends()):
    jwt_cookie.remove(r)
    r.status_code = status.HTTP_403_FORBIDDEN
    return ResponseSchema(detail="Выход из системы выполнен успешно.")
