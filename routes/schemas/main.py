from pydantic import UUID4, BaseModel


class BindingsModel(BaseModel):
    id: UUID4
    text_id: UUID4
    category_id: UUID4
    audio_id: UUID4


class CategoriesModel(BaseModel):
    id: UUID4
    name: str


class AudiosModel(BaseModel):
    channels: int
    id: UUID4
    audio_length: float
    file_name: str
    frequency: int
    url: str


class TextsModel(BaseModel):
    text: str
    id: UUID4


class BindingsResponse(BaseModel):
    Bindings: BindingsModel
    Categories: CategoriesModel
    Audios: AudiosModel
    Texts: TextsModel
