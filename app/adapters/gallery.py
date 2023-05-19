import io
import uuid

from PIL import Image


class ImageManager:  # TODO: DI конфига и мб файловой системы.
    def __init__(self, image_bytes, crop_box: tuple[int, int, int, int], height: int, width: int):
        self.image_bytes = image_bytes
        self.crop_box = crop_box
        self.filename = uuid.uuid4().hex
        self.height = height
        self.width = width

    def save(self, save_original: bool):
        with io.BytesIO(self.image_bytes) as buffer:
            image = Image.open(buffer)
            ext = image.format.lower()
            if save_original:
                with open(f"pictures/original/{self.filename}.{ext}", "wb") as f:
                    f.write(self.image_bytes)

            cropped_image = self._crop(image)
            self._save_small(cropped_image)
            self._save_large(cropped_image)

        cropped_image.close()
        image.close()

    def _crop(self, image: Image):
        converted_image = image.convert("RGB")
        return converted_image.crop(self.crop_box)

    def _save_small(self, small_image: Image):
        if self.width > 1080 and self.height >= self.height:
            small_image = small_image.resize((1080, int((self.height / self.width) * 1080)), Image.ANTIALIAS)
        elif self.height > 1080:
            small_image = small_image.resize((int((self.width / self.height) * 1080), 1080), Image.ANTIALIAS)

        small_image.save(
            f"pictures/small/{self.filename}.jpg", 'jpeg',
            optimize=True, quality=90
        )
        small_image.close()

    def _save_large(self, large_image: Image):
        if self.width > 1920 and self.height >= self.height:
            large_image = large_image.resize((1920, int((self.height / self.width) * 1920)), Image.ANTIALIAS)
        elif self.height > 1920:
            large_image = large_image.resize((int((self.width / self.height) * 1920), 1920), Image.ANTIALIAS)

        large_image.save(
            f"pictures/large/{self.filename}.jpg", 'jpeg',
            optimize=True, quality=90
        )
        large_image.close()
