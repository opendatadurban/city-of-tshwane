import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from app.crud import CRUDUsers
from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.security import verify_password
from app.models.api.users import (
    UserGetResponse,
    UsersGetResponse,
    UserCreateRequest,
    UserCreateResponse,
    UserPatchRequest,
    UserPatchResponse,
    UserPatchPasswordRequest,
)
from app.models.api.generic import Message

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersGetResponse,
)
async def read_users(
    session: SessionDep, skip: int = 0, limit: int = 100
) -> Any:
    """## Retrieve all users with pagination.

    **Query Parameters**:
    - skip (int): Number of users to skip (default: 0)
    - limit (int): Maximum number of users to return (default: 100)

    **Returns**:
    - users (list): List of users where each user contains:
        - id (UUID): User unique identifier
        - email (str): User email address
        - is_active (bool): User active status
        - is_superuser (bool): User superuser status
        - full_name (str): User's full name
    - count (int): Total number of users returned

    **Permissions**:
    - Requires superuser access
    """
    users = await CRUDUsers.get_all(session=session, skip=skip, limit=limit)
    user_return_list: list[UserGetResponse] = list()
    for user in users:
        user_return_list.append(
            UserGetResponse(
                id=user.id,
                email=user.email,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                full_name=user.full_name,
            )
        )
    return UsersGetResponse(users=user_return_list, count=len(user_return_list))


@router.get("/me", response_model=UserGetResponse)
async def read_user_me(current_user: CurrentUser) -> Any:
    """## Retrieve current user's information.

    **Returns**:
    - id (UUID): User unique identifier
    - email (str): User email address
    - is_active (bool): User active status
    - is_superuser (bool): User superuser status
    - full_name (str): User's full name

    **Permissions**:
    - Requires authentication
    """
    response = UserGetResponse(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        full_name=current_user.full_name,
    )
    return response


@router.delete("/me", status_code=204)
async def delete_user_me(
    session: SessionDep, current_user: CurrentUser
) -> None:
    """## Delete current user's account.

    **Returns**:
    - None

    **Raises**:
    - HTTPException: 403 if user is a superuser (superusers cannot delete themselves)

    **Permissions**:
    - Requires authentication
    - Not available for superusers
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Super users are not allowed to delete themselves",
        )
    await CRUDUsers.remove_by_id(session=session, id_=current_user.id)
    return None


@router.post("/signup", response_model=UserCreateResponse, status_code=201)
async def register_user(
    session: SessionDep,
    user_in: UserCreateRequest,
) -> Any:
    """## Create a new user account.

    **Request Body**:
    - email (str): User email address
    - password (str): User password
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


@router.get("/{user_id}", response_model=UserGetResponse)
async def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """## Retrieve a specific user by ID.

    **Path Parameters**:
    - user_id (UUID): User unique identifier

    **Returns**:
    - id (UUID): User unique identifier
    - email (str): User email address
    - is_active (bool): User active status
    - is_superuser (bool): User superuser status
    - full_name (str): User's full name

    **Raises**:
    - HTTPException: 404 if user not found (for superusers)
    - HTTPException: 403 if insufficient privileges

    **Permissions**:
    - Users can view their own information
    - Superusers can view any user's information
    """
    user = await CRUDUsers.get_one_by_id(session=session, id_=user_id)
    if not user and current_user.is_superuser:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    elif not user:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    if current_user.id == user_id:
        response = UserGetResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            full_name=user.full_name,
        )
        return response
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )

    response = UserGetResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        full_name=user.full_name,
    )
    return response


@router.patch("/me")
async def update_user_me(
    session: SessionDep, user_in: UserPatchRequest, current_user: CurrentUser
) -> Any:
    """## Update current user's information.

    **Request Body** (all fields optional):
    - email (str | None): New email address
    - full_name (str | None): New full name
    - is_active (bool | None): New active status

    **Returns**:
    - message (str): Success message

    **Raises**:
    - HTTPException: 409 if new email already exists for another user

    **Permissions**:
    - Requires authentication
    """
    if user_in.email:
        existing_user = await CRUDUsers.get_user_by_email(
            session=session, email=user_in.email
        )
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    db_user = await CRUDUsers.update_by_id(
        session=session, data=user_in, id_=current_user.id
    )
    return {"message": "User updated successfully"}


@router.patch("/me/password", status_code=200)
async def update_password_me(
    *,
    session: SessionDep,
    body: UserPatchPasswordRequest,
    current_user: CurrentUser,
) -> Any:
    """## Update current user's password.

    **Request Body**:
    - current_password (str): Current password
    - new_password (str): New password

    **Returns**:
    - message (str): Success message

    **Raises**:
    - HTTPException: 400 if current password is incorrect
    - HTTPException: 400 if new password is same as current password

    **Permissions**:
    - Requires authentication
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400,
            detail="New password cannot be the same as the current one",
        )
    await CRUDUsers.update_user_password(
        session=session,
        current_user=current_user,
        new_password=body.new_password,
    )
    return {"message": "Password updated successfully"}


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPatchResponse,
)
async def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserPatchRequest,
) -> Any:
    """## Update a specific user's information.

    **Path Parameters**:
    - user_id (UUID): User unique identifier

    **Request Body** (all fields optional):
    - email (str | None): New email address
    - full_name (str | None): New full name
    - is_active (bool | None): New active status

    **Returns**:
    - id (UUID): User unique identifier
    - email (str): User email address
    - is_active (bool): User active status
    - is_superuser (bool): User superuser status
    - full_name (str): User's full name

    **Raises**:
    - HTTPException: 404 if user not found
    - HTTPException: 409 if new email already exists for another user

    **Permissions**:
    - Requires superuser access
    """
    user = await CRUDUsers.get_one_by_id(session=session, id_=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = await CRUDUsers.get_user_by_email(
            session=session, email=user_in.email
        )
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    db_user = await CRUDUsers.update_by_id(
        session=session, data=user_in, id_=user_id
    )
    return db_user


@router.delete(
    "/{user_id}", dependencies=[Depends(get_current_active_superuser)]
)
async def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """## Delete a specific user.

    **Path Parameters**:
    - user_id (UUID): User unique identifier

    **Returns**:
    - message (str): Success message

    **Raises**:
    - HTTPException: 404 if user not found
    - HTTPException: 403 if attempting to delete own superuser account

    **Permissions**:
    - Requires superuser access
    - Superusers cannot delete themselves
    """
    user = await CRUDUsers.get_one_by_id(session=session, id_=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Super users are not allowed to delete themselves",
        )
    await CRUDUsers.remove_by_id(session=session, id_=user_id)

    return Message(message="User deleted successfully")