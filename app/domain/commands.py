import dataclasses


class Command:
    pass


@dataclasses.dataclass
class CreatePost(Command):
    user_id: int
    title: str | None
    description: str | None


@dataclasses.dataclass
class AddImage(Command):
    post_id: int
    original: str


@dataclasses.dataclass
class RegistrateUser(Command):
    username: str
    name: str | None
    password: str
    email: str
