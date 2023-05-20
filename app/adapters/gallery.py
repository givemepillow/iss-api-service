import io
import os.path
from logging import Logger
from typing import Protocol

from PIL import Image


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

    def save(self, filename: str, save_original: bool):
        if save_original:
            with open(os.path.join(self.original_path, f"{filename}.{self.format}"), "wb") as f:
                f.write(self.raw_image)

        self.image.save(
            os.path.join(self.optimized_path, f'{filename}.jpeg'), 'jpeg',
            optimize=True, quality=95
        )


class GalleryProtocol(Protocol):
    def __init__(self): pass

    def __call__(self, raw_image: bytes, user_id: int) -> ImageProcess:
        raise NotImplementedError


class Gallery:
    def __init__(self, logger: Logger, original_path: str, optimized_path: str):
        self.logger = logger
        self.logger.info("initialization...")
        self.original_path = os.path.abspath(original_path)
        self.optimized_path = os.path.abspath(optimized_path)
        if not os.path.exists(self.original_path):
            os.makedirs(self.original_path, exist_ok=True)
        if not os.path.exists(self.optimized_path):
            os.makedirs(self.optimized_path, exist_ok=True)

    def __call__(self, raw_image: bytes, user_id: int) -> ImageProcess:
        original_path = os.path.join(self.original_path, str(user_id))
        optimized_path = os.path.join(self.optimized_path, str(user_id))
        if not os.path.exists(original_path):
            os.makedirs(original_path, exist_ok=True)

        if not os.path.exists(optimized_path):
            os.makedirs(optimized_path, exist_ok=True)

        return ImageProcess(raw_image, original_path, optimized_path)
