from pydantic import BaseModel as PydanticBaseModel, Field, EmailStr
import uuid


class UserRequestBase(PydanticBaseModel):
    email: EmailStr = Field(max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class UserResponseBase(UserRequestBase):
    id: uuid.UUID


class UserCreateRequest(UserRequestBase):
    password: str
    re_password: str


class UserCreateResponse(UserResponseBase):
    pass


class UserGetResponse(UserResponseBase):
    pass


class UsersGetResponse(PydanticBaseModel):
    users: list[UserGetResponse]
    count: int


class UserPatchRequest(PydanticBaseModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = True
    is_superuser: bool | None = False
    full_name: str | None = Field(default=None, max_length=255)


class UserPatchPasswordRequest(PydanticBaseModel):
    current_password: str
    new_password: str

class UserPatchResetPasswordRequest(PydanticBaseModel):
    token: str
    new_password: str
    re_new_password: str

class UserPatchResponse(UserResponseBase):
    pass
