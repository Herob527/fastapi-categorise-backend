from __future__ import annotations
import io
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.responses import StreamingResponse
from database_handle.database import get_db
from database_handle.queries.bindings import get_all_bindings
from routes.finalize.classes import DirectoryModel, FinaliseConfigModel
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


@router.post("/", response_model=DirectoryModel)
async def finalise(
    config: FinaliseConfigModel,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    bindings = await get_all_bindings(db, skip_empty=config.omit_empty)
    service = minio_service.minio_service
    await service.remove_dir(str(OUTPUT_DIR))
    await service.delete_file(OUTPUT_ARCHIVE)

    categories = set(
        map(
            lambda x: x.category.name if x.category else config.uncategorized_name,
            bindings,
        )
    )
    indexed_categories = {v: k for k, v in dict(enumerate(categories, 1)).items()}

    base_dir = DirectoryModel(dir_name="files", files=[], is_dir=True)

    for item in service.list_files("temp"):
        if item.object_name is not None:
            base_dir.append(Path(item.object_name.replace("temp/", "")))

    background_tasks.add_task(
        process_and_create_zip, bindings, config, indexed_categories
    )

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
