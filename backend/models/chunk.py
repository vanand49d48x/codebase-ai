from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class Chunk(BaseModel):
    chunk_id: Optional[UUID] = Field(None, description="Unique chunk identifier")
    project_id: UUID = Field(..., description="Project identifier")
    function_name: Optional[str] = Field(None, description="Function or class name")
    file_path: str = Field(..., description="File path relative to project root")
    language: str = Field(..., description="Programming language")
    chunk_type: str = Field(..., description="Type: function, class, or module")
    code: str = Field(..., description="Raw code content")
    summary: Optional[str] = Field(None, description="LLM-generated summary")
    combined: Optional[str] = Field(None, description="Summary + code combined")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    tokens: Optional[int] = Field(None, description="Token count")
    qdrant_id: Optional[str] = Field(None, description="Qdrant vector ID")
    tested: bool = Field(False, description="Whether chunk has tests")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    class Config:
        from_attributes = True


class ChunkCreate(BaseModel):
    project_id: UUID = Field(..., description="Project identifier")
    function_name: Optional[str] = Field(None, description="Function or class name")
    file_path: str = Field(..., description="File path relative to project root")
    language: str = Field(..., description="Programming language")
    chunk_type: str = Field(..., description="Type: function, class, or module")
    code: str = Field(..., description="Raw code content")
