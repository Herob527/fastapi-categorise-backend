from pathlib import Path

OUTPUT_DIR = Path("temp")

OUTPUT_ARCHIVE = "categorized_files.zip"

EMPTY_TEXT_TAG = "<empty-text>"


class PathItem:
    def __init__(self, name: str):
        self.name = name

    def as_path(self, *parts: Path | str) -> Path:
        return Path(*parts, self.name)

    def as_string(self, *parts: str) -> str:
        return str(Path(*parts, self.name)) if parts else self.name


TranscriptFile = PathItem("transcript.txt")
WavsDir = PathItem("wavs")
