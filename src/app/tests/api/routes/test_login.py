import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
import logging

@pytest.mark.asyncio
class TestLoginRouter():

    async def test_get_access_token(self, client: AsyncClient, session: AsyncSession) -> None:
        login_data = {
            "username": settings.FIRST_SUPERUSER,
            "password": settings.FIRST_SUPERUSER_PASSWORD,
        }
        r = await client.post(
            f"{settings.API_V1_STR}/login/access-token", data=login_data
        )
        tokens = r.json()
        assert r.status_code == 200
        assert "access_token" in tokens
        assert tokens["access_token"]

    async def test_get_access_token_incorrect_password(
        self, client: AsyncClient
    ) -> None:
        login_data = {
            "username": settings.FIRST_SUPERUSER,
            "password": "incorrect",
        }
        r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
        assert r.status_code == 400

    async def test_use_access_token(
        self, client: AsyncClient, superuser_token_headers: dict[str, str]
    ) -> None:
        r = await client.post(
            f"{settings.API_V1_STR}/login/test-token",
            headers=superuser_token_headers,
        )
        result = r.json()
        assert r.status_code == 200
        assert "email" in result


# async def test_recovery_password(
#     client: AsyncClient, normal_user_token_headers: dict[str, str]
# ) -> None:
#     with (
#         patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
#         patch("app.core.config.settings.SMTP_USER", "admin@example.com"),
#     ):
#         email = "test@example.com"
#         r = client.post(
#             f"{settings.API_V1_STR}/password-recovery/{email}",
#             headers=normal_user_token_headers,
#         )
#         assert r.status_code == 200
#         assert r.json() == {"message": "Password recovery email sent"}

# async def test_recovery_password_user_not_exits(
#     client: AsyncClient, normal_user_token_headers: dict[str, str]
# ) -> None:
#     email = "jVgQr@example.com"
#     r = client.post(
#         f"{settings.API_V1_STR}/password-recovery/{email}",
#         headers=normal_user_token_headers,
#     )
#     assert r.status_code == 404

# async def test_reset_password(
#     client: AsyncClient,
#     superuser_token_headers: dict[str, str],
#     session: AsyncSession,
# ) -> None:
#     token = generate_password_reset_token(email=settings.FIRST_SUPERUSER)
#     data = {"new_password": "changethis", "token": token}
#     r = client.post(
#         f"{settings.API_V1_STR}/reset-password/",
#         headers=superuser_token_headers,
#         json=data,
#     )
#     assert r.status_code == 200
#     assert r.json() == {"message": "Password updated successfully"}

#     user_query = select(UserInDb).where(UserInDb.email == settings.FIRST_SUPERUSER)
#     user = session.exec(user_query).first()
#     assert user
#     assert verify_password(data["new_password"], user.hashed_password)

# async def test_reset_password_invalid_token(
#     client: AsyncClient, superuser_token_headers: dict[str, str]
# ) -> None:
#     data = {"new_password": "changethis", "token": "invalid"}
#     r = client.post(
#         f"{settings.API_V1_STR}/reset-password/",
#         headers=superuser_token_headers,
#         json=data,
#     )
#     response = r.json()

#     assert "detail" in response
#     assert r.status_code == 400
#     assert response["detail"] == "Invalid token"
