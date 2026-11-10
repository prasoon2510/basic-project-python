from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Category(Base):

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    products = relationship(
        "Product",
        back_populates="category"
    )