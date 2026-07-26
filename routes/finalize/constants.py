from pathlib import Path

OUTPUT_DIR = Path("temp")

OUTPUT_ARCHIVE = "categorized_files.zip"

EMPTY_TEXT_TAG = "<empty-text>"


class TranscriptFile:
    name = "transcript.txt"

    @classmethod
    def as_path(cls, *parts: Path | str) -> Path:
        return Path(*parts, cls.name)
