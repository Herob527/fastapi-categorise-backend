from typing import Tuple

from pydantic import BaseModel

class DashboardModel(BaseModel):
    categories_count: int
    total_bindings_count: int
    category_with_most_bindings: Tuple[str, int]
    uncategorizaed_count: int
    categorized_count: int
    total_audio_duration: float
    filled_transcript_count: int
    empty_transcript_count: int
