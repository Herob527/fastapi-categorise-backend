from __future__ import annotations
from collections.abc import Callable, Sequence
from pathlib import Path
import re
from shutil import copy2, rmtree
from typing import Dict, List, Literal, Tuple, TypedDict, Union

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Row
from sqlalchemy.ext.asyncio.session import AsyncSession

from database_handle.database import get_db
from database_handle.models.audios import Audio
from database_handle.models.bindings import Binding, BindingModel
from database_handle.models.categories import Category
from database_handle.models.texts import Text
from database_handle.queries.bindings import get_all_bindings

__all__ = ["router"]

output_dir = Path("output")


EMPTY_TEXT_TAG = "<empty-text>"


class FileModel(BaseModel):
    file_name: str
    is_dir: Literal[False]


class DirectoryModel(BaseModel):
    dir_name: str
    is_dir: Literal[True]
    files: List[Union[FileModel, DirectoryModel]]


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
    uncaterized_name: str = "Uncategorized"

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


def prepare_path(dir: str):
    path = Path(output_dir, dir, "wavs")
    path.mkdir(parents=True, exist_ok=True)


def copy_file(
    source_file: str,
    target_file: str,
):
    copy2(source_file, target_file)


def write_transcript(
    lines: list[str],
    target_file: str,
    filter_predicate: Callable[[str], bool] = lambda _: True,
    post_processing: Callable[[str], str] = lambda x: x,
):
    """
    params:
        lines - list of lines
        target_file - path to write lines
        filter_predicate - filter out lines not matching criteria
        post_processing - transform line before writing one
    """
    with open(target_file, "a", encoding="utf-8") as f:
        f.writelines(map(post_processing, filter(filter_predicate, lines)))


router = APIRouter(
    tags=["Finalise"],
    prefix="/finalise",
    responses={404: {"description": "Not found"}},
)


def process_path(binding: BindingModel, config: FinaliseConfigModel):
    target_dir = (
        Path(
            output_dir,
            process_category(
                (
                    str(binding.category.name)
                    if binding.category is not None
                    else config.uncaterized_name
                ),
                config,
            ),
        )
        if config.divide_by_category
        else Path(output_dir)
    )

    output_file = Path(target_dir, "wavs", binding.audio.file_name)
    source_file = Path(binding.audio.url)

    if config.omit_empty and binding.text.text.strip() == "":
        return []

    return [source_file, output_file]


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
            else config.uncaterized_name
        )
        if indexed_categories
        else 0
    )
    formatted_line = config.line_format.format(
        file=binding.audio.file_name,
        text=(
            binding.text.text
            if str(binding.text.text).strip() != ""
            else EMPTY_TEXT_TAG
        ),
        duration=binding.audio.audio_length,
        category=process_category(
            str(binding.category.name if binding.category else config.uncaterized_name),
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
                        else config.uncaterized_name
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
            else config.uncaterized_name
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
    rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir()
    bindings = await get_all_bindings(db)
    categories = set(
        map(
            lambda x: x.replace(" ", config.category_space_replacer),
            map(
                lambda x: x.lower() if config.category_to_lower else x,
                map(
                    lambda x: (
                        x.category.name if x.category else config.uncaterized_name
                    ),
                    bindings,
                ),
            ),
        )
    )
    # TODO: Adjust finalise to use minio instead of local storage

    # audio_paths = map(lambda x: x.audio.url , bindings)
    #
    # indexed_categories = {v: k for k, v in dict(enumerate(categories, 1)).items()}
    #
    # transcript_data = process_transcript(bindings, config, indexed_categories)
    # used_category = categories if config.divide_by_category else []
    # for category in used_category:
    #     prepare_path(category)
    #
    # if len(used_category) == 0:
    #     Path(output_dir, "wavs").mkdir(parents=True, exist_ok=True)
    #
    # for audio_path in audio_paths:
    #     download
    #     copy_file(str(audio_path[0]), str(audio_path[1]))
    #
    # if config.export_transcript:
    #     for data in transcript_data:
    #         write_transcript(
    #             data["lines"],
    #             str(data["path"]),
    #             lambda x: x.find(EMPTY_TEXT_TAG) == -1 if config.omit_empty else True,
    #             lambda x: x.replace(EMPTY_TEXT_TAG, ""),
    #         )
    converted_tree = convert_tree_to_pydantic(output_dir)
    return converted_tree
