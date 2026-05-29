from pydantic import BaseModel, Field


class ParsedDocument(BaseModel):
    source_id: int
    source_url: str
    text: str
    source_name: str | None = None
    place_of_work: str | None = None


class DocumentChunkCreate(ParsedDocument):
    chunk_index: int


class StoredDocumentChunk(DocumentChunkCreate):
    id: int


class ChunkWithQuestions(StoredDocumentChunk):
    questions: list[str] = Field(default_factory=list)


class EmbeddedChunkQuestion(BaseModel):
    vector: list[float]


class EmbeddedChunkForIndex(ChunkWithQuestions):
    vector: list[float]
    questions: list[EmbeddedChunkQuestion] = Field(default_factory=list)


class DiscoveredLink(BaseModel):
    source_id: int
    url: str
    depth: int
    document_type: str  # html, pdf, doc, docx, xls, xlsx, odt, ods, rtf
