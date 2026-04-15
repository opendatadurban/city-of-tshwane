import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.crud.users import CRUDUsers
from app.models.api.users import UserCreateRequest


# Test data fixtures
@pytest.fixture
def user_create_request() -> UserCreateRequest:
    return UserCreateRequest(
        email="test@example.com",
        is_active=True,
        is_superuser=False,
        full_name="Test User",
        password="testpassword123",
    )


@pytest.mark.asyncio
class TestCRUDUsers:

    async def test_create_user_with_hashed_password(
        self, session: AsyncSession, user_create_request: UserCreateRequest
    ):
        password = "testpassword123"
        user = await CRUDUsers.create_user_with_hashed_password(
            session=session,
            user_in=user_create_request,
            password=password,
        )

        assert user.email == user_create_request.email
        assert user.full_name == user_create_request.full_name
        assert user.is_active == user_create_request.is_active
        assert user.is_superuser == user_create_request.is_superuser
        assert verify_password(password, user.hashed_password)

    async def test_get_user_hashed_password(
        self, session: AsyncSession, user_create_request: UserCreateRequest
    ):
        password = "testpassword123"
        user = await CRUDUsers.create_user_with_hashed_password(
            session=session,
            user_in=user_create_request,
            password=password,
        )

        hashed_password = await CRUDUsers.get_user_hashed_password(
            session=session, user_id=str(user.id)
        )

        assert hashed_password == user.hashed_password

    async def test_update_user_password(
        self, session: AsyncSession, user_create_request: UserCreateRequest
    ):
        old_password = "oldpassword123"
        new_password = "newpassword123"

        user = await CRUDUsers.create_user_with_hashed_password(
            session=session,
            user_in=user_create_request,
            password=old_password,
        )

        result = await CRUDUsers.update_user_password(
            session=session, current_user=user, new_password=new_password
        )

        assert result is True
        assert verify_password(new_password, user.hashed_password)
        assert not verify_password(old_password, user.hashed_password)

    async def test_get_user_by_email(
        self, session: AsyncSession, user_create_request: UserCreateRequest
    ):
        user = await CRUDUsers.create_user_with_hashed_password(
            session=session,
            user_in=user_create_request,
            password="testpassword123",
        )

        retrieved_user = await CRUDUsers.get_user_by_email(
            session=session, email=user.email
        )

        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        assert retrieved_user.email == user.email

    async def test_authenticate_success(
        self, session: AsyncSession, user_create_request: UserCreateRequest
    ):
        password = "testpassword123"
        user = await CRUDUsers.create_user_with_hashed_password(
            session=session,
            user_in=user_create_request,
            password=password,
        )

        authenticated_user = await CRUDUsers.authenticate(
            session=session, email=user.email, password=password
        )

        assert authenticated_user is not None
        assert authenticated_user.id == user.id

    async def test_authenticate_wrong_password(
        self, session: AsyncSession, user_create_request: UserCreateRequest
    ):
        password = "testpassword123"
        user = await CRUDUsers.create_user_with_hashed_password(
            session=session,
            user_in=user_create_request,
            password=password,
        )

        authenticated_user = await CRUDUsers.authenticate(
            session=session, email=user.email, password="wrongpassword"
        )

        assert authenticated_user is None

    async def test_authenticate_nonexistent_user(
        self,
        session: AsyncSession,
    ):
        authenticated_user = await CRUDUsers.authenticate(
            session=session,
            email="nonexistent@example.com",
            password="testpassword123",
        )

        assert authenticated_user is None
