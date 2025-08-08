from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class File(BaseModel):
    file_id: Optional[UUID] = Field(None, description="Unique file identifier")
    project_id: UUID = Field(..., description="Project identifier")
    file_path: str = Field(..., description="File path relative to project root")
    language: str = Field(..., description="Programming language")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    class Config:
        from_attributes = True


class FileCreate(BaseModel):
    project_id: UUID = Field(..., description="Project identifier")
    file_path: str = Field(..., description="File path relative to project root")
    language: str = Field(..., description="Programming language")
