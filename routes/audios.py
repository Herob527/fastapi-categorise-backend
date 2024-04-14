from uuid import uuid4
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
import librosa
from io import BytesIO
from pydantic import UUID4
from pathlib import Path
from sqlalchemy.orm import Session
from database_handle.database import get_db
from database_handle.models.audios import Audios
from database_handle.queries.audios import create_audio, audio_exists


class NotAnAudio(Exception):
    pass


__all__ = ["router"]

router = APIRouter(
    tags=["Audio"],
    prefix="/audios",
    responses={404: {"description": "Not found"}},
)


@router.get("{audio_id}")
async def get_audio(audio_id: UUID4):
    print(f"Got audio with ID: {audio_id}")
    return {"test": audio_id}


@router.get("")
async def get_all_audios():
    print("Printed all audios")
    return {"test": "test"}


@router.post("", responses={400: {"description": "Invalid file"}})
async def post_new_audio(
    id: UUID4 = Form(),
    file: UploadFile = Form(),
    db: Session = Depends(get_db),
    commit=True,
):
    output_dir = Path("audios")
    file_data = file.file.read()
    # TODO: Handle not-audio files
    try:
        y_stereo, sr = librosa.load(BytesIO(file_data), sr=None, mono=False)
    except:
        print("[post_new_audio - 'invalid-file']", "invalid-file")
        raise HTTPException(status_code=400, detail="Invalid file")

    output_dir.mkdir(exist_ok=True)

    duration = round(librosa.get_duration(y=y_stereo, sr=sr), 2)
    channels = len(y_stereo)
    filename_path = Path(file.filename or "")
    url = Path(output_dir, f"{uuid4()}{filename_path.suffix}")

    params = Audios(
        id=id,
        audio_length=duration,
        channels=channels,
        file_name=file.filename,
        url=str(url),
        frequency=int(sr),
    )
    create_audio(db=db, audio=params)

    with url.open("bw") as audio_output:
        audio_output.write(file_data)

    if commit:
        db.commit()

    return {
        "test": f"duration: {duration} seconds and amount of channels is equal to {channels} "
    }


@router.delete("{audio_id}")
async def remove_audio(audio_id: UUID4):
    print(f"Removed audio with ID: {audio_id}")
    return {"test": audio_id}
