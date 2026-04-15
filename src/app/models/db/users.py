import uuid
from sqlalchemy import String
from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.models.db import SQLBase


class UserInDb(SQLBase):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column()
    items: Mapped[list["ItemInDb"]] = relationship(
        back_populates="owner", cascade="all, delete"
    )
