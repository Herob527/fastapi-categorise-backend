from typing import Annotated
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
import librosa
from io import BytesIO
from pydantic import UUID4

from sqlalchemy.orm import Session
from database_handle.database import get_db
from database_handle.models.audios import Audios
from database_handle.queries.audios import create_audio


class NotAnAudio(Exception):
    pass


__all__ = ["router"]

router = APIRouter(
    tags=["Audio"],
    prefix="/audios",
    responses={404: {"description": "Not found"}},
)


@router.get("{audio_id}")
async def get_audio(audio_id: int):
    print(f"Got audio with ID: {audio_id}")
    return {"test": audio_id}


@router.get("")
async def get_all_audios():
    print("Printed all audios")
    return {"test": "test"}


@router.post("", responses={400: {"description": "Invalid file"}})
async def post_new_audio(id: UUID4, file: UploadFile, db: Session = Depends(get_db)):
    try:
        y_stereo, sr = librosa.load(BytesIO(file.file.read()), sr=None, mono=False)
    except:
        raise HTTPException(status_code=400, detail="Invalid file")
    duration = round(librosa.get_duration(y=y_stereo, sr=sr), 2)
    channels = len(y_stereo)
    params = Audios(
        id=id, audio_length=duration, channels=channels, url="test", frequency=int(sr)
    )
    create_audio(db=db, audio=params)
    return {
        "test": f"duration: {duration} seconds and amount of channels is equal to {channels} "
    }


@router.delete("{audio_id}")
async def remove_audio(audio_id: int):
    print(f"Removed audio with ID: {audio_id}")
    return {"test": audio_id}
