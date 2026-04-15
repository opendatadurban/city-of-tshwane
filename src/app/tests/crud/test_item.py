import pytest
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.items import CRUDItems
from app.crud.users import CRUDUsers
from app.models.api.items import ItemCreateRequest
from app.models.db import UserInDb
from app.core.config import settings


@pytest.fixture
def item_create_request():
    return ItemCreateRequest(title="Test Item", description="Test Description")


# Test CRUDItems
@pytest.mark.asyncio
class TestCRUDItems:

    async def test_create_item(
        self,
        session: AsyncSession,
        item_create_request: ItemCreateRequest,
        get_item_owner: UserInDb,
    ):
        owner_id = get_item_owner.id
        item = await CRUDItems.create_item(
            session=session, item_in=item_create_request, owner_id=owner_id
        )

        assert item.title == item_create_request.title
        assert item.description == item_create_request.description
        assert item.owner_id == owner_id
        assert isinstance(item.id, uuid.UUID)

    async def test_get_by_owner_id(
        self,
        session: AsyncSession,
        item_create_request: ItemCreateRequest,
        get_item_owner: UserInDb,
    ):
        owner_id = get_item_owner.id

        # Create multiple items
        items = []
        for i in range(3):
            item = await CRUDItems.create_item(
                session=session,
                item_in=ItemCreateRequest(
                    title=f"Test Item {i}", description=f"Test Description {i}"
                ),
                owner_id=owner_id,
            )
            items.append(item)

        supe_owner = await CRUDUsers.get_user_by_email(
            session=session, email=settings.FIRST_SUPERUSER
        )

        # Create item with different owner
        await CRUDItems.create_item(
            session=session, item_in=item_create_request, owner_id=supe_owner.id
        )

        # Test retrieval
        retrieved_items = await CRUDItems.get_by_owner_id(
            session=session, owner_id=owner_id
        )

        assert len(retrieved_items) == 3
        for item in retrieved_items:
            assert item.owner_id == owner_id

    async def test_get_count_by_owner_id(
        self,
        session: AsyncSession,
        item_create_request: ItemCreateRequest,
        get_item_owner: UserInDb,
    ):
        owner_id = get_item_owner.id

        # Create multiple items
        for i in range(3):
            await CRUDItems.create_item(
                session=session, item_in=item_create_request, owner_id=owner_id
            )

        count = await CRUDItems.get_count_by_owner_id(
            session=session, owner_id=owner_id
        )

        assert count == 3

    async def test_get_count(
        self,
        session: AsyncSession,
        item_create_request: ItemCreateRequest,
        get_item_owner: UserInDb,
    ):
        owner_id = get_item_owner.id

        # Create multiple items
        for i in range(3):
            await CRUDItems.create_item(
                session=session, item_in=item_create_request, owner_id=owner_id
            )

        count = await CRUDItems.get_count(session=session)
        assert count == 3
