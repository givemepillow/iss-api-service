from dataclasses import dataclass


@dataclass
class NewPicture:
    file_bytes: bytes
    crop_box: tuple[int, int, int, int]
    save_original: bool


@dataclass
class NewPost:
    user_id: int
    title: str
    description: str
    pictures: list[NewPicture]
