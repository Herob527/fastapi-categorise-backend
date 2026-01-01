from __future__ import annotations
import re
from pathlib import Path
from typing import List, Literal, TypedDict, Union, cast

from pydantic import BaseModel, Field, field_validator


class FileModel(BaseModel):
    file_name: str
    is_dir: Literal[False]


class DirectoryModel(BaseModel):
    dir_name: str
    is_dir: Literal[True]
    files: List[Union[FileModel, DirectoryModel]]
    original_name: str | None = None
    category_id: str | None = None

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


class TranscriptEntry(TypedDict):
    lines: list[str]
    path: Path
