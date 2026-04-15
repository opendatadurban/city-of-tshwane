import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.crud import CRUDUsers
from app.core.config import settings
from app.core.security import verify_password
from app.tests.utils.utils import random_email, random_lower_string
from app.tests.utils.user import create_random_user


@pytest.mark.asyncio
class TestUser:

    async def test_get_users_superuser_me(
        self, client: AsyncClient, superuser_token_headers: dict[str, str]
    ) -> None:
        r = await client.get(
            f"{settings.API_V1_STR}/users/me", headers=superuser_token_headers
        )
        current_user = r.json()
        assert current_user
        assert current_user["is_active"] is True
        assert current_user["is_superuser"]
        assert current_user["email"] == settings.FIRST_SUPERUSER

    async def test_get_users_normal_user_me(
        self, client: AsyncClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        r = await client.get(
            f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers
        )
        current_user = r.json()
        assert current_user
        assert current_user["is_active"] is True
        assert current_user["is_superuser"] is False
        assert current_user["email"] == settings.EMAIL_TEST_USER

    async def test_get_existing_user(
        self,
        client: AsyncClient,
        superuser_token_headers: dict[str, str],
        session: AsyncSession,
    ) -> None:
        random_user, password = await create_random_user(session)
        user_id = random_user.id
        r = await client.get(
            f"{settings.API_V1_STR}/users/{user_id}",
            headers=superuser_token_headers,
        )
        assert 200 <= r.status_code < 300
        api_user = r.json()
        existing_user = await CRUDUsers.get_user_by_email(
            session=session, email=random_user.email
        )
        assert existing_user
        assert existing_user.email == api_user["email"]

    async def test_get_existing_user_current_user(
        self,
        client: AsyncClient,
        session: AsyncSession,
    ) -> None:
        random_user, password = await create_random_user(session)
        user_id = random_user.id

        login_data = {
            "username": random_user.email,
            "password": password,
        }
        r = await client.post(
            f"{settings.API_V1_STR}/login/access-token", data=login_data
        )
        tokens = r.json()
        a_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {a_token}"}

        r = await client.get(
            f"{settings.API_V1_STR}/users/{user_id}",
            headers=headers,
        )
        assert 200 <= r.status_code < 300
        api_user = r.json()
        existing_user = await CRUDUsers.get_user_by_email(
            session=session, email=random_user.email
        )
        assert existing_user
        assert existing_user.email == api_user["email"]

    async def test_get_existing_user_permissions_error(
        self, client: AsyncClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        r = await client.get(
            f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 403
        assert r.json() == {"detail": "The user doesn't have enough privileges"}

    async def test_retrieve_users(
        self,
        client: AsyncClient,
        superuser_token_headers: dict[str, str],
        session: AsyncSession,
    ) -> None:
        random_user_1, password_1 = await create_random_user(session)
        random_user_2, password_2 = await create_random_user(session)

        r = await client.get(
            f"{settings.API_V1_STR}/users/", headers=superuser_token_headers
        )
        all_users = r.json()

        assert len(all_users["users"]) > 1
        assert "count" in all_users
        for item in all_users["users"]:
            assert "email" in item

    async def test_update_user_me(
        self,
        client: AsyncClient,
        normal_user_token_headers: dict[str, str],
        session: AsyncSession,
    ) -> None:
        full_name = "Updated Name"
        email = settings.EMAIL_TEST_USER
        data = {"full_name": full_name, "email": settings.EMAIL_TEST_USER}
        r = await client.patch(
            f"{settings.API_V1_STR}/users/me",
            headers=normal_user_token_headers,
            json=data,
        )
        assert r.status_code == 200
        updated_user = r.json()
        assert updated_user["message"] == "User updated successfully"

        user_db = await CRUDUsers.get_user_by_email(
            session=session, email=email
        )
        assert user_db
        assert user_db.email == email
        assert user_db.full_name == full_name

    async def test_update_password_me(
        self,
        client: AsyncClient,
        superuser_token_headers: dict[str, str],
        session: AsyncSession,
    ) -> None:
        new_password = random_lower_string()
        data = {
            "current_password": settings.FIRST_SUPERUSER_PASSWORD,
            "new_password": new_password,
        }
        r = await client.patch(
            f"{settings.API_V1_STR}/users/me/password",
            headers=superuser_token_headers,
            json=data,
        )
        assert r.status_code == 200
        updated_user = r.json()
        assert updated_user["message"] == "Password updated successfully"

        user_db = await CRUDUsers.get_user_by_email(
            session=session, email=settings.FIRST_SUPERUSER
        )
        assert user_db
        assert user_db.email == settings.FIRST_SUPERUSER
        assert verify_password(new_password, user_db.hashed_password)

        # Revert to the old password to keep consistency in test
        old_data = {
            "current_password": new_password,
            "new_password": settings.FIRST_SUPERUSER_PASSWORD,
        }
        r = await client.patch(
            f"{settings.API_V1_STR}/users/me/password",
            headers=superuser_token_headers,
            json=old_data,
        )
        await session.refresh(user_db)

        assert r.status_code == 200
        assert verify_password(
            settings.FIRST_SUPERUSER_PASSWORD, user_db.hashed_password
        )

    async def test_update_password_me_incorrect_password(
        self, client: AsyncClient, superuser_token_headers: dict[str, str]
    ) -> None:
        new_password = random_lower_string()
        data = {"current_password": new_password, "new_password": new_password}
        r = await client.patch(
            f"{settings.API_V1_STR}/users/me/password",
            headers=superuser_token_headers,
            json=data,
        )
        assert r.status_code == 400
        updated_user = r.json()
        assert updated_user["detail"] == "Incorrect password"

    async def test_update_user_me_email_exists(
        self,
        client: AsyncClient,
        normal_user_token_headers: dict[str, str],
        session: AsyncSession,
    ) -> None:

        data = {"email": settings.FIRST_SUPERUSER}
        r = await client.patch(
            f"{settings.API_V1_STR}/users/me",
            headers=normal_user_token_headers,
            json=data,
        )
        assert r.status_code == 409
        assert r.json()["detail"] == "User with this email already exists"

    async def test_update_password_me_same_password_error(
        self, client: AsyncClient, superuser_token_headers: dict[str, str]
    ) -> None:
        data = {
            "current_password": settings.FIRST_SUPERUSER_PASSWORD,
            "new_password": settings.FIRST_SUPERUSER_PASSWORD,
        }
        r = await client.patch(
            f"{settings.API_V1_STR}/users/me/password",
            headers=superuser_token_headers,
            json=data,
        )
        assert r.status_code == 400
        updated_user = r.json()
        assert (
            updated_user["detail"]
            == "New password cannot be the same as the current one"
        )

    async def test_register_user(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        username = random_email()
        password = random_lower_string()
        full_name = random_lower_string()
        data = {"email": username, "password": password, "full_name": full_name}
        r = await client.post(
            f"{settings.API_V1_STR}/users/signup",
            json=data,
        )
        assert r.status_code == 201
        created_user = r.json()
        assert created_user["email"] == username
        assert created_user["full_name"] == full_name

        user_db = await CRUDUsers.get_user_by_email(
            session=session, email=username
        )
        assert user_db
        assert user_db.email == username
        assert user_db.full_name == full_name
        assert verify_password(password, user_db.hashed_password)

    async def test_register_user_already_exists_error(
        self, client: AsyncClient
    ) -> None:
        password = random_lower_string()
        full_name = random_lower_string()
        data = {
            "email": settings.FIRST_SUPERUSER,
            "password": password,
            "full_name": full_name,
        }
        r = await client.post(
            f"{settings.API_V1_STR}/users/signup",
            json=data,
        )
        assert r.status_code == 400
        assert (
            r.json()["detail"]
            == "The user with this email already exists in the system"
        )

    async def test_update_user(
        self,
        client: AsyncClient,
        superuser_token_headers: dict[str, str],
        session: AsyncSession,
    ) -> None:
        random_user, password = await create_random_user(session)

        data = {"full_name": "Updated_full_name"}
        r = await client.patch(
            f"{settings.API_V1_STR}/users/{random_user.id}",
            headers=superuser_token_headers,
            json=data,
        )
        assert r.status_code == 200
        updated_user = r.json()

        assert updated_user["full_name"] == "Updated_full_name"

        user_db = await CRUDUsers.get_user_by_email(
            session=session, email=random_user.email
        )
        await session.refresh(user_db)
        assert user_db
        assert user_db.full_name == "Updated_full_name"

    async def test_update_user_not_exists(
        self, client: AsyncClient, superuser_token_headers: dict[str, str]
    ) -> None:
        data = {"full_name": "Updated_full_name"}
        r = await client.patch(
            f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
            headers=superuser_token_headers,
            json=data,
        )
        assert r.status_code == 404
        assert (
            r.json()["detail"]
            == "The user with this id does not exist in the system"
        )

    async def test_update_user_email_exists(
        self,
        client: AsyncClient,
        superuser_token_headers: dict[str, str],
        session: AsyncSession,
    ) -> None:
        random_user_1, password_1 = await create_random_user(session)
        random_user_2, password_2 = await create_random_user(session)

        data = {"email": random_user_2.email}
        r = await client.patch(
            f"{settings.API_V1_STR}/users/{random_user_1.id}",
            headers=superuser_token_headers,
            json=data,
        )
        assert r.status_code == 409
        assert r.json()["detail"] == "User with this email already exists"

    async def test_delete_user_me(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        random_user, password = await create_random_user(session)
        user_id = random_user.id

        login_data = {
            "username": random_user.email,
            "password": password,
        }
        r = await client.post(
            f"{settings.API_V1_STR}/login/access-token", data=login_data
        )
        tokens = r.json()
        a_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {a_token}"}

        r = await client.delete(
            f"{settings.API_V1_STR}/users/me",
            headers=headers,
        )
        assert r.status_code == 204
        result = await CRUDUsers.get_one_by_id(session=session, id_=user_id)
        assert result is None

    async def test_delete_user_me_as_superuser(
        self, client: AsyncClient, superuser_token_headers: dict[str, str]
    ) -> None:
        r = await client.delete(
            f"{settings.API_V1_STR}/users/me",
            headers=superuser_token_headers,
        )
        assert r.status_code == 403
        response = r.json()
        assert (
            response["detail"]
            == "Super users are not allowed to delete themselves"
        )

    async def test_delete_user_super_user(
        self,
        client: AsyncClient,
        superuser_token_headers: dict[str, str],
        session: AsyncSession,
    ) -> None:
        random_user, password = await create_random_user(session)
        user_id = random_user.id
        r = await client.delete(
            f"{settings.API_V1_STR}/users/{user_id}",
            headers=superuser_token_headers,
        )
        assert r.status_code == 200
        deleted_user = r.json()
        assert deleted_user["message"] == "User deleted successfully"
        result = await CRUDUsers.get_one_by_id(session=session, id_=user_id)
        assert result is None

    async def test_delete_user_not_found(
        self, client: AsyncClient, superuser_token_headers: dict[str, str]
    ) -> None:
        r = await client.delete(
            f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
            headers=superuser_token_headers,
        )
        assert r.status_code == 404
        assert r.json()["detail"] == "User not found"

    async def test_delete_user_current_super_user_error(
        self,
        client: AsyncClient,
        superuser_token_headers: dict[str, str],
        session: AsyncSession,
    ) -> None:
        super_user = await CRUDUsers.get_user_by_email(
            session=session, email=settings.FIRST_SUPERUSER
        )
        assert super_user
        user_id = super_user.id

        r = await client.delete(
            f"{settings.API_V1_STR}/users/{user_id}",
            headers=superuser_token_headers,
        )
        assert r.status_code == 403
        assert (
            r.json()["detail"]
            == "Super users are not allowed to delete themselves"
        )

    async def test_delete_user_without_privileges(
        self,
        client: AsyncClient,
        normal_user_token_headers: dict[str, str],
        session: AsyncSession,
    ) -> None:
        random_user, password = await create_random_user(session)
        r = await client.delete(
            f"{settings.API_V1_STR}/users/{random_user.id}",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 403
        assert r.json()["detail"] == "The user doesn't have enough privileges"
