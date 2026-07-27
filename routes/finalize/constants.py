from pathlib import Path

OUTPUT_DIR = Path("temp")

OUTPUT_ARCHIVE = "categorized_files.zip"

EMPTY_TEXT_TAG = "<empty-text>"


class TranscriptFile:
    name = "transcript.txt"

    @classmethod
    def as_path(cls, *parts: Path | str) -> Path:
        return Path(*parts, cls.name)

    @classmethod
    def as_string(cls, *parts: str) -> str:
        return str(Path(*parts, cls.name)) if parts else cls.name


class WavsDir:
    name = "wavs"

    @classmethod
    def as_path(cls, *parts: Path | str) -> Path:
        return Path(*parts, cls.name)

    @classmethod
    def as_string(cls, *parts: str) -> str:
        return str(Path(*parts, cls.name)) if parts else cls.name
