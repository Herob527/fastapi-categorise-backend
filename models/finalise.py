
import re
from typing import List, Union
from pydantic import BaseModel, Field, field_validator


class FileModel(BaseModel):
    file_name: str


class DirectoryModel(BaseModel):
    dir_name: str
    files: List[Union["FileModel", "DirectoryModel"]] = []


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
