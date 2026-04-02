from pydantic import BaseModel


class Document(BaseModel):
    source_id: int
    source_url: str
    source_name: str
    region_code: str
    text: str | None


class DocumentChunkCreate(BaseModel):
    source_id: int
    source_url: str
    source_name: str
    region_code: str
    chunk_index: int
    text: str


class StoredDocumentChunk(BaseModel):
    id: int
    source_id: int
    source_url: str
    source_name: str
    region_code: str
    chunk_index: int
    text: str
