from pydantic import BaseModel, ConfigDict


class SourceRegionInfo(BaseModel):
    id: int
    code: str
    name: str

    model_config = ConfigDict(frozen=True)
