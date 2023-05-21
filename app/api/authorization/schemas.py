from pydantic import BaseModel, EmailStr, Field


class SignInEmail(BaseModel):
    email: EmailStr


class SignInCode(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=4)


class SignUp(BaseModel):
    username: str = Field(min_length=3, max_length=25)
    name: str | None
