from io import BytesIO
from typing import Annotated

import librosa
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database_handle.database import get_db
from database_handle.models.audios import Audio, StatusEnum
from database_handle.queries.audios import AudioQueries
from services.minio_service import minio_service

router = APIRouter(prefix="/audio", tags=["audio"])


@router.post("/upload")
async def upload_audio(
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile,
    uuid: UUID4,
    folder: str = "audio",
):
    """Upload audio file to MinIO and save metadata to database"""
    if file.content_type is None:
        raise HTTPException(status_code=400, detail="File type not specified")
    if file.filename is None:
        raise HTTPException(status_code=400, detail="File name not specified")
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Only audio files are allowed")

    file_content = await file.read()
    file_size = len(file_content)
    file_name = file.filename
    content_type = file.content_type

    object_name = await minio_service.upload_file(
        file_data=BytesIO(file_content),
        size=file_size,
        filename=file_name,
        content_type=content_type,
        folder=folder,
        metadata={"uuid": str(uuid)},
    )

    y, sr = librosa.load(BytesIO(file_content), sr=None)
    audio_length = librosa.get_duration(y=y, sr=sr)

    async with db.begin() as session:
        queries = AudioQueries(session=session.session)
        await queries.update_audio(
            audio_id=uuid,
            url=object_name,
            audio_length=audio_length,
            status=StatusEnum.available,
        )


@router.get("/download/{audio_id}")
async def download_audio(audio_id: UUID4, db: Annotated[AsyncSession, Depends(get_db)]):
    """Download audio file by UUID"""
    audio_record = (
        await db.scalars(select(Audio).where(Audio.id == audio_id).limit(1))
    ).first()
    if not audio_record:
        raise HTTPException(status_code=404, detail="Audio file not found")

    object_name = str(audio_record.url)

    file_data = await minio_service.download_file(object_name)

    return StreamingResponse(
        BytesIO(file_data),
        media_type="audio/wav",
        headers={
            "Content-Disposition": f"attachment; filename={audio_record.file_name}"
        },
    )


@router.get("/download/{audio_id}/url")
async def download_url(audio_id: str):
    return await minio_service.get_file_url(audio_id)


@router.get("/url/{audio_id}")
async def get_audio_url(
    db: Annotated[AsyncSession, Depends(get_db)],
    audio_id: UUID4,
    expires: int = 3600,
):
    """Get presigned URL for audio file access"""
    audio_record = await db.scalar(select(Audio).where(Audio.id == audio_id).limit(1))
    if not audio_record:
        raise HTTPException(status_code=404, detail="Audio file not found")

    object_name = audio_record.url.split(f"{minio_service.bucket_name}/")[-1]

    url = await minio_service.get_file_url(object_name, expires)

    return {"url": url, "expires_in": expires}


@router.delete("/{audio_id}")
async def delete_audio(audio_id: UUID4, db: Annotated[AsyncSession, Depends(get_db)]):
    """Delete audio file from both MinIO and database"""
    audio_record = await db.scalar(select(Audio).where(Audio.id == audio_id).limit(1))
    if not audio_record:
        raise HTTPException(status_code=404, detail="Audio file not found")

    object_name = str(audio_record.url).split(f"{minio_service.bucket_name}/")[-1]

    success = await minio_service.delete_file(object_name)

    if success:
        async with db.begin() as session:
            await session.delete(audio_record)
        return {"message": "Audio file deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete audio file")
