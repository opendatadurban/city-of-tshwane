import logging
from typing import Annotated, AsyncGenerator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.core.db import sessionmanager
from app.models.db.users import UserInDb
from app.models.api.generic import TokenPayload
from app.crud import CRUDUsers
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create and yield a database session.

    This dependency function creates an async database session using
    the session manager and yields it for use in FastAPI endpoints.
    The session is automatically closed when the request is complete.

    Yields:
        AsyncSession: An async SQLAlchemy session for database operations.

    Example:
        @app.get("/items")
        async def get_items(db: Annotated[AsyncSession, Depends(get_db)]):
            # Use db session here
            pass
    """
    logging.debug(sessionmanager._engine.pool.status())
    async with sessionmanager.session() as session:
        yield session
    logging.debug(sessionmanager._engine.pool.status())


SessionDep = Annotated[AsyncSession, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


async def get_current_user(session: SessionDep, token: TokenDep) -> UserInDb:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = await CRUDUsers.get_one_by_id(session=session, id_=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

CurrentUser = Annotated[UserInDb, Depends(get_current_user)]


async def get_current_active_superuser(current_user: CurrentUser) -> UserInDb:

    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
