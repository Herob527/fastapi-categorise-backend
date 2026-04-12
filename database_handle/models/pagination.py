from pydantic import BaseModel


class PaginationModel(BaseModel):
    total: int
    current_page: int
    total_pages: int
    per_page: int
    has_next: bool
    has_previous: bool
    next_page: int | None = None
    previous_page: int | None = None


class Paginated[T](BaseModel):
    items: list[T]
    pagination: PaginationModel
