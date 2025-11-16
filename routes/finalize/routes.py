from __future__ import annotations
import asyncio
from os import cpu_count
from pathlib import Path
import zipfile
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio.session import AsyncSession
from database_handle.database import get_db
from database_handle.queries.bindings import get_all_bindings
from routes.finalize.classes import DirectoryModel, FinaliseConfigModel
from routes.finalize.constants import OUTPUT_ARCHIVE, OUTPUT_DIR
from routes.finalize.utils import process_transcript
from services import minio_service

__all__ = ["router"]

DirectoryModel.model_rebuild()

router = APIRouter(
    tags=["Finalise"],
    prefix="/finalise",
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=DirectoryModel)
async def finalise(config: FinaliseConfigModel, db: AsyncSession = Depends(get_db)):
    bindings = await get_all_bindings(db, skip_empty=config.omit_empty)
    service = minio_service.minio_service
    await service.remove_dir(str(OUTPUT_DIR))
    await service.delete_file(OUTPUT_ARCHIVE)

    def get_paths():
        for b in bindings:
            subdir = Path(
                OUTPUT_DIR,
            )
            if config.divide_by_category:
                subdir = Path(
                    subdir,
                    b.category.name if b.category else config.uncategorized_name,
                    "files",
                )
            else:
                subdir = Path(subdir, "files")

            yield (b.audio.url, Path(subdir, b.audio.file_name))

    async def perform_copy():
        sem = asyncio.Semaphore(
            (cpu_count() or 6) * 5
        )  # Allow up to 20 concurrent copies

        async def limited_copy(url, subdir):
            async with sem:
                await service.copy_file(url, str(subdir))

        await asyncio.gather(
            *(limited_copy(url, subdir) for url, subdir in get_paths())
        )

    await perform_copy()

    categories = set(
        map(
            lambda x: x.category.name if x.category else config.uncategorized_name,
            bindings,
        )
    )
    indexed_categories = {v: k for k, v in dict(enumerate(categories, 1)).items()}

    transcript_data = process_transcript(bindings, config, indexed_categories)

    for i in transcript_data:
        lines = "".join(i["lines"])
        path = i["path"]
        service.append_to_text(str(path), lines)

    base_dir = DirectoryModel(dir_name="files", files=[], is_dir=True)

    for item in service.list_files("temp"):
        if item.object_name is not None:
            base_dir.append(Path(item.object_name.replace("temp/", "")))

    return base_dir


@router.get("/{object_id}", response_model=str)
async def get_dir(object_id: str):
    return await minio_service.minio_service.get_file_url(object_id)


@router.get(
    "/download/zip",
    responses={
        200: {
            "content": {"application/zip": {}},
            "description": "Returns a zip file containing all finalized files",
        },
        404: {"description": "No finalized files found"},
    },
)
async def download_finalized_zip():
    """
    Downloads all finalized files from the temp directory as a zip file.
    """

    service = minio_service.minio_service

    # List all files in the temp directory
    files = list(service.list_files(str(OUTPUT_DIR)))

    # Check if there are any files to download
    if not files or len(files) == 0:
        raise HTTPException(
            status_code=404,
            detail="No finalized files found. Please run the finalize endpoint first.",
        )

    # Create a BytesIO object to hold the zip file in memory
    zip_buffer = io.BytesIO()

    # Create a zip file
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Download and add each file to the zip
        for item in files:
            if item.object_name is not None:
                # Download the file content
                file_content = await service.download_file(item.object_name)

                # Remove the "temp/" prefix from the path for the zip archive
                archive_path = item.object_name.replace(f"{OUTPUT_DIR}/", "")

                # Add file to zip
                zip_file.writestr(archive_path, file_content)

    # Seek to the beginning of the BytesIO buffer
    zip_buffer.seek(0)

    # Return the zip file as a streaming response
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={OUTPUT_ARCHIVE}"},
    )
