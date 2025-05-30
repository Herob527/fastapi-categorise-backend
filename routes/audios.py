from uuid import uuid4
from pprint import pprint
from fastapi import APIRouter, UploadFile, HTTPException, Depends
from fastapi.responses import StreamingResponse
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
import librosa
from pydantic import UUID4
from sqlalchemy.orm.query import sql
from sqlalchemy.sql.expression import select
from database_handle.database import get_db
from database_handle.models.audios import Audio, AudioModel
from services.minio_service import minio_service

router = APIRouter(prefix="/audio", tags=["audio"])


@router.post("/upload", response_model=AudioModel)
async def upload_audio(
    file: UploadFile,
    uuid: UUID4 = uuid4(),
    folder: str = "audio",
    db: AsyncSession = Depends(get_db),
) -> AudioModel:
    """Upload audio file to MinIO and save metadata to database"""
    try:
        if file.content_type is None:
            raise HTTPException(status_code=400, detail="File type not specified")
        if file.filename is None:
            raise HTTPException(status_code=400, detail="File name not specified")
        # Validate audio file type
        if not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="Only audio files are allowed")

        # Upload to MinIO
        object_name = await minio_service.upload_file(
            file_data=file.file,
            filename=file.filename,
            content_type=file.content_type,
            folder=folder,
        )

        # Generate MinIO URL for the uploaded file
        file_url = (
            f"http://{minio_service.endpoint}/{minio_service.bucket_name}/{object_name}"
        )

        # Download file temporarily to analyze audio properties
        file_data = await minio_service.download_file(object_name)

        # Analyze audio file properties using librosa
        # Save to temporary file for librosa processing
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(file_data)
            temp_file_path = temp_file.name

        try:
            # Load audio file and extract metadata
            y, sr = librosa.load(temp_file_path, sr=None)
            audio_length = librosa.get_duration(y=y, sr=sr)

            # Get number of channels (librosa loads as mono by default, so check original)
            import soundfile as sf

            info = sf.info(temp_file_path)
            channels = info.channels
            frequency = info.samplerate
        finally:
            # Clean up temporary file
            import os

            os.unlink(temp_file_path)

        # Save metadata to database with your existing Audio model
        audio_record = Audio(
            id=uuid,
            url=file_url,
            file_name=file.filename,
            channels=channels,
            frequency=frequency,
            audio_length=audio_length,
        )

        return AudioModel.from_orm(audio_record)

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
    object_name = audio_record.url.split(f"{minio_service.bucket_name}/")[-1]

    # Download from MinIO
    file_data = await minio_service.download_file(object_name)

    return StreamingResponse(
        BytesIO(file_data),
        media_type="audio/wav",  # or determine from file extension
        headers={
            "Content-Disposition": f"attachment; filename={audio_record.file_name}"
        },
    )


@router.get("/url/{audio_id}")
async def get_audio_url(
    audio_id: UUID4, expires: int = 3600, db: AsyncSession = Depends(get_db)
):
    """Get presigned URL for audio file access"""
    audio_record = (
        await db.execute(select(Audio).filter(Audio.id == audio_id))
    ).first()
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
    audio_record = (
        await db.execute(select(Audio).where(Audio.id == audio_id).limit(1))
    ).first()
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
