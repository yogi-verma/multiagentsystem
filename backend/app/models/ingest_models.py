from pydantic import BaseModel


class IngestResponse(BaseModel):
    indexed_count: int
    index_name: str
    source_file: str