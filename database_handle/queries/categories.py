from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from pydantic import UUID4
from sqlalchemy import Column, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func, select

from database_handle.database import get_db
from database_handle.models.categories import Category


@dataclass
class CategoriesQueries:
    session: AsyncSession

    async def get_one(self, id: Column[str] | str | UUID4):
        entry = await self.session.scalar(select(Category).where(Category.id == id))
        return entry

    async def get_one_by_name(self, name: Column[str] | str):
        entry = await self.session.scalar(
            select(Category).where(Category.name == name).limit(1)
        )
        return entry

    async def get_count(self):
        count_func = func.count(Category.id)
        entry = (
            await self.session.execute(select(count_func).select_from(Category))
        ).scalar() or 0
        return entry

    async def get_all(self):
        return (await self.session.scalars(select(Category))).all()

    async def remove(self, name: str):
        query = select(Category).where(Category.name == name).limit(1)
        entry = (await self.session.scalars(query)).first()
        if entry is None:
            raise Exception("Category not found")
        await self.session.delete(entry)
        await self.session.commit()

    async def create(self, category: Category):
        category_exists = await self.get_one(id=category.id)
        if category_exists:
            return
        self.session.add(category)
        await self.session.commit()

    async def update(self, category: Category):
        stmt = (
            update(Category)
            .where(Category.id == category.id)
            .values(name=category.name)
        )
        await self.session.execute(stmt)
        await self.session.commit()


def get_categories_queries(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoriesQueries:
    return CategoriesQueries(session=db)
