from typing import List, Optional

from pydantic import BaseModel, Field

class IngestResponse(BaseModel):
    indexed_count: int
    index_name: str
    source_file: str

class FileIngestResponse(BaseModel):
    indexed_count: int
    index_name: str
    file_name: str
    file_type: str
    documents_processed: int

class BatchIngestResponse(BaseModel):
    total_files_processed: int
    total_documents_indexed: int
    index_name: str
    files_summary: List[dict] = Field(default_factory=list)
    errors: Optional[List[str]] = Field(default_factory=list)
    
class IngestRequest(BaseModel):
    directory_path: str = Field(default="data", description="Directory path to ingest files from")
    file_types: Optional[List[str]] = Field(default=None, description="File types to process (pdf, csv)")
    recursive: bool = Field(default=False, description="Whether to search subdirectories recursively")