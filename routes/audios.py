from fastapi import APIRouter

__all__ = ["router"]

router = APIRouter(
    tags=["Audio"],
    prefix="/audios",
    responses={404: {"description": "Not found"}},
)


@router.get("/{audio_id}")
async def get_audio(audio_id: int):
    print(f"Got audio with ID: {audio_id}")
    return {"test": audio_id}


@router.get("/")
async def get_all_audios():
    print("Printed all audios")
    return {"test": "test"}


@router.post("/")
async def post_new_audio():
    print("Created new audio")
    return {"test": "test"}


@router.delete("/{audio_id}")
async def remove_audio(audio_id: int):
    print(f"Removed audio with ID: {audio_id}")
    return {"test": audio_id}
