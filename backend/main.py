from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
from uuid import UUID
import os
import shutil
import tempfile

from config import settings
from db import db
from ingest import ingester
from chunker import chunker
from summarizer import summarizer
from embedder import embedder
from vector_store import vector_store
from models.project import ProjectCreate, Project
from models.chunk import Chunk


app = FastAPI(title="Codebase Ingestion API", version="1.0.0")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        # Connect to database
        await db.connect()
        print("✅ Connected to PostgreSQL")
        
        # Test Qdrant connection
        if await vector_store.test_connection():
            print("✅ Connected to Qdrant")
        else:
            print("❌ Failed to connect to Qdrant")
        
        # Test Ollama connection
        if await summarizer.test_connection():
            print("✅ Connected to Ollama")
        else:
            print("❌ Failed to connect to Ollama")
        
        # Create Qdrant collection
        vector_size = embedder.get_embedding_dimension()
        await vector_store.create_collection(vector_size)
        print(f"✅ Qdrant collection ready (vector size: {vector_size})")
        
    except Exception as e:
        print(f"❌ Startup error: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await db.disconnect()


@app.post("/projects/", response_model=Project)
async def create_project(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    repo_url: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    zip_file: Optional[UploadFile] = File(None)
):
    """Create a new project and ingest codebase."""
    try:
        # Handle zip file upload
        zip_path = None
        if zip_file:
            # Save uploaded file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                shutil.copyfileobj(zip_file.file, tmp_file)
                zip_path = tmp_file.name
        
        # Create project data
        project_data = ProjectCreate(
            name=name,
            description=description,
            repo_url=repo_url,
            language=language,
            zip_file=zip_path
        )
        
        # Ingest project
        result = await ingester.ingest_project(project_data)
        
        # Clean up temporary file
        if zip_path and os.path.exists(zip_path):
            os.unlink(zip_path)
        
        return result["project"]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/projects/{project_id}/process")
async def process_project(project_id: UUID):
    """Process a project: chunk → summarize → embed → store."""
    try:
        # Get project
        project = await db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get project files
        files = await ingester.get_project_files(project_id)
        
        total_chunks = 0
        processed_chunks = 0
        
        for file_record in files:
            try:
                # Read file content
                file_content = await ingester.read_project_file(project_id, file_record.file_path)
                
                # Chunk the file
                chunks = await chunker.chunk_file(
                    file_record.file_path, 
                    file_content, 
                    file_record.language,
                    str(project_id)
                )
                
                total_chunks += len(chunks)
                
                # Process each chunk
                for chunk_data in chunks:
                    try:
                        # Set project ID
                        chunk_data.project_id = project_id
                        
                        # Create chunk in database
                        chunk = await db.create_chunk(chunk_data)
                        
                        # Generate summary
                        summary_result = await summarizer.summarize_code(
                            chunk.code,
                            chunk.language,
                            chunk.chunk_type,
                            chunk.function_name
                        )
                        
                        # Update chunk with summary
                        chunk = await db.update_chunk_summary(
                            chunk.chunk_id,
                            summary_result["summary"],
                            summary_result["combined"],
                            summary_result["tokens"]
                        )
                        
                        # Generate embedding
                        embedding_result = embedder.embed_code(chunk.combined)
                        
                        # Store in Qdrant
                        qdrant_id = str(chunk.chunk_id)
                        chunk_data_for_qdrant = {
                            "qdrant_id": qdrant_id,
                            "project_id": project_id,
                            "file_path": chunk.file_path,
                            "function_name": chunk.function_name,
                            "language": chunk.language,
                            "chunk_type": chunk.chunk_type,
                            "summary": chunk.summary,
                            "code": chunk.code,
                            "combined": chunk.combined,
                            "embedding": embedding_result["embedding"],
                            "tokens": chunk.tokens,
                            "tested": chunk.tested
                        }
                        
                        await vector_store.upsert_chunk(chunk_data_for_qdrant)
                        
                        # Update chunk with Qdrant ID
                        await db.update_chunk_embedding(chunk.chunk_id, qdrant_id)
                        
                        processed_chunks += 1
                        
                    except Exception as e:
                        print(f"Error processing chunk: {str(e)}")
                        continue
                        
            except Exception as e:
                print(f"Error processing file {file_record.file_path}: {str(e)}")
                continue
        
        return {
            "project_id": project_id,
            "total_chunks": total_chunks,
            "processed_chunks": processed_chunks,
            "status": "completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/", response_model=List[Project])
async def list_projects():
    """List all projects."""
    return await db.list_projects()


@app.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: UUID):
    """Get project by ID."""
    project = await db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.get("/projects/{project_id}/chunks", response_model=List[Chunk])
async def get_project_chunks(project_id: UUID):
    """Get all chunks for a project."""
    chunks = await db.get_chunks_by_project(project_id)
    return chunks


@app.post("/search")
async def search_chunks(
    query: str,
    project_id: Optional[UUID] = None,
    limit: int = 10
):
    """Search for similar code chunks."""
    try:
        # Generate embedding for query
        query_embedding = embedder.embed_text(query)
        
        # Search in Qdrant
        results = await vector_store.search_similar(
            query_embedding["embedding"],
            limit=limit,
            project_id=project_id
        )
        
        return {
            "query": query,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        db_ok = True
        try:
            await db.list_projects()
        except:
            db_ok = False
        
        # Test Qdrant connection
        qdrant_ok = await vector_store.test_connection()
        
        # Test Ollama connection
        ollama_ok = await summarizer.test_connection()
        
        return {
            "status": "healthy" if all([db_ok, qdrant_ok, ollama_ok]) else "degraded",
            "services": {
                "database": "ok" if db_ok else "error",
                "qdrant": "ok" if qdrant_ok else "error",
                "ollama": "ok" if ollama_ok else "error"
            }
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
