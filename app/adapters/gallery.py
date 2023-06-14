import io
import os.path
import uuid
from enum import StrEnum, auto
from logging import Logger
from shutil import rmtree
from typing import Self, Optional

from PIL import Image

from app.utils.interface import Interface


class Source(StrEnum):
    original: str = auto()
    optimized: str = auto()


class ImageProcess:
    def __init__(self, raw_image: bytes, base_path: str):
        self.base_path = base_path
        self.raw_image = raw_image
        self.buffer: io.BytesIO | None = None
        self.image: Optional[Image] = None
        self.format: str | None = None
        self.real_height = 0
        self.real_width = 0
        self.size: int = 0

    def __enter__(self):
        self.buffer = io.BytesIO(self.raw_image)
        self.image: Image = Image.open(self.buffer)
        self.format = self.image.format.lower()
        self.real_width, self.real_height = self.image.size
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        self.buffer.close()
        self.image.close()

    @property
    def height(self):
        return self.image.size[1]

    @property
    def width(self):
        return self.image.size[0]

    def convert(self) -> Self:
        self.image = self.image.convert("RGB")
        return self

    def crop(self, box: tuple[int, int, int, int]):
        self.image = self.image.crop(box)
        return self

    def rotate(self, angel: int):
        self.image = self.image.rotate(-angel, expand=True)
        return self

    def resize(self, resolution_limit: int = 1080):
        if self.width > resolution_limit and self.height >= self.height:
            self.image = self.image.resize(
                (resolution_limit, int((self.height / self.width) * resolution_limit)),
                Image.ANTIALIAS
            )
        elif self.height > resolution_limit:
            self.image = self.image.resize(
                (int((self.width / self.height) * resolution_limit), resolution_limit),
                Image.ANTIALIAS
            )
        return self

    def save(self, user_id: int, original: bool = False, fmt: str = 'jpeg') -> uuid.UUID:
        os.makedirs(os.path.join(self.base_path, Source.original, f"{user_id}"), exist_ok=True)
        os.makedirs(os.path.join(self.base_path, Source.optimized, f"{user_id}"), exist_ok=True)
        filename = uuid.uuid4()
        optimized_path = os.path.join(self.base_path, Source.optimized, f"{user_id}", f"{filename}")
        original_path = os.path.join(self.base_path, Source.original, f"{user_id}", f"{filename}")
        self.image.save(
            os.path.join(self.base_path, Source.optimized, f"{user_id}", f"{filename}"),
            format=fmt,
            progressive=True,
            optimize=True,
            quality=70
        )

        if original:
            with open(os.path.join(self.base_path, Source.original, f"{user_id}", f"{filename}"), "wb") as f:
                f.write(self.raw_image)
            self.size = os.stat(original_path).st_size
        else:
            self.real_width, self.real_height = self.image.size
            self.size = os.stat(optimized_path).st_size
            self.format = fmt
            os.link(
                os.path.join(self.base_path, Source.optimized, f"{user_id}", f"{filename}"),
                os.path.join(self.base_path, Source.original, f"{user_id}", f"{filename}")
            )

        return filename


class Gallery:
    def __init__(self, logger: Logger, base_path: str):
        self.logger = logger
        self.logger.info("initialization...")
        self.base_path = os.path.abspath(base_path)
        os.makedirs(os.path.join(self.base_path, Source.original), exist_ok=True)
        os.makedirs(os.path.join(self.base_path, Source.optimized), exist_ok=True)

    def get_path(self, source: Source, user_id: int, picture_id: str, is_avatar: bool = False) -> str:
        path = os.path.abspath(os.path.join(
            self.base_path, source, str(user_id), picture_id
        ))
        if not is_avatar or os.path.exists(path):
            return path
        else:
            return os.path.abspath(os.path.join(
                self.base_path, "0.webp"
            ))

    def delete(self, user_id: int, picture_id: uuid.UUID | None = None):
        for source in Source:
            try:
                if picture_id is None:
                    rmtree(os.path.abspath(os.path.join(
                        self.base_path, source.value, str(user_id)
                    )))
                else:
                    os.remove(os.path.abspath(os.path.join(
                        self.base_path, source.value, str(user_id), str(picture_id)
                    )))
            except FileNotFoundError:
                pass
        return self

    def __call__(self, raw_image: bytes) -> ImageProcess:
        return ImageProcess(raw_image, self.base_path)


class IGallery(Interface, Gallery):
    pass
