from dataclasses import dataclass


@dataclass
class NewPicture:
    file_bytes: bytes
    crop_box: tuple[int, int, int, int]
    rotate: int
    save_original: bool


@dataclass
class NewPost:
    user_id: int
    title: str
    description: str
    aspect_ratio: float
    pictures: list[NewPicture]
