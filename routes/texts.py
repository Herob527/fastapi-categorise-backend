from fastapi import APIRouter

__all__ = ["router"]

router = APIRouter(
    tags=["Texts"],
    prefix="/texts",
    responses={404: {"description": "Not found"}},
)


@router.get("/{text_id}")
async def get_text(text_id: int):
    print(f"Got text with ID: {text_id}")
    return {"test": text_id}


@router.get("/")
async def get_all_texts():
    print("Got all texts")
    return {"test": "test"}


@router.post("/")
async def post_new_text():
    print("Created new text")
    return {"test": "test"}


@router.patch("/{text_id}")
async def update_text(text_id: int):
    print("Updated text with name: {text_id}")
    return {"test": text_id}


@router.delete("/{text_id}")
async def remove_text(text_id: int):
    print(f"Removed text with ID: {text_id}")
    return {"test": text_id}
