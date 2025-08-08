import os
import shutil
from typing import Optional
from uuid import UUID
from utils.file_utils import clone_repository, extract_zip, find_code_files, read_file_content
from models.project import ProjectCreate
from models.file import FileCreate
from db import db
from config import settings


class Ingester:
    def __init__(self):
        self.workspace_dir = settings.workspace_dir
    
    async def ingest_project(self, project_data: ProjectCreate) -> dict:
        """Ingest a project from git repo or zip file."""
        project = await db.create_project(project_data)
        project_dir = None
        
        try:
            # Handle git repository
            if project_data.repo_url:
                project_dir = await clone_repository(project_data.repo_url, str(project.project_id))
            
            # Handle zip file
            elif project_data.zip_file:
                project_dir = await extract_zip(project_data.zip_file, str(project.project_id))
            
            else:
                raise ValueError("Either repo_url or zip_file must be provided")
            
            # Find and register all code files
            code_files = await find_code_files(project_dir)
            files_created = []
            
            for file_path in code_files:
                language = self._get_language_from_path(file_path)
                file_data = FileCreate(
                    project_id=project.project_id,
                    file_path=file_path,
                    language=language
                )
                file_record = await db.create_file(file_data)
                files_created.append(file_record)
            
            return {
                "project": project,
                "files_created": len(files_created),
                "project_dir": project_dir
            }
            
        except Exception as e:
            # Clean up on failure
            if project_dir and os.path.exists(project_dir):
                shutil.rmtree(project_dir)
            raise e
    
    def _get_language_from_path(self, file_path: str) -> str:
        """Get programming language from file path."""
        from utils.file_utils import get_file_extension
        return get_file_extension(file_path)
    
    async def get_project_files(self, project_id: UUID) -> list:
        """Get all files for a project."""
        return await db.get_files_by_project(project_id)
    
    async def read_project_file(self, project_id: UUID, file_path: str) -> str:
        """Read content of a specific file in a project."""
        project_dir = os.path.join(self.workspace_dir, str(project_id))
        full_path = os.path.join(project_dir, file_path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        return await read_file_content(full_path)


# Global ingester instance
ingester = Ingester()
