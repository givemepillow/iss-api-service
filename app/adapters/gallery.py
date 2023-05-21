import io
import os.path
import shutil
import uuid
from enum import StrEnum, auto
from logging import Logger
from typing import Protocol
from uuid import UUID

from PIL import Image


class Source(StrEnum):
    original: str = auto()
    optimized: str = auto()


class ImageProcess:
    def __init__(self, raw_image: bytes, original_path: str, optimized_path: str):
        self.raw_image = raw_image
        self.buffer: io.BytesIO | None = None
        self.image: Image | None = None
        self.format: str | None = None
        self.original_path = original_path
        self.optimized_path = optimized_path

    def __enter__(self):
        self.buffer = io.BytesIO(self.raw_image)
        self.image = Image.open(self.buffer)
        self.format = self.image.format.lower()
        self.width, self.height = self.image.size
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.buffer.close()
        self.image.close()

    @property
    def size(self) -> int:
        return len(self.raw_image)

    def convert(self):
        self.image = self.image.convert("RGB")

    def crop(self, box: tuple[int, int, int, int]):
        self.image = self.image.crop(box)

    def resize(self, resolution_limit: int = 1920):
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

    def save(self, save_original: bool) -> UUID:
        filename = uuid.uuid4()
        self.image.save(
            os.path.join(self.optimized_path, f'{filename}'), 'jpeg',
            optimize=True, quality=95
        )

        if save_original:
            with open(os.path.join(self.original_path, f"{filename}"), "wb") as f:
                f.write(self.raw_image)
        else:
            os.link(
                os.path.join(self.optimized_path, f'{filename}'),
                os.path.join(self.original_path, f"{filename}")
            )

        return filename


class GalleryProtocol(Protocol):
    def __init__(self): pass

    def __call__(self, raw_image: bytes, user_id: str) -> ImageProcess:
        raise NotImplementedError

    def path(self, source: Source, user_id: str, picture_id: str) -> str:
        raise NotImplementedError

    def delete(self, user_id: str, picture_id: str):
        raise NotImplementedError


class Gallery:
    def __init__(self, logger: Logger, base_path: str):
        self.logger = logger
        self.logger.info("initialization...")
        self.base_path = os.path.abspath(base_path)
        os.makedirs(os.path.join(self.base_path, Source.original), exist_ok=True)
        os.makedirs(os.path.join(self.base_path, Source.optimized), exist_ok=True)

    def path(self, source: Source, user_id: str, picture_id: str) -> str:
        return os.path.abspath(os.path.join(
            self.base_path, source, user_id, picture_id
        ))

    def delete(self, user_id: str, picture_id: str):
        for source in Source:
            shutil.rmtree(os.path.abspath(os.path.join(
                self.base_path, source, user_id, picture_id
            )))

    def __call__(self, raw_image: bytes, user_id: str) -> ImageProcess:
        original_path = os.path.abspath(os.path.join(
            self.base_path, Source.original, user_id
        ))
        optimized_path = os.path.abspath(os.path.join(
            self.base_path, Source.optimized, user_id
        ))
        os.makedirs(original_path, exist_ok=True)
        os.makedirs(optimized_path, exist_ok=True)

        return ImageProcess(raw_image, original_path, optimized_path)
