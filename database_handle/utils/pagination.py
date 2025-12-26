from typing import Any, Callable

from sqlalchemy import func
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from database_handle.models.bindings import PaginationModel


async def with_paginated[T](
    db: AsyncSession,
    stmt: Select,
    page: int,
    limit: int,
    transform_fn: Callable[[Row[Any]], T],
) -> tuple[list[T], PaginationModel]:
    """
    Higher-order function to add pagination to any SQLAlchemy select statement.

    Args:
        db: AsyncSession database connection
        stmt: Base SQLAlchemy select statement
        page: Current page number (0-indexed)
        limit: Number of items per page
        transform_fn: Function to transform each row into the desired model

    Returns:
        Tuple of (list of transformed items, pagination metadata)
    """
    # Add total count as a window function and apply pagination
    paginated_stmt = (
        stmt.add_columns(func.count().over().label("total_items"))
        .limit(limit)
        .offset(page * limit)
    )

    result = (await db.execute(paginated_stmt)).all()

    if not result:
        return [], PaginationModel(
            total=0,
            current_page=page,
            total_pages=0,
            per_page=limit,
            has_next=False,
            has_previous=page > 0,
        )

    # Total is the same for all rows (window function), so grab from first row
    total_items = result[0][-1]  # Last column is total_items
    total_pages = (total_items + limit - 1) // limit  # Ceiling division

    # Transform each row using the provided function
    items = [transform_fn(row) for row in result]

    pagination = PaginationModel(
        total=total_items,
        current_page=page,
        total_pages=total_pages,
        per_page=limit,
        has_next=page < total_pages - 1,
        has_previous=page > 0,
        next_page=page + 1 if page < total_pages - 1 else None,
        previous_page=page - 1 if page > 0 else None,
    )

    return items, pagination
