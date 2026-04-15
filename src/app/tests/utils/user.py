from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from app.crud.users import CRUDUsers
from app.core.config import settings
from app.models.db.users import UserInDb
from app.models.api.users import UserCreateRequest, UserPatchPasswordRequest
from app.tests.utils.utils import random_email, random_lower_string
from typing import Tuple


async def user_authentication_headers(
    *, client: AsyncClient, email: str, password: str
) -> dict[str, str]:
    data = {"username": email, "password": password}

    r = await client.post(
        f"{settings.API_V1_STR}/login/access-token", data=data
    )
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


async def create_random_user(db: AsyncSession) -> Tuple[UserInDb, str]:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreateRequest(email=email, password=password)
    user = await CRUDUsers.create_user_with_hashed_password(
        session=db, user_in=user_in, password=password
    )
    return user, password


async def authentication_token_from_email(
    *, client: AsyncClient, email: str, db: AsyncSession
) -> dict[str, str]:
    """
    Return a valid token for the user with given email.

    If the user doesn't exist it is created first.
    """
    password = random_lower_string()
    user = await CRUDUsers.get_user_by_email(session=db, email=email)
    if not user:
        user_in = UserCreateRequest(
            email=email, password=password, is_superuser=False, is_active=True
        )
        user = await CRUDUsers.create_user_with_hashed_password(
            session=db, user_in=user_in, password=password
        )
    else:
        user_in_update = UserPatchPasswordRequest(password=password)
        if not user.id:
            raise Exception("User id not set")
        user = await CRUDUsers.update_by_id(
            session=db, data=user_in_update, id_=user.id
        )

    return await user_authentication_headers(
        client=client, email=email, password=password
    )
