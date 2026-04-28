from pydantic import BaseModel, Field


class AddTextToSourceRequest(BaseModel):
    source_url: str
    source_name: str | None = None

    region_code: str | None = Field(default=None, min_length=1, max_length=4)
    region_name: str | None = None

    place_of_work: str | None = None

    text: str = Field(..., min_length=50)


class UpdateChunkRequest(BaseModel):
    text: str = Field(..., min_length=50)
    place_of_work: str | None = None
