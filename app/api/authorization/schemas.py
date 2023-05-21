from pydantic import BaseModel, EmailStr, Field


class SignInEmail(BaseModel):
    email: EmailStr


class SignInCode(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=4)


class SignInTelegram(BaseModel):
    id: int
    first_name: str
    auth_date: int
    hash: str
    photo_url: str = ""
    last_name: str = ""
    username: str = ""


class SignInSuccess(BaseModel):
    user_exists: bool = Field(alias="userExists")

    class Config:
        allow_population_by_field_name = True


class SignUp(BaseModel):
    username: str = Field(min_length=3, max_length=25)
    name: str | None
