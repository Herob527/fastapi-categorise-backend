from __future__ import annotations
import concurrent.futures
import asyncio
import re
from pathlib import Path
from typing import Dict, List, Literal, TypedDict, Union, cast

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio.session import AsyncSession

from database_handle.database import get_db
from database_handle.models.bindings import BindingModel
from database_handle.queries.bindings import get_all_bindings
from services import minio_service

__all__ = ["router"]

output_dir = Path("temp")

EMPTY_TEXT_TAG = "<empty-text>"


class FileModel(BaseModel):
    file_name: str
    is_dir: Literal[False]


class DirectoryModel(BaseModel):
    dir_name: str
    is_dir: Literal[True]
    files: List[Union[FileModel, DirectoryModel]]

    def __init__(self, **data):
        super().__init__(**data)

    def _append(self, dir: DirectoryModel, file: FileModel):
        dir.files.append(file)

    def append(self, file: Path, level=0, dir: DirectoryModel | None = None):
        file_name = file.name
        path_part = file.parts[level]
        files_container = self.files if dir is None else dir.files
        if path_part.endswith((".wav", ".txt")):
            self._append(dir or self, FileModel(file_name=file_name, is_dir=False))
            return

        def dirs_on_level():
            return (
                cast(DirectoryModel, x)
                for x in files_container
                if isinstance(x, DirectoryModel)
            )

        def dir_names_on_level():
            return map(lambda x: x.dir_name, dirs_on_level())

        if path_part not in dir_names_on_level():
            files_container.append(
                DirectoryModel(dir_name=path_part, files=[], is_dir=True)
            )

        for i in dirs_on_level():
            if i.dir_name == path_part:
                self.append(file, level + 1, i)
                break


DirectoryModel.model_rebuild()


class FinaliseConfigModel(BaseModel):
    omit_empty: bool = True
    line_format: str = Field(
        "{file}|{text}",
        description="""\r
    supported keys:\r
        {file} - file name\r
        {category} - category name\r
        {category_index} - category index (created automatically)\r
        {text} - text of entry\r
        {duration} - duration of audio in seconds\r
    """,
    )
    divide_by_category: bool = True
    category_to_lower: bool = False
    category_space_replacer: str = " "
    export_transcript: bool = True
    uncategorized_name: str

    @field_validator("line_format")
    def validate_line_format(cls, v):
        format_keys = re.findall(r"\{(.*?)\}", v)

        expected_keys = ["file", "duration", "category", "category_index", "text"]

        for i in format_keys:
            if i not in expected_keys:
                raise ValueError(
                    f"Unsupported key '{i}' in line_format.\nSupported keys: {expected_keys}"
                )

        return v


router = APIRouter(
    tags=["Finalise"],
    prefix="/finalise",
    responses={404: {"description": "Not found"}},
)


class TranscriptEntry(TypedDict):
    lines: list[str]
    path: Path


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
                output_dir,
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
            else Path(output_dir)
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


@router.post("/", response_model=DirectoryModel)
async def finalise(config: FinaliseConfigModel, db: AsyncSession = Depends(get_db)):
    bindings = await get_all_bindings(db, skip_empty=config.omit_empty)
    service = minio_service.minio_service
    await service.remove_dir(str(output_dir))

    def get_paths():
        for b in bindings:
            subdir = Path(
                output_dir,
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
        sem = asyncio.Semaphore(20)  # Allow up to 20 concurrent copies

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
        base_dir.append(Path(item.replace("temp/", "")))

    return base_dir
