from pydantic import BaseModel


class ParsedDocument(BaseModel):
    source_id: int
    source_url: str
    source_name: str
    region_code: int
    text: str


class DocumentChunkCreate(BaseModel):
    source_id: int
    source_url: str
    source_name: str
    region_code: int
    chunk_index: int
    text: str


class StoredDocumentChunk(BaseModel):
    id: int
    source_id: int
    source_url: str
    source_name: str
    region_code: int
    chunk_index: int
    text: str


class EmbeddedDocumentChunk(BaseModel):
    id: int
    source_id: int
    source_url: str
    source_name: str
    region_code: int
    chunk_index: int
    text: str
    vector: list[float]
    access_level: str
