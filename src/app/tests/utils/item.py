from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db import ItemInDb
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_lower_string
from app.crud.items import CRUDItems
from app.models.api.items import ItemCreateRequest


async def create_random_item(session: AsyncSession) -> ItemInDb:
    user, password = await create_random_user(session)
    owner_id = user.id
    assert owner_id is not None
    title = random_lower_string()
    description = random_lower_string()
    item = await CRUDItems.create_item(
        session=session,
        item_in=ItemCreateRequest(title=title, description=description),
        owner_id=owner_id,
    )
    return item
