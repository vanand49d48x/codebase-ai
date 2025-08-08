import asyncpg
from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4
from config import settings
from models.project import Project, ProjectCreate
from models.chunk import Chunk, ChunkCreate
from models.file import File, FileCreate


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create database connection pool."""
        self.pool = await asyncpg.create_pool(settings.db_url)
        await self.create_tables()
    
    async def disconnect(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
    
    async def create_tables(self):
        """Create database tables if they don't exist."""
        async with self.pool.acquire() as conn:
            # Create projects table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    project_id UUID PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    repo_url TEXT,
                    language VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create files table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
                    file_path VARCHAR(500) NOT NULL,
                    language VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(project_id, file_path)
                )
            """)
            
            # Create chunks table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
                    function_name VARCHAR(255),
                    file_path VARCHAR(500) NOT NULL,
                    language VARCHAR(50) NOT NULL,
                    chunk_type VARCHAR(50) NOT NULL,
                    code TEXT NOT NULL,
                    summary TEXT,
                    combined TEXT,
                    tokens INTEGER,
                    qdrant_id VARCHAR(255),
                    tested BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    async def create_project(self, project_data: ProjectCreate) -> Project:
        """Create a new project."""
        project_id = uuid4()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO projects (project_id, name, description, repo_url, language)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
            """, project_id, project_data.name, project_data.description,
                 project_data.repo_url, project_data.language)
            
            return Project(**dict(row))
    
    async def get_project(self, project_id: UUID) -> Optional[Project]:
        """Get project by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM projects WHERE project_id = $1
            """, project_id)
            
            return Project(**dict(row)) if row else None
    
    async def list_projects(self) -> List[Project]:
        """List all projects."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM projects ORDER BY created_at DESC
            """)
            
            return [Project(**dict(row)) for row in rows]
    
    async def create_file(self, file_data: FileCreate) -> File:
        """Create a new file record."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO files (project_id, file_path, language)
                VALUES ($1, $2, $3)
                ON CONFLICT (project_id, file_path) DO UPDATE SET
                    language = EXCLUDED.language
                RETURNING *
            """, file_data.project_id, file_data.file_path, file_data.language)
            
            return File(**dict(row))
    
    async def get_files_by_project(self, project_id: UUID) -> List[File]:
        """Get all files for a project."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM files WHERE project_id = $1 ORDER BY file_path
            """, project_id)
            
            return [File(**dict(row)) for row in rows]
    
    async def create_chunk(self, chunk_data: ChunkCreate) -> Chunk:
        """Create a new chunk record."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO chunks (project_id, function_name, file_path, language, chunk_type, code)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
            """, chunk_data.project_id, chunk_data.function_name, chunk_data.file_path,
                 chunk_data.language, chunk_data.chunk_type, chunk_data.code)
            
            return Chunk(**dict(row))
    
    async def update_chunk_summary(self, chunk_id: UUID, summary: str, combined: str, tokens: int) -> Chunk:
        """Update chunk with summary and combined text."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                UPDATE chunks SET summary = $2, combined = $3, tokens = $4
                WHERE chunk_id = $1
                RETURNING *
            """, chunk_id, summary, combined, tokens)
            
            return Chunk(**dict(row))
    
    async def update_chunk_embedding(self, chunk_id: UUID, qdrant_id: str) -> Chunk:
        """Update chunk with Qdrant vector ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                UPDATE chunks SET qdrant_id = $2
                WHERE chunk_id = $1
                RETURNING *
            """, chunk_id, qdrant_id)
            
            return Chunk(**dict(row))
    
    async def get_chunks_by_project(self, project_id: UUID) -> List[Chunk]:
        """Get all chunks for a project."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM chunks WHERE project_id = $1 ORDER BY file_path, function_name
            """, project_id)
            
            return [Chunk(**dict(row)) for row in rows]
    
    async def get_chunk(self, chunk_id: UUID) -> Optional[Chunk]:
        """Get chunk by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM chunks WHERE chunk_id = $1
            """, chunk_id)
            
            return Chunk(**dict(row)) if row else None


# Global database instance
db = Database()
