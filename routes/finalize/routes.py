"""
Todo:
    - Create endpoint for scheduling creation of zip file in the background
    - Create endpoint for attempting fetching data and if it's not finished, return 202
"""

from __future__ import annotations
import io
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.responses import StreamingResponse
from database_handle.database import get_db
from database_handle.models.bindings import BindingModel
from database_handle.queries.bindings import get_all_bindings
from routes.finalize.classes import DirectoryModel, FileModel, FinaliseConfigModel
from routes.finalize.constants import OUTPUT_ARCHIVE, OUTPUT_DIR
from routes.finalize.utils import process_and_create_zip
from services import minio_service

__all__ = ["router"]

DirectoryModel.model_rebuild()

router = APIRouter(
    tags=["Finalise"],
    prefix="/finalise",
    responses={404: {"description": "Not found"}},
)


@router.post("/generate_preview", response_model=DirectoryModel)
async def finalise(
    config: FinaliseConfigModel,
    db: AsyncSession = Depends(get_db),
):
    bindings = await get_all_bindings(db, skip_empty=config.omit_empty)
    category_mapping: dict[str, list[BindingModel]] = {}

    for binding in bindings:
        category_name = (
            binding.category.name if binding.category else config.uncategorized_name
        )

        if category_mapping.get(category_name) is None:
            category_mapping[category_name] = []
        else:
            category_mapping[category_name].append(binding)

    files: list[FileModel | DirectoryModel] = []

    for category, bindings in category_mapping.items():
        directory = DirectoryModel(dir_name=category, files=[], is_dir=True)
        for binding in bindings:
            directory.append(file=Path(binding.audio.file_name))
        directory.append(file=Path("transcript.txt"))
        files.append(directory)

    base_dir = DirectoryModel(dir_name="files", files=files, is_dir=True)

    return base_dir


@router.get("/download/zip", response_model=str)
async def download_finalized_zip():
    """
    Downloads all finalized files from the temp directory as a zip file.
    """

    service = minio_service.minio_service

    print("pre-download")
    zip_file = await service.download_file(OUTPUT_ARCHIVE)
    print("post-download")
    zip_bytes = io.BytesIO(zip_file)
    print("post-bytes")
    # Return the zip file as a streaming response
    return StreamingResponse(zip_bytes, media_type="application/zip")
