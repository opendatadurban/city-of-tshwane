import secrets
import base64
import time
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, get_password_hash
from app.models.db import UserInDb
from app.models.api.users import UserCreateRequest
from app.crud.base import AsyncCrudBase
from app.core.security import send_email

from pydantic import EmailStr


class CRUDUsers(AsyncCrudBase[UserInDb]):
    sql_model = UserInDb

    @staticmethod
    async def create_user_with_hashed_password(
        session: AsyncSession, user_in: UserCreateRequest, password: str
    ) -> UserInDb:
        """
        Create a new task in the database.

        Args:
            db (AsyncSession): The database session.
            task_in (TaskCreateRequest): The task creation request object containing task data.

        Returns:
            Task: The newly created task object.
        """
        new_user = UserInDb(
            email=user_in.email,
            hashed_password=get_password_hash(password),
            is_active=user_in.is_active,
            is_superuser=user_in.is_superuser,
            full_name=user_in.full_name,
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

    @classmethod
    async def get_user_hashed_password(
        cls, *, session: AsyncSession, user_id: str
    ):
        stmt = select(UserInDb).where(UserInDb.id == user_id)
        user_data = await session.execute(stmt)
        user = user_data.unique().scalars().one()
        return user.hashed_password

    @classmethod
    async def update_user_password(
        cls, *, session: AsyncSession, current_user: UserInDb, new_password: str
    ):
        current_user.hashed_password = get_password_hash(new_password)
        session.add(current_user)
        await session.commit()
        await session.refresh(current_user)
        return True

    @classmethod
    async def get_user_by_email(
        cls, *, session: AsyncSession, email: EmailStr
    ) -> UserInDb | None:
        user = await cls.get_one_by_id(
            session=session, id_=email, column="email"
        )
        return user

    @classmethod
    async def authenticate(
        cls, *, session: AsyncSession, email: str, password: str
    ) -> UserInDb | None:
        logging.info(f"Start time user get: {datetime.now()}")
        db_user = await cls.get_user_by_email(session=session, email=email)
        logging.info(f"End time user get: {datetime.now()}")
        if not db_user:
            return None
        logging.info(f"Start time password verify: {datetime.now()}")
        if not verify_password(password, db_user.hashed_password):
            return None
        logging.info(f"End time password verify: {datetime.now()}")
        return db_user


    @classmethod
    async def send_password_reset_email(
        cls, session: AsyncSession, email: EmailStr, reset_url: str
    ) -> None:
        user = await cls.get_user_by_email(session=session, email=email)
        if not user:
            return None

        subject = "Verify your email address"
        body = f"Please verify your email by clicking the following link: {reset_url}"

        send_email(
            to_email=email,
            subject=subject,
            body=body,
        )

    @classmethod
    async def generate_password_reset_token(
        cls, user_id: str
    ) -> str:
        random_bytes = secrets.token_bytes(32)
        expires_at = int(time.time()) + 15 * 60  # 15 minutes from now (in seconds)
        payload = f"{user_id}:{expires_at}"
        payload_bytes = payload.encode("utf-8")
        token = base64.urlsafe_b64encode(payload_bytes).rstrip(b'=').decode('utf-8')
        return f"{user_id}.{token}"
    
    @classmethod
    async def verify_password_reset_token(
        cls, token: str
    ) -> str | None:
        try:
            user_id, token = token.split('.')
            payload_bytes = base64.urlsafe_b64decode(token + '==')
            payload = payload_bytes.decode("utf-8")
            user_id_from_payload, expires_at = payload.split(':')
            if user_id != user_id_from_payload:
                return None
            if int(time.time()) > int(expires_at):
                return None
            decoded_token = base64.urlsafe_b64decode(token + '==')
            return user_id
        except Exception as e:
            print(f"Token verification failed: {e}")
            return None