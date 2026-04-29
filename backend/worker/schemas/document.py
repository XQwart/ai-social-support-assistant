from pydantic import BaseModel


class ParsedDocument(BaseModel):
    source_id: int
    source_url: str
    source_name: str | None = None
    text: str


class DocumentChunkCreate(BaseModel):
    source_id: int
    source_url: str
    source_name: str | None = None
    chunk_index: int
    text: str


class StoredDocumentChunk(BaseModel):
    id: int
    source_id: int
    source_url: str
    source_name: str | None = None
    chunk_index: int
    text: str


class EmbeddedDocumentChunk(BaseModel):
    id: int
    source_id: int
    source_url: str
    source_name: str | None = None
    chunk_index: int
    text: str
    vector: list[float]


class DiscoveredLink(BaseModel):
    source_id: int
    url: str
    depth: int
    document_type: str  # html, pdf, doc, docx, xls, xlsx, odt, ods, rtf


class GeneratedChunkQuestion(BaseModel):
    chunk_id: int
    source_id: int
    source_url: str
    source_name: str | None = None
    chunk_index: int
    text: str


class EmbeddedChunkQuestion(BaseModel):
    chunk_id: int
    source_id: int
    source_url: str
    source_name: str | None = None
    chunk_index: int
    text: str
    vector: list[float]
