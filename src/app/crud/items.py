from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence
from sqlalchemy import select, func
import uuid

from app.models.db import ItemInDb
from app.crud.base import AsyncCrudBase
from app.models.api.items import ItemCreateRequest


class CRUDItems(AsyncCrudBase[ItemInDb]):
    sql_model = ItemInDb

    @staticmethod
    async def create_item(
        *,
        session: AsyncSession,
        item_in: ItemCreateRequest,
        owner_id: uuid.UUID
    ) -> ItemInDb:
        new_item = ItemInDb(
            title=item_in.title,
            description=item_in.description,
            owner_id=owner_id,
        )
        session.add(new_item)
        await session.commit()
        await session.refresh(new_item)
        return new_item

    @staticmethod
    async def get_by_owner_id(
        *,
        session: AsyncSession,
        owner_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[ItemInDb]:

        stmt = (
            select(ItemInDb)
            .where(ItemInDb.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        items = await session.execute(stmt)
        return items.scalars().all()

    @staticmethod
    async def get_count_by_owner_id(
        *, session: AsyncSession, owner_id: uuid.UUID
    ) -> int:

        count_stmt = (
            select(func.count())
            .select_from(ItemInDb)
            .where(ItemInDb.owner_id == owner_id)
        )
        count = await session.execute(count_stmt)
        count = count.scalar()
        if count is None:
            return 0
        return count

    @staticmethod
    async def get_count(*, session: AsyncSession) -> int | None:

        count_stmt = select(func.count()).select_from(ItemInDb)
        count = await session.execute(count_stmt)
        count = count.scalar()
        if count is None:
            return 0
        return count
