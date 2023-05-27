import datetime
from random import randint
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from app.adapters.gallery import GalleryProtocol
from app.adapters.mailer import MailerProtocol
from app.domain import models
from app.service_layer.dto import NewPost
from app.service_layer.unit_of_work import UnitOfWork


async def publish_post(new_post: NewPost, gallery: GalleryProtocol):
    post = models.Post(
        user_id=new_post.user_id,
        title=new_post.title,
        description=new_post.description,
        aspect_ratio=new_post.aspect_ratio,
        pictures=[]
    )

    for p in new_post.pictures:
        with gallery(p.file_bytes, str(new_post.user_id)) as im:
            im.rotate(p.rotate)
            im.convert()
            im.crop(p.crop_box)
            im.resize()
            picture_id = im.save(p.save_original)
            post.pictures.append(models.Picture(
                id=picture_id,
                format=im.format,
                height=im.height,
                width=im.width,
                size=im.size
            ))

    async with UnitOfWork() as uow:
        uow.posts.add(post)
        await uow.commit()


async def confirm_code(code: str, email: str):
    async with UnitOfWork() as uow:
        verify_code = await uow.verify_codes.get(email)
        if not verify_code:
            return False

        if verify_code.expire_at < datetime.datetime.now(datetime.timezone.utc):
            await uow.verify_codes.delete(email)
            return False

        if code != verify_code.code and verify_code.attempts > 1:
            verify_code.attempts -= 1
            return False

        if code != verify_code.code and verify_code.attempts <= 1:
            await uow.verify_codes.delete(email)
            return False

        await uow.verify_codes.delete(email)
    return True


async def verify_email(email: str, mailer: MailerProtocol):
    code = f"{randint(0, 9999):04d}"
    subject = "Код подтверждения."
    content = f"{code} — ваш код для авторизации на givemepillow.ru."

    await mailer.send(subject, content, email)

    async with UnitOfWork() as uow:
        await uow.verify_codes.add(models.VerifyCode(
            email=email,
            code=code,
            expire_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=120)
        ))
        await uow.commit()


async def registrate_user(code: str):
    pass
