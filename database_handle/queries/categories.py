from sqlalchemy import Column, update
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import UUID4
from sqlalchemy.sql.expression import func, select
from database_handle.models.categories import Category


async def get_one_category(db: AsyncSession, id: Column[str] | str | UUID4):
    entry = (await db.execute(select(Category).where(Category.id == id))).first()
    return entry


async def get_one_category_by_name(db: AsyncSession, name: Column[str] | str):
    entry = await db.scalar(select(Category).where(Category.name == name).limit(1))
    return entry


async def get_categories_count(db: AsyncSession):
    count_func = func.count(Category.id)
    entry = (await db.execute(select(count_func).select_from(Category))).scalar() or 0
    return entry


async def get_all_categories(db: AsyncSession):
    return (await db.scalars(select(Category))).all()


async def remove_category(db: AsyncSession, name: str):
    query = select(Category).where(Category.name == name).limit(1)
    entry = (await db.scalars(query)).first()
    if entry is None:
        raise Exception("Category not found")
    await db.delete(entry)


async def create_category(db: AsyncSession, category: Category):
    category_exists = await get_one_category(db, id=category.id)
    if category_exists:
        return
    db.add(category)


async def update_category(db: AsyncSession, category: Category):
    stmt = update(Category).where(Category.id == category.id).values(name=category.name)
    await db.execute(stmt)
