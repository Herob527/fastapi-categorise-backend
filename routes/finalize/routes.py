"""
Todo:
    - Create endpoint for scheduling creation of zip file in the background
    - Create endpoint for attempting fetching data and if it's not finished, return 202
"""

from __future__ import annotations
import io
from pathlib import Path
from typing import TypedDict
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.responses import StreamingResponse
from database_handle.database import get_db
from database_handle.models.bindings import BindingModel
from database_handle.models.exports import ExportModel, ExportStatus
from database_handle.models.pagination import Paginated
from database_handle.queries.bindings import get_all_bindings
from database_handle.queries.exports import ExportsQueries, get_exports_queries
from routes.finalize.classes import DirectoryModel, FileModel, FinaliseConfigModel
from routes.finalize.constants import OUTPUT_ARCHIVE
from routes.finalize.utils import process_line
from services import minio_service
from uuid import uuid4
from tempfile import TemporaryFile
from pprint import pprint


class CategoryData(TypedDict):
    id: str | None
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
        category_id = str(binding.category.id) if binding.category else None
        if category_id is None:
            if category_mapping.get(config.uncategorized_name) is None:
                category_mapping[config.uncategorized_name] = CategoryData(
                    id=None,
                    original_name=config.uncategorized_name,
                    bindings=[binding],
                )
            else:
                category_mapping[config.uncategorized_name]["bindings"].append(binding)
            continue
        category_name = (
            binding.category.name if binding.category else config.uncategorized_name
        )

        if category_mapping.get(category_id) is None:
            category_mapping[category_id] = CategoryData(
                id=category_id,
                original_name=category_name,
                bindings=[],
            )

        category_mapping[category_id]["bindings"].append(binding)

    files: list[FileModel | DirectoryModel] = []
    print(category_mapping)

    if config.divide_by_category:
        for category_id, data in category_mapping.items():
            # Process category name: replace whitespace with underscores for directory name
            processed_name = data["original_name"].replace(" ", "_")
            directory = DirectoryModel(
                dir_name=processed_name,
                files=[],
                is_dir=True,
                original_name=data["original_name"],
                category_id=data["id"],
            )
            for binding in data["bindings"]:
                dir = directory.get_or_create_dir("wavs")
                dir.append(file=Path(binding.audio.file_name))
            directory.append(file=Path("transcript.txt"))
            files.append(directory)
    else:
        directory = DirectoryModel(
            dir_name="main",
            files=[],
            is_dir=True,
            original_name=None,
            category_id=None,
        )
        for binding in bindings:
            directory.append(file=Path(binding.audio.file_name))
        directory.append(file=Path("transcript.txt"))
        files.append(directory)

    base_dir = DirectoryModel(
        dir_name="wavs", files=files, is_dir=True, original_name=None
    )

    return base_dir


class ScheduleData(BaseModel):
    categories: list[str | None] | None = None


async def schedule_task(
    id: str,
    config: FinaliseConfigModel,
    categories: list[str | None] = [],
):
    from database_handle.database import get_sessionmanager
    import zipfile

    async with get_sessionmanager().session() as bg_session:
        _queries = ExportsQueries(session=bg_session)
        await _queries.set_status(id, ExportStatus.IN_PROGRESS)

        with TemporaryFile("wb+") as temp:
            with zipfile.ZipFile(temp, mode="w", compression=zipfile.ZIP_STORED) as zf:
                if config.divide_by_category:
                    for category in categories:
                        res = await get_all_bindings(
                            bg_session,
                            category_id=category,
                            skip_empty=config.omit_empty,
                            include_none=category is None,
                        )
                        text_lines = []
                        category_name = config.uncategorized_name
                        for binding in res:
                            file = await minio_service.minio_service.download_file(
                                binding.audio.url
                            )
                            category_name = (
                                binding.category.name
                                if binding.category is not None
                                else config.uncategorized_name
                            )
                            zf.writestr(
                                f"{category_name}/wavs/{binding.audio.file_name}", file
                            )
                            text_lines.append(
                                process_line(binding, config, indexed_categories=None)
                            )

                        zf.writestr(
                            f"{category_name}/transcript.txt", "\n".join(text_lines)
                        )
                else:
                    res = await get_all_bindings(
                        bg_session,
                        skip_empty=config.omit_empty,
                        include_none=False,
                    )

                    text_lines = []
                    indexed_categories = list[str]()
                    for binding in res:
                        file = await minio_service.minio_service.download_file(
                            binding.audio.url
                        )
                        category_name = (
                            binding.category.name
                            if binding.category is not None
                            else config.uncategorized_name
                        )
                        if category_name not in indexed_categories:
                            indexed_categories.append(category_name)

                        zf.writestr(binding.audio.file_name, file)
                        text_lines.append(
                            process_line(
                                binding,
                                config,
                                indexed_categories={
                                    k: v for v, k in enumerate(indexed_categories)
                                },
                            )
                        )

                    zf.writestr("transcript.txt", "\n".join(text_lines))

            size = temp.tell()
            temp.seek(0)
            upload_name = f"{id}_{OUTPUT_ARCHIVE}"
            await minio_service.minio_service.upload_file(
                temp, upload_name, size, content_type="application/zip"
            )
            await _queries.set_archive_url(id, upload_name)
            await _queries.set_status(id, ExportStatus.COMPLETED)


@router.post("/schedule", response_model=None)
async def schedule_finalise(
    backgroundTasks: BackgroundTasks,
    config: FinaliseConfigModel,
    params: ScheduleData | None = None,
    queries: ExportsQueries = Depends(get_exports_queries),
):
    categories = params.categories if params is not None else None

    id = str(uuid4())
    await queries.schedule(
        id,
        categories,
    )

    backgroundTasks.add_task(
        schedule_task, id=id, categories=categories or [], config=config
    )


@router.get("/status", response_model=Paginated[ExportModel])
async def get_statuses(
    page: int = 0,
    limit: int = 20,
    queries: ExportsQueries = Depends(get_exports_queries),
):
    return await queries.get_paginated(page, limit)


@router.get("/download/{export_id}")
async def download_finalized_zip(
    export_id: str,
    queries: ExportsQueries = Depends(get_exports_queries),
):
    service = minio_service.minio_service
    archive_url = await queries.get_archive(export_id)
    zip_file = await service.download_file(archive_url)
    zip_bytes = io.BytesIO(zip_file)
    # Return the zip file as a streaming response
    return StreamingResponse(zip_bytes, media_type="application/zip")


@router.get("/delete-zip/{export_id}")
async def delete_finalized_zip(
    export_id: str,
    queries: ExportsQueries = Depends(get_exports_queries),
):
    service = minio_service.minio_service
    archive_url = await queries.get_archive(export_id)
    await service.delete_file(archive_url)
    await queries.delete_export(export_id)
