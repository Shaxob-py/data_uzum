from enum import Enum

from sqlalchemy import select, update
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import String, Integer, BigInteger, Enum as SQLEnum

from database.base import CreatedModel, db


class User(CreatedModel):
    class Role(Enum):
        ADMIN = 'Admin'
        USER = 'User'

    name: Mapped[str] = mapped_column(String(100))
    coin: Mapped[str] = mapped_column(Integer(), default=100)
    telegram_id: Mapped[str] = mapped_column(BigInteger(), unique=True)
    phone: Mapped[str] = mapped_column(String(14))
    role: Mapped[Role] = mapped_column(
        SQLEnum(Role, name="role"),
        default=Role.USER,

    )
    password: Mapped[str] = mapped_column(String(100), nullable=True)

    @classmethod
    async def get_by_telegram_id(cls, telegram_id: int):
        query = (
            select(cls).where(cls.telegram_id == telegram_id))
        res = await db.execute(query)
        return res.first()

    @classmethod
    async def update_coin(cls, telegram_id: int, coin: int):
        query = (
            update(cls)
            .where(cls.telegram_id == telegram_id)
            .values(coin=cls.coin - coin)
        )

        await db.execute(query)
        await db.commit()

    @classmethod
    async def check_coin(cls, telegram_id: int):
        query = (
            select(cls).where(cls.telegram_id == telegram_id))
        res = await db.execute(query)
        return res.scalar()

    @classmethod
    async def give_coin(cls, phone: str, coin: int):
        query = (update(cls).where(cls.phone == phone).values(coin=cls.coin + coin))
        await db.execute(query)
        await db.commit()

    @classmethod
    async def get_by_phone(cls, phone: str):
        query = (select(cls).where(cls.phone == phone))
        res = await db.execute(query)

        return res.scalar()
