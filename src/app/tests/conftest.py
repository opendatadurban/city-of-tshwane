import logging
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
import warnings
from sqlalchemy.pool import NullPool
from sqlalchemy import exc as sa_exc
from asgi_lifespan import LifespanManager
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.deps import get_db
from app.models.db.base import SQLBase as SQLModel
from app.models.db.users import UserInDb
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import get_superuser_token_headers
from app.core.security import get_password_hash
from sqlalchemy import insert
from app.api.main import api_router

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create a test database engine that persists for the entire test session.

    This fixture:
    - Creates a new SQLAlchemy engine with test settings
    - Drops all existing tables
    - Creates fresh tables for testing
    - Cleans up by dropping all tables and disposing engine after tests

    Yields:
        AsyncEngine: SQLAlchemy async engine instance for test database
    """
    url = settings.SQLALCHEMY_DATABASE_URI.unicode_string()
    engine = create_async_engine(
        url,
        echo=False,  # Disable SQL logging for cleaner test output
        future=True,
        poolclass=NullPool,  # Disable connection pooling for tests
    )

    # Setup fresh database for testing
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

        # insert superuser into db for testing using run_sync
        def create_superuser(conn):

            # Create insert statement
            stmt = insert(UserInDb).values(
                email=settings.FIRST_SUPERUSER,
                is_active=True,
                is_superuser=True,
                full_name="Test Superuser",
                hashed_password=get_password_hash(
                    settings.FIRST_SUPERUSER_PASSWORD
                ),
            )

            # Execute the insert
            conn.execute(stmt)
            conn.commit()

        # Run the superuser creation
        await conn.run_sync(create_superuser)

    yield engine

    # Cleanup database after all tests
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for a single test function.

    This fixture:
    - Creates a new session for each test
    - Sets up nested transactions for test isolation
    - Rolls back changes after each test
    - Handles proper cleanup of transactions and connections

    Args:
        engine: The test database engine fixture

    Yields:
        AsyncSession: SQLAlchemy async session for database operations
    """
    SessionLocal = async_sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        autocommit=False,
    )

    # Filter out SQLAlchemy warnings about nested transactions
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=sa_exc.SAWarning)

        # Create nested transaction context for test isolation
        async with engine.connect() as conn:
            # Start outer transaction
            tsx = await conn.begin()
            try:
                async with SessionLocal(bind=conn) as session:
                    # Create savepoint for nested transaction
                    nested_tsx = await conn.begin_nested()
                    yield session

                    # Rollback to savepoint if transaction is still active
                    if nested_tsx.is_active:
                        await nested_tsx.rollback()

                    # Rollback outer transaction
                    await tsx.rollback()
            finally:
                await tsx.close()

            await conn.close()


@pytest_asyncio.fixture(scope="function")
async def client(session) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an HTTP test client for API testing.

    This fixture:
    - Sets up a FastAPI test application
    - Configures routing and dependencies
    - Creates an async HTTP client for making requests
    - Uses the test session fixture for database operations

    Args:
        session: The database session fixture

    Yields:
        AsyncClient: HTTPX async client configured for testing the API
    """
    # Create test FastAPI application
    app = FastAPI()
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Override database dependency to use test session
    app.dependency_overrides[get_db] = lambda: session

    # Create async HTTP client using ASGI transport
    # Note: We use HTTPX instead of FastAPI's TestClient for async support
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture(scope="function")
async def get_item_owner(session: AsyncSession) -> UserInDb:
    """
    Create a user in the database for testing item ownership.

    Args:
        session: The database session fixture

    Returns:
        UserInDb: The user created for item ownership testing
    """
    user_in = UserInDb(
        email=settings.EMAIL_TEST_USER,
        hashed_password=get_password_hash("SFGASFGASFGH"),
        is_active=True,
        is_superuser=False,
        full_name="Test User",
    )
    session.add(user_in)
    await session.commit()
    await session.refresh(user_in)
    return user_in

@pytest_asyncio.fixture(scope="function")
async def superuser_token_headers(client: AsyncClient) -> dict[str, str]:
    return await get_superuser_token_headers(client)


@pytest_asyncio.fixture(scope="function")
async def normal_user_token_headers(
    client: AsyncClient, session: AsyncSession
) -> dict[str, str]:
    return await authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=session
    )
