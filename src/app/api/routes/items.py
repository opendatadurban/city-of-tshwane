import uuid
from typing import Any
from fastapi import APIRouter, HTTPException
from app.api.deps import CurrentUser, SessionDep
from app.models.api.items import (
    ItemsResponse,
    ItemResponse,
    ItemCreateRequest,
    ItemUpdateRequest,
)
from app.models.api.generic import Message
from app.models.db import ItemInDb
from app.crud.items import CRUDItems

router = APIRouter(
    prefix="/items",
    tags=["items"],
)

@router.get("/", response_model=ItemsResponse)
async def read_items(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """## Retrieve paginated list of items.

    **Query Parameters**:
    - skip (int): Number of items to skip (default: 0)
    - limit (int): Maximum number of items to return (default: 100)

    **Returns**:
    - data (list): List of items where each item contains:
        - id (UUID): Item unique identifier
        - title (str): Item title
        - description (str): Item description
        - owner_id (UUID): ID of the user who owns the item
    - count (int): Total number of items available

    **Notes**:
    - Superusers can view all items
    - Regular users can only view their own items

    **Permissions**:
    - Requires authentication
    - Superusers: access to all items
    - Regular users: access to own items only
    """
    if current_user.is_superuser:
        count = await CRUDItems.get_count(session=session)
        items = await CRUDItems.get_all(session=session, skip=skip, limit=limit)
    else:
        count = await CRUDItems.get_count_by_owner_id(
            session=session, owner_id=current_user.id
        )
        items = await CRUDItems.get_by_owner_id(
            session=session, owner_id=current_user.id, skip=skip, limit=limit
        )
    item_return_list: list[ItemResponse] = list()
    for item in items:
        item_return_list.append(
            ItemResponse(
                id=item.id,
                title=item.title,
                description=item.description,
                owner_id=item.owner_id,
            )
        )
    return ItemsResponse(data=item_return_list, count=count)

@router.get("/{id}", response_model=ItemResponse)
async def read_item(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """## Retrieve a specific item by ID.

    **Path Parameters**:
    - id (UUID): Item unique identifier

    **Returns**:
    - id (UUID): Item unique identifier
    - title (str): Item title
    - description (str): Item description
    - owner_id (UUID): ID of the user who owns the item

    **Raises**:
    - HTTPException: 404 if item not found
    - HTTPException: 400 if user doesn't have permission to access the item

    **Permissions**:
    - Requires authentication
    - Superusers: access to any item
    - Regular users: access to own items only
    """
    item = await session.get(ItemInDb, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return item

@router.post("/", response_model=ItemResponse)
async def create_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    item_in: ItemCreateRequest,
) -> Any:
    """## Create a new item.

    **Request Body**:
    - title (str): Item title
    - description (str): Item description

    **Returns**:
    - id (UUID): Item unique identifier
    - title (str): Item title
    - description (str): Item description
    - owner_id (UUID): ID of the user who created the item

    **Notes**:
    - The current user is automatically set as the owner

    **Permissions**:
    - Requires authentication
    """
    item = await CRUDItems.create_item(
        session=session, item_in=item_in, owner_id=current_user.id
    )
    return item

@router.put("/{id}", response_model=ItemResponse)
async def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    item_in: ItemUpdateRequest,
) -> Any:
    """## Update a specific item.

    **Path Parameters**:
    - id (UUID): Item unique identifier

    **Request Body**:
    - title (str): New item title
    - description (str): New item description

    **Returns**:
    - id (UUID): Item unique identifier
    - title (str): Updated item title
    - description (str): Updated item description
    - owner_id (UUID): ID of the user who owns the item

    **Raises**:
    - HTTPException: 404 if item not found
    - HTTPException: 400 if user doesn't have permission to modify the item

    **Permissions**:
    - Requires authentication
    - Superusers: can update any item
    - Regular users: can only update own items
    """
    item = await session.get(ItemInDb, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    item = await CRUDItems.update_by_id(session=session, id_=id, data=item_in)
    return item

@router.delete("/{id}")
async def delete_item(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """## Delete a specific item.

    **Path Parameters**:
    - id (UUID): Item unique identifier

    **Returns**:
    - message (str): Success message

    **Raises**:
    - HTTPException: 404 if item not found
    - HTTPException: 400 if user doesn't have permission to delete the item

    **Permissions**:
    - Requires authentication
    - Superusers: can delete any item
    - Regular users: can only delete own items
    """
    item = await session.get(ItemInDb, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    await CRUDItems.remove_by_id(session=session, id_=id)
    return Message(message="Item deleted successfully")