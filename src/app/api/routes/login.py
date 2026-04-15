from datetime import timedelta, datetime
import logging
from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.crud.users import CRUDUsers
from app.api.deps import CurrentUser, SessionDep
from app.core import security
from app.core.config import settings
from app.models.api.generic import Token
from app.models.api.users import UserGetResponse

router = APIRouter(tags=["login"])

@router.post("/login/access-token")
async def login_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
) -> Token:
    """## Generate OAuth2 compatible access token for authentication.

    **Request Body** (form-data):
    - username (str): User's email address
    - password (str): User's password

    **Returns**:
    - access_token (str): JWT access token
    - token_type (str): Token type (always "bearer")

    **Raises**:
    - HTTPException: 400 if email/password combination is incorrect
    - HTTPException: 400 if user account is inactive

    **Notes**:
    - Token expires after the configured ACCESS_TOKEN_EXPIRE_MINUTES
    - Uses standard OAuth2 password flow
    - Username field expects the user's email address

    **Permissions**:
    - No authentication required
    """

    user = await CRUDUsers.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=400, detail="Incorrect email or password"
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    token = Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )
    return token

@router.post("/login/test-token", response_model=UserGetResponse)
async def test_token(current_user: CurrentUser) -> Any:
    """## Validate access token and retrieve current user information.

    **Returns**:
    - id (UUID): User unique identifier
    - email (str): User email address
    - is_active (bool): User active status
    - is_superuser (bool): User superuser status
    - full_name (str): User's full name

    **Raises**:
    - HTTPException: 401 if token is invalid or expired

    **Notes**:
    - Useful for validating tokens and checking user authentication status
    - Returns the same user information as /users/me endpoint

    **Permissions**:
    - Requires valid authentication token
    """
    return current_user