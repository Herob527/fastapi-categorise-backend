from __future__ import annotations

import asyncio
import io
import zipfile
from os import cpu_count
from pathlib import Path
from typing import Dict

from fastapi import HTTPException

from database_handle.models.bindings import BindingModel
from routes.finalize.classes import (
    DirectoryModel,
    FileModel,
    FinaliseConfigModel,
    TranscriptEntry,
)
from routes.finalize.constants import EMPTY_TEXT_TAG, OUTPUT_ARCHIVE, OUTPUT_DIR
from services import minio_service


def process_category(category: str, config: FinaliseConfigModel):
    res = category.replace(" ", config.category_space_replacer)
    if config.category_to_lower:
        res = res.lower()
    return res


def process_line(
    binding: BindingModel,
    config: FinaliseConfigModel,
    indexed_categories: Dict[str, int] | None = None,
):
    category_index = (
        indexed_categories.get(
            binding.category.name
            if binding.category is not None
            else config.uncategorized_name
        )
        if indexed_categories
        else 0
    )
    formatted_line = config.line_format.format(
        file=f"files/{binding.audio.file_name}",
        text=(
            binding.text.text
            if str(binding.text.text).strip() != ""
            else EMPTY_TEXT_TAG
        ),
        duration=binding.audio.audio_length,
        category=process_category(
            str(
                binding.category.name if binding.category else config.uncategorized_name
            ),
            config,
        ),
        category_index=category_index,
    )
    return f"{formatted_line}\n"


def process_transcript(
    bindings: list[BindingModel],
    config: FinaliseConfigModel,
    indexed_categories: Dict[str, int] | None = None,
):
    res: Dict[str, TranscriptEntry] = dict()
    for binding in bindings:
        target_dir = (
            Path(
                OUTPUT_DIR,
                process_category(
                    (
                        str(binding.category.name)
                        if binding.category is not None
                        else config.uncategorized_name
                    ),
                    config,
                ),
            )
            if config.divide_by_category
            else Path(OUTPUT_DIR)
        )

        output_file = Path(target_dir, "transcript.txt")
        current_category = (
            str(binding.category.name)
            if binding.category is not None
            else config.uncategorized_name
        )

        current_value = res.get(current_category)
        text_to_insert = process_line(binding, config, indexed_categories)
        if current_value is None:
            res[current_category] = {
                "lines": [text_to_insert],
                "path": output_file,
            }
        else:
            res[current_category]["lines"].append(text_to_insert)

    return res.values()


def convert_tree_to_pydantic(root: Path):
    files = []
    dirs = []

    for i in root.glob("*"):
        if i.is_dir():
            dirs.append(convert_tree_to_pydantic(i))
        else:
            files.append(FileModel(file_name=i.name, is_dir=False))
    combined = [*files, *dirs]
    return DirectoryModel(dir_name=root.name, files=combined, is_dir=True)


def get_paths(bindings: list[BindingModel], config: FinaliseConfigModel):
    """Generate paths for all audio files based on configuration."""
    for b in bindings:
        subdir = Path(OUTPUT_DIR)
        if config.divide_by_category:
            subdir = Path(
                subdir,
                b.category.name if b.category else config.uncategorized_name,
                "files",
            )
        else:
            subdir = Path(subdir, "files")

        yield (b.audio.url, Path(subdir, b.audio.file_name))


async def perform_copy(bindings: list[BindingModel], config: FinaliseConfigModel):
    """Copy all audio files to their destination paths with concurrency control."""
    service = minio_service.minio_service
    sem = asyncio.Semaphore((cpu_count() or 6) * 5)

    async def limited_copy(url, subdir):
        async with sem:
            await service.copy_file(url, str(subdir))

    await asyncio.gather(
        *(limited_copy(url, subdir) for url, subdir in get_paths(bindings, config))
    )


async def create_zip():
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

    size = zip_buffer.getbuffer().nbytes
    zip_buffer.seek(0)

    await minio_service.minio_service.upload_file(zip_buffer, OUTPUT_ARCHIVE, size)


async def process_and_create_zip(
    bindings: list[BindingModel],
    config: FinaliseConfigModel,
    indexed_categories: Dict[str, int],
):
    service = minio_service.minio_service

    # Step 1: Perform file copying
    await perform_copy(bindings, config)

    # Step 2: Process and write transcripts
    transcript_data = process_transcript(bindings, config, indexed_categories)
    for i in transcript_data:
        lines = "".join(i["lines"])
        path = i["path"]
        service.append_to_text(str(path), lines)

    # Step 3: Create zip archive
    await create_zip()
