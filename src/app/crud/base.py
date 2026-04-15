# Heavily inspired by https://medium.com/@lawsontaylor/the-factory-and-repository-pattern-with-sqlalchemy-and-pydantic-33cea9ae14e0
from uuid import UUID

from sqlalchemy import delete, select, asc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db import SQLBase
from pydantic import BaseModel as PydanticBaseModel


class CrudException(Exception):
    pass


class IntegrityConflictException(Exception):
    pass


class NotFoundException(Exception):
    pass


class AsyncCrudBase[
    DbModelType: SQLBase
]:

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        data: PydanticBaseModel,
    ) -> DbModelType:
        """Accepts a Pydantic model, creates a new record in the database, catches
        any integrity errors, and returns the record.

        Args:
            session (AsyncSession): SQLAlchemy async session
            data (PydanticBaseModel): Pydantic model

        Raises:
            IntegrityConflictException: if creation conflicts with existing data
            CrudException: if an unknown error occurs

        Returns:
            SQLBase: created SQLAlchemy model
        """
        try:
            db_model = cls.sql_model(**data.model_dump())
            session.add(db_model)
            await session.commit()
            await session.refresh(db_model)
            return db_model
        except IntegrityError:
            raise IntegrityConflictException(
                f"{cls.sql_model.__tablename__} conflicts with existing data.",
            )
        except Exception as e:
            raise CrudException(f"Unknown error occurred: {e}") from e

    @classmethod
    async def create_many(
        cls,
        session: AsyncSession,
        data: list[PydanticBaseModel],
        return_models: bool = False,
    ) -> list[DbModelType] | bool:
        """_summary_

        Args:
            session (AsyncSession): SQLAlchemy async session
            data (list[PydanticBaseModel]): list of Pydantic models
            return_models (bool, optional): Should the created models be returned
                or a boolean indicating they have been created. Defaults to False.

        Raises:
            IntegrityConflictException: if creation conflicts with existing data
            CrudException: if an unknown error occurs

        Returns:
            list[SQLBase] | bool: list of created SQLAlchemy models or boolean
        """
        db_models = [cls.sql_model(**d.model_dump()) for d in data]
        try:
            session.add_all(db_models)
            await session.commit()
        except IntegrityError:
            raise IntegrityConflictException(
                f"{cls.sql_model.__tablename__} conflict with existing data.",
            )
        except Exception as e:
            raise CrudException(f"Unknown error occurred: {e}") from e

        if not return_models:
            return True

        for m in db_models:
            await session.refresh(m)

        return db_models

    @classmethod
    async def get_all(
        cls,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DbModelType]:
        """Fetches all records from the database and returns them.

        Args:
            session (AsyncSession): SQLAlchemy async session
            skip (int, optional): number of records to skip. Defaults to 0.
            limit (int, optional): number of records to return. Defaults to 100.

        Returns:
            list[SQLBase]: list of SQLAlchemy models
        """
        stmt = (
            select(cls.sql_model)
            .offset(skip)
            .limit(limit)
        )
        rows = await session.execute(stmt)

        data = rows.scalars().all()
        public_data = [d for d in data]
        return public_data

    @classmethod
    async def get_one_by_id(
        cls,
        session: AsyncSession,
        id_: str | UUID,
        column: str = "id",
        with_for_update: bool = False,
    ) -> DbModelType:
        """Fetches one record from the database based on a column value and returns
        it, or returns None if it does not exist. Raises an exception if the column
        doesn't exist.

        Args:
            session (AsyncSession): SQLAlchemy async session
            id_ (str | UUID): value to search for in `column`.
            column (str, optional): the column name in which to search.
                Defaults to "uuid".
            with_for_update (bool, optional): Should the returned row be locked
                during the lifetime of the current open transactions.
                Defaults to False.

        Raises:
            CrudException: if the column does not exist on the model

        Returns:
            SQLBase: SQLAlchemy model or None
        """
        try:
            stmt = select(cls.sql_model).where(getattr(cls.sql_model, column) == id_)
        except AttributeError:
            raise CrudException(
                f"Column {column} not found on {cls.sql_model.__tablename__}.",
            )

        if with_for_update:
            stmt = stmt.with_for_update()

        results = await session.execute(stmt)
        return_data = results.unique().scalar_one_or_none()
        if return_data:
            return return_data
        return None

    @classmethod
    async def get_many_by_ids(
        cls,
        session: AsyncSession,
        ids: list[str | UUID] = None,
        column: str = "id",
        with_for_update: bool = False,
    ) -> list[DbModelType]:
        """Fetches multiple records from the database based on a column value and
        returns them. Raises an exception if the column doesn't exist.

        Args:
            session (AsyncSession): SQLAlchemy async session
            ids (list[str  |  UUID], optional): list of values to search for in
                `column`. Defaults to None.
            column (str, optional): the column name in which to search
                Defaults to "uuid".
            with_for_update (bool, optional): Should the returned rows be locked
                during the lifetime of the current open transactions.
                Defaults to False.

        Raises:
            CrudException: if the column does not exist on the model

        Returns:
            list[SQLBase]: list of SQLAlchemy models
        """
        stmt = select(cls.sql_model)
        if ids:
            try:
                stmt = stmt.where(getattr(cls.sql_model, column).in_(ids))
            except AttributeError:
                raise CrudException(
                    f"Column {column} not found on {cls.sql_model.__tablename__}.",
                )

        if with_for_update:
            stmt = stmt.with_for_update()

        rows = await session.execute(stmt)
        return rows.unique().scalars().all()

    @classmethod
    async def update_by_id(
        cls,
        session: AsyncSession,
        data: PydanticBaseModel,
        id_: str | UUID,
        column: str = "id",
    ) -> DbModelType:
        """Updates a record in the database based on a column value and returns the
        updated record. Raises an exception if the record isn't found or if the
        column doesn't exist.

        Args:
            session (AsyncSession): SQLAlchemy async session
            data (PydanticBaseModel): Pydantic schema for the updated data.
            id_ (str | UUID): value to search for in `column`
            column (str, optional): the column name in which to search
                Defaults to "uuid".
        Raises:
            NotFoundException: if the record isn't found
            IntegrityConflictException: if the update conflicts with existing data

        Returns:
            SQLBase: updated SQLAlchemy model
        """
        db_model = await cls.get_one_by_id(
            session, id_, column=column, with_for_update=True
        )
        if not db_model:
            raise NotFoundException(
                f"{cls.sql_model.__tablename__} {column}={id_} not found.",
            )

        values = data.model_dump(exclude_unset=True)
        for k, v in values.items():
            setattr(db_model, k, v)

        try:
            session.add(db_model)
            await session.commit()
            await session.refresh(db_model)
            return db_model
        except IntegrityError:
            raise IntegrityConflictException(
                f"{cls.sql_model.__tablename__}"
                f"{column}={id_} conflict with existing data.",
            )

    @classmethod
    async def update_many_by_ids(
        cls,
        session: AsyncSession,
        updates: dict[str | UUID, PydanticBaseModel],
        column: str = "id",
        return_models: bool = False,
    ) -> list[DbModelType] | bool:
        """Updates multiple records in the database based on a column value and
        returns the updated records. Raises an exception if the column doesn't
        exist.

        Args:
            session (AsyncSession): SQLAlchemy async session
            updates (dict[str  |  UUID, PydanticBaseModel]): dictionary of id_ to
                Pydantic update schema
            column (str, optional): the column name in which to search.
                Defaults to "uuid".
            return_models (bool, optional): Should the created models be returned
                or a boolean indicating they have been created. Defaults to False.
                Defaults to False.

        Raises:
            IntegrityConflictException: if the update conflicts with existing data

        Returns:
            list[SQLBase] | bool: list of updated SQLAlchemy models or boolean
        """
        updates = {str(id): update for id, update in updates.items() if update}
        ids = list(updates.keys())
        db_models = await cls.get_many_by_ids(
            session, ids=ids, column=column, with_for_update=True
        )

        for db_model in db_models:
            values = updates[str(getattr(db_model, column))].model_dump(
                exclude_unset=True
            )
            for k, v in values.items():
                setattr(db_model, k, v)
            session.add(db_model)

        try:
            await session.commit()
        except IntegrityError:
            raise IntegrityConflictException(
                f"{cls.sql_model.__tablename__} conflict with existing data.",
            )

        if not return_models:
            return True

        for db_model in db_models:
            await session.refresh(db_model)

        return db_models

    @classmethod
    async def remove_by_id(
        cls,
        session: AsyncSession,
        id_: str | UUID,
        column: str = "id",
    ) -> int:
        """Removes a record from the database based on a column value. Raises an
        exception if the column doesn't exist.

        Args:
            session (AsyncSession): SQLAlchemy async session
            id (str | UUID): value to search for in `column` and delete
            column (str, optional): the column name in which to search.
                Defaults to "uuid".

        Raises:
            CrudException: if the column does not exist on the model

        Returns:
            int: number of rows removed, 1 if successful, 0 if not. Can be greater
                than 1 if id_ is not unique in the column.
        """
        try:
            stmt = delete(cls.sql_model).where(getattr(cls.sql_model, column) == id_)
        except AttributeError:
            raise CrudException(
                f"Column {column} not found on {cls.sql_model.__tablename__}.",
            )

        rows = await session.execute(stmt)
        await session.commit()
        return rows.rowcount

    @classmethod
    async def remove_many_by_ids(
        cls,
        session: AsyncSession,
        ids: list[str | UUID],
        column: str = "id",
    ) -> int:
        """Removes multiple records from the database based on a column value.
        Raises an exception if the column doesn't exist.

        Args:
            session (AsyncSession): SQLAlchemy async session
            ids (list[str  |  UUID]): list of values to search for in `column` and
            column (str, optional): the column name in which to search.
                Defaults to "uuid".

        Raises:
            CrudException: if ids is empty to stop deleting an entire table
            CrudException: if column does not exist on the model

        Returns:
            int: _description_
        """
        if not ids:
            raise CrudException("No ids provided.")

        try:
            stmt = delete(cls.sql_model).where(getattr(cls.sql_model, column).in_(ids))
        except AttributeError:
            raise CrudException(
                f"Column {column} not found on {cls.sql_model.__tablename__}.",
            )

        rows = await session.execute(stmt)
        await session.commit()
        return rows.rowcount
