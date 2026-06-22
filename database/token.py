from sqlalchemy import select, delete, insert
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import String

from database.base import db, Model


class Token(Model):
    token: Mapped[str] = mapped_column(String())

    @classmethod
    async def get_token(cls):
        query = (select(cls))
        res = await db.execute(query)
        return res.scalar()

    @classmethod
    async def update_token(cls, token: str):
        await db.execute(delete(cls))
        await db.execute(insert(cls).values(token=token))
        await db.commit()
