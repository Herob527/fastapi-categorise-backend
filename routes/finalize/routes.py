"""
Todo:
    - Create endpoint for scheduling creation of zip file in the background
    - Create endpoint for attempting fetching data and if it's not finished, return 202
"""

from __future__ import annotations
import io
from pathlib import Path
from typing import TypedDict
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.responses import StreamingResponse
from database_handle.database import get_db
from database_handle.models.bindings import BindingModel
from database_handle.models.exports import ExportStatus, Exports
from database_handle.queries.bindings import get_all_bindings
from database_handle.queries.exports import ExportsQueries, get_exports_queries
from routes.finalize.classes import DirectoryModel, FileModel, FinaliseConfigModel
from routes.finalize.constants import OUTPUT_ARCHIVE
from services import minio_service


class CategoryData(TypedDict):
    original_name: str
    bindings: list[BindingModel]


__all__ = ["router"]

DirectoryModel.model_rebuild()

router = APIRouter(
    tags=["Finalise"],
    prefix="/finalise",
    responses={404: {"description": "Not found"}},
)


@router.post("/generate_preview", response_model=DirectoryModel)
async def generate_preview(
    config: FinaliseConfigModel,
    db: AsyncSession = Depends(get_db),
):
    bindings = await get_all_bindings(db, skip_empty=config.omit_empty)
    category_mapping: dict[str, CategoryData] = {}

    for binding in bindings:
        original_name = (
            binding.category.name if binding.category else config.uncategorized_name
        )
        # Process category name: replace whitespace with underscores
        processed_name = original_name.replace(" ", "_")

        if category_mapping.get(processed_name) is None:
            category_mapping[processed_name] = {
                "original_name": original_name,
                "bindings": [],
            }

        category_mapping[processed_name]["bindings"].append(binding)

    files: list[FileModel | DirectoryModel] = []

    for processed_name, data in category_mapping.items():
        directory = DirectoryModel(
            dir_name=processed_name,
            files=[],
            is_dir=True,
            original_name=data["original_name"],
        )
        for binding in data["bindings"]:
            directory.append(file=Path(binding.audio.file_name))
        directory.append(file=Path("transcript.txt"))
        files.append(directory)

    base_dir = DirectoryModel(dir_name="files", files=files, is_dir=True)

    return base_dir


@router.get("/schedule/{category}", response_model=None)
async def schedule_finalise(
    category: str | None = None,
    queries: ExportsQueries = Depends(get_exports_queries),
    backgroundTasks: BackgroundTasks = BackgroundTasks(),
):
    id = category or "all"
    was_scheduled = await queries.exists(id)
    if was_scheduled:
        raise HTTPException(status_code=423, detail="Already scheduled")

    await queries.schedule(id)

    async def schedule_task():
        from database_handle.database import get_sessionmanager

        async with get_sessionmanager().session() as bg_session:
            _queries = ExportsQueries(session=bg_session)
            await _queries.set_status(id, ExportStatus.IN_PROGRESS)

    backgroundTasks.add_task(schedule_task)


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
