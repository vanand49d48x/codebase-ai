from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class ProjectCreate(BaseModel):
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    repo_url: Optional[str] = Field(None, description="Git repository URL")
    language: Optional[str] = Field(None, description="Primary programming language")
    zip_file: Optional[str] = Field(None, description="Path to uploaded zip file")


class Project(BaseModel):
    project_id: UUID = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    repo_url: Optional[str] = Field(None, description="Git repository URL")
    language: Optional[str] = Field(None, description="Primary programming language")
    created_at: datetime = Field(..., description="Project creation timestamp")
    
    class Config:
        from_attributes = True
