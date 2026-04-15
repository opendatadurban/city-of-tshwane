import contextlib
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor

from app.crud import CRUDUsers
from app.models.db import UserInDb
from app.core.config import settings
from app.core.security import get_password_hash

# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


class DatabaseSessionManager:
    """
    Manages async database sessions and connections for SQLAlchemy.

    This class provides a centralized way to manage database engine initialization,
    session creation, and connection handling for asynchronous SQLAlchemy operations.
    It ensures proper resource cleanup and implements context managers for safe
    database interactions.

    Attributes:
        _engine (AsyncEngine | None): The SQLAlchemy async engine instance.
        _sessionmaker (async_sessionmaker | None): The async session factory.
    """
    def __init__(self):
        """
        Initialize an AsyncDbSessionManager instance.

        The manager starts with no engine or sessionmaker configured.
        Call init() to set up the database connection.
        """
        self._engine: AsyncEngine | None = None
        self._sessionmaker: async_sessionmaker | None = None

    def init(self, host: str):
        """
        Initialize the database engine and session maker.

        Args:
            host (str): The database connection string.

        Note:
            This method must be called before any database operations can be performed.
            It sets up both the engine and the session maker with default configurations.
        """
        self._engine = create_async_engine(host)
        self._sessionmaker = async_sessionmaker(autocommit=False, bind=self._engine)
        SQLAlchemyInstrumentor().instrument(
            engine=self._engine.sync_engine,
            enable_commenter=True,
            commenter_options={},
        )
        AsyncPGInstrumentor().instrument()

    async def close(self):
        """
        Close the database engine and clean up resources.

        Raises:
            Exception: If the manager hasn't been initialized before calling close().

        Note:
            This method should be called during application shutdown to ensure
            proper cleanup of database resources.
        """
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        """
        Create a database connection context.

        Yields:
            AsyncConnection: An async database connection with transaction management.

        Raises:
            Exception: If the manager hasn't been initialized.

        Note:
            This context manager automatically handles transaction commit/rollback.
            If an exception occurs, the transaction is rolled back automatically.

        Example:
            async with session_manager.connect() as conn:
                await conn.execute(query)
        """
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """
        Create a database session context.

        Yields:
            AsyncSession: An async SQLAlchemy session.

        Raises:
            Exception: If the manager hasn't been initialized.

        Note:
            This context manager handles session lifecycle including:
            - Automatic session closure
            - Transaction rollback on exceptions
            - Resource cleanup

        Example:
            async with session_manager.session() as session:
                result = await session.execute(query)
        """
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def add_first_superuser(session: AsyncSession) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    user = await CRUDUsers.get_user_by_email(
        session=session, email=settings.FIRST_SUPERUSER
    )

    if not user:

        new_user = UserInDb(
            email=settings.FIRST_SUPERUSER,
            hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            is_active=True,
            is_superuser=True,
            full_name="Admin User",
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

# Global session manager instance
sessionmanager = DatabaseSessionManager()
