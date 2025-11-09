from uuid import uuid4
from pprint import pprint
from fastapi import APIRouter, BackgroundTasks, UploadFile, HTTPException, Depends
from fastapi.responses import StreamingResponse
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
import librosa
from pydantic import UUID4
from sqlalchemy.orm.query import sql
from sqlalchemy.sql.expression import select
from database_handle.database import get_db
from database_handle.models.audios import Audio, AudioModel, StatusEnum
from database_handle.queries.audios import AudioQueries
from services.minio_service import minio_service

router = APIRouter(prefix="/audio", tags=["audio"])


@router.post("/upload")
async def upload_audio(
    file: UploadFile,
    uuid: UUID4,
    folder: str = "audio",
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Upload audio file to MinIO and save metadata to database"""
    try:
        if file.content_type is None:
            raise HTTPException(status_code=400, detail="File type not specified")
        if file.filename is None:
            raise HTTPException(status_code=400, detail="File name not specified")
        # Validate audio file type
        if not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="Only audio files are allowed")

        async def upload():
            if file.content_type is None:
                raise HTTPException(status_code=400, detail="File type not specified")
            if file.filename is None:
                raise HTTPException(status_code=400, detail="File name not specified")
            # Validate audio file type
            if not file.content_type.startswith("audio/"):
                raise HTTPException(
                    status_code=400, detail="Only audio files are allowed"
                )
            # Upload to MinIO
            object_name = await minio_service.upload_file(
                file_data=file.file,
                size=file.size,
                filename=file.filename,
                content_type=file.content_type,
                folder=folder,
            )

            # Load audio file and extract metadata
            y, sr = librosa.load(file.file, sr=None)
            audio_length = librosa.get_duration(y=y, sr=sr)

            await AudioQueries(session=db).update_audio(
                audio_id=uuid,
                audio_length=audio_length,
                status=StatusEnum.available,
            )

        background_tasks.add_task(upload)

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{audio_id}")
async def download_audio(audio_id: UUID4, db: AsyncSession = Depends(get_db)):
    """Download audio file by UUID"""
    # Get audio metadata from database
    audio_record = (
        await db.scalars(select(Audio).where(Audio.id == audio_id).limit(1))
    ).first()
    if not audio_record:
        raise HTTPException(status_code=404, detail="Audio file not found")

    # Extract object name from URL
    # URL format: http://minio:9000/{bucket}/{object_name}
    object_name = str(audio_record.url)

    # Download from MinIO
    file_data = await minio_service.download_file(object_name)

    return StreamingResponse(
        BytesIO(file_data),
        media_type="audio/wav",  # or determine from file extension
        headers={
            "Content-Disposition": f"attachment; filename={audio_record.file_name}"
        },
    )


@router.get("/download/{audio_id}/url")
async def download_url(audio_id: str):
    return await minio_service.get_file_url(audio_id)


@router.get("/url/{audio_id}")
async def get_audio_url(
    audio_id: UUID4, expires: int = 3600, db: AsyncSession = Depends(get_db)
):
    """Get presigned URL for audio file access"""
    audio_record = await db.scalar(select(Audio).where(Audio.id == audio_id).limit(1))
    if not audio_record:
        raise HTTPException(status_code=404, detail="Audio file not found")

    print(audio_record.url)
    # Extract object name from stored URL
    object_name = audio_record.url.split(f"{minio_service.bucket_name}/")[-1]
    print(object_name)

    url = await minio_service.get_file_url(object_name, expires)
    print(url)

    return {"url": url, "expires_in": expires}


@router.delete("/{audio_id}")
async def delete_audio(audio_id: UUID4, db: AsyncSession = Depends(get_db)):
    """Delete audio file from both MinIO and database"""
    audio_record = await db.scalar(select(Audio).where(Audio.id == audio_id).limit(1))
    if not audio_record:
        raise HTTPException(status_code=404, detail="Audio file not found")

    # Extract object name from stored URL
    object_name = audio_record.url.split(f"{minio_service.bucket_name}/")[-1]

    # Delete from MinIO
    success = await minio_service.delete_file(object_name)

    if success:
        await db.delete(audio_record)
        return {"message": "Audio file deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete audio file")
