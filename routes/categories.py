from fastapi import APIRouter, Form

__all__ = ["router"]

router = APIRouter(
    tags=["Category"],
    prefix="/categories",
    responses={404: {"description": "Not found"}},
)


@router.get("/{category_id}")
async def get_category(category_id: int):
    print(f"Got category with ID: {category_id}")
    return {"test": category_id}


@router.get("/")
async def get_all_categories():
    print("Got all categories")
    return {"test": "test"}


@router.post("/")
async def post_new_category(category: str = Form()):
    print("Created new category")
    return {"test": "test"}


@router.patch("/{category_id}")
async def update_category(category_id: int):
    print(f"Updated category with name: {category_id}")
    return {"test": category_id}


@router.delete("/{category_id}")
async def remove_category(category_id: int):
    print(f"Removed category with ID: {category_id}")
    return {"test": category_id}
