from fastapi import APIRouter, Depends, HTTPException
from typing import Any
from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.crud import CRUDUsers
from app.models.api.users import (
    UserCreateRequest,
    UserCreateResponse,
    UserPatchResponse,
    UserPatchResetPasswordRequest,
)

router = APIRouter(tags=["register"])

@router.post("/signup", response_model=UserCreateResponse, status_code=201)
async def register_user(
    session: SessionDep,
    user_in: UserCreateRequest,
) -> Any:
    """## Create a new user account.

    **Request Body**:
    - email (str): User email address
    - password (str): User password
    - re_password (str): User password confirmation
    - full_name (str): User's full name
    - is_active (bool, optional): User active status
    - is_superuser (bool, optional): User superuser status

    **Returns**:
    - id (UUID): User unique identifier
    - email (str): User email address
    - is_active (bool): User active status
    - is_superuser (bool): User superuser status
    - full_name (str): User's full name

    **Raises**:
    - HTTPException: 400 if email already exists

    **Permissions**:
    - No authentication required
    """
    user = await CRUDUsers.get_user_by_email(
        session=session, email=user_in.email
    )
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    
    if user_in.password != user_in.re_password:
        raise HTTPException(
            status_code=400,
            detail="Password mismatch, please check your password and try again",
        )

    created_user = await CRUDUsers.create_user_with_hashed_password(
        session=session, user_in=user_in, password=user_in.password
    )
    response = UserCreateResponse(
        id=created_user.id,
        email=created_user.email,
        is_active=created_user.is_active,
        is_superuser=created_user.is_superuser,
        full_name=created_user.full_name,
    )
    return response


@router.post("/request-reset-password", status_code=200)
async def request_reset_password(
    session: SessionDep,
    email: str,
) -> Any:
    """
    Initiate password reset by email.

    **Request Body**:
    - email (str): User email address

    **Returns**:
    - message (str): Status message

    **Raises**:
    - HTTPException: 404 if email not found
    """
    user = await CRUDUsers.get_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User with this email does not exist")

    # Generate token (implement your own token generation logic)
    token = await CRUDUsers.generate_password_reset_token(user.id)

    # Send email with tokenized URL (implement your own email sending logic)
    reset_url = f"{settings.DOMAIN_URL}/reset-password?token={token}"
    await CRUDUsers.send_password_reset_email(session, user.email, reset_url)

    return {"message": "Password reset instructions sent to your email."}

@router.patch("/reset-password", status_code=200)
async def reset_password(
    session: SessionDep,
    request: UserPatchResetPasswordRequest,
) -> UserPatchResponse:
    """
    Reset user password using a valid reset token.

    **Request Body**:
    - token (str): Password reset token
    - new_password (str): New password

    **Returns**:
    - UserPatchResponse: Updated user info

    **Raises**:
    - HTTPException: 400 if token is invalid or expired
    - HTTPException: 404 if user not found
    """
    user_id = await CRUDUsers.verify_password_reset_token(request.token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = await CRUDUsers.get_one_by_id(session=session, id_=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if request.new_password != request.re_new_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    await CRUDUsers.update_user_password(
        session=session,
        current_user=user,
        new_password=request.new_password,
    )

    return UserPatchResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        full_name=user.full_name,
    )

