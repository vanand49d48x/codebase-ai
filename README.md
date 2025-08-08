# CodebaseAI - Self-Hosted Codebase Intelligence Platform

A fully configurable, self-hosted backend architecture for ingesting codebases, chunking them into functions/classes, generating summaries with LLMs, creating embeddings, and storing everything in Qdrant + PostgreSQL.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Git Repo      │    │   Upload Zip    │    │   FastAPI       │
│   or Zip File   │───▶│   or Clone      │───▶│   Backend       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │◀───│   Qdrant        │◀───│   Chunk →       │
│   (Metadata)    │    │   (Vectors)     │    │   Summarize →   │
└─────────────────┘    └─────────────────┘    │   Embed         │
                                              └─────────────────┘
```

## 🚀 Features

- **✅ Fully Self-Hosted**: No external API dependencies
- **✅ Configurable**: Everything driven by environment variables
- **✅ Modular Design**: Clean separation of concerns
- **✅ Multi-Language Support**: Python, JavaScript, TypeScript, Java, C++, Go, Rust, and more
- **✅ AST-Based Chunking**: Intelligent parsing of functions and classes
- **✅ LLM Summarization**: Using self-hosted Ollama with Codestral model
- **✅ Vector Embeddings**: Using sentence-transformers locally
- **✅ Vector Search**: Qdrant for semantic code search
- **✅ Metadata Storage**: PostgreSQL for project and chunk metadata

## 🐳 Quick Start with Docker

### 1. Clone and Setup

```bash
git clone <your-repo>
cd <your-repo>
```

### 2. Start Services

```bash
docker compose up -d
```

This will start:
- **Backend API** (port 8000)
- **Qdrant Vector DB** (port 6333)
- **PostgreSQL** (port 5432)
- **Ollama LLM** (port 11434)

### 3. Wait for Initialization

The first startup will:
- Download the Codestral model (~7GB)
- Create Qdrant collection
- Initialize PostgreSQL tables

Check status:
```bash
curl http://localhost:8000/health
```

## 📋 API Endpoints

### Create Project
```bash
# From Git repository
curl -X POST "http://localhost:8000/projects/" \
  -F "name=my-project" \
  -F "description=Authentication microservice" \
  -F "repo_url=https://github.com/user/repo.git" \
  -F "language=python"

# From ZIP file
curl -X POST "http://localhost:8000/projects/" \
  -F "name=my-project" \
  -F "description=Uploaded codebase" \
  -F "language=python" \
  -F "zip_file=@/path/to/codebase.zip"
```

### Process Project
```bash
curl -X POST "http://localhost:8000/projects/{project_id}/process"
```

### Search Code
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication login function",
    "project_id": "optional-project-uuid",
    "limit": 10
  }'
```

### List Projects
```bash
curl "http://localhost:8000/projects/"
```

## ⚙️ Configuration

All configuration is done via environment variables in `docker-compose.yml`:

### LLM Configuration
```yaml
LLM_PROVIDER=ollama
LLM_MODEL=codestral
OLLAMA_HOST=http://ollama:11434
```

### Embedding Configuration
```yaml
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Vector Store Configuration
```yaml
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=code_chunks
```

### Database Configuration
```yaml
DB_URL=postgresql+asyncpg://user:password@postgres:5432/codebase_db
```

## 🔧 Development Setup

### Local Development

1. **Install Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

2. **Setup Services**
```bash
# Start PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=codebase_db \
  -p 5432:5432 \
  postgres:14

# Start Qdrant
docker run -d --name qdrant \
  -p 6333:6333 \
  qdrant/qdrant

# Start Ollama
docker run -d --name ollama \
  -p 11434:11434 \
  ollama/ollama
```

3. **Pull LLM Model**
```bash
docker exec ollama ollama pull codestral
```

4. **Run Backend**
```bash
cd backend
python main.py
```

## 📊 Data Flow

### 1. Ingestion
- Accept Git URL or ZIP file
- Clone/extract to workspace
- Register project in PostgreSQL
- Find all code files

### 2. Chunking
- Parse each file with AST (Python) or as whole file
- Extract functions and classes
- Create chunk records in database

### 3. Summarization
- Send code to Ollama with Codestral model
- Generate concise summaries
- Combine summary + code for embedding

### 4. Embedding
- Use sentence-transformers locally
- Generate vector embeddings
- Store in Qdrant with metadata

### 5. Storage
- **Qdrant**: Vector embeddings for semantic search
- **PostgreSQL**: Project metadata, file info, chunk details

## 🗂️ Database Schema

### Projects Table
```sql
CREATE TABLE projects (
  project_id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  repo_url TEXT,
  language VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Files Table
```sql
CREATE TABLE files (
  file_id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(project_id),
  file_path VARCHAR(500) NOT NULL,
  language VARCHAR(50) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Chunks Table
```sql
CREATE TABLE chunks (
  chunk_id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(project_id),
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
);
```

## 🔍 Qdrant Schema

Each chunk is stored as a vector point with payload:
```json
{
  "project_id": "uuid",
  "file_path": "auth/login.py",
  "function_name": "login",
  "language": "python",
  "chunk_type": "function",
  "summary": "# LLM Summary: Authenticates user using bcrypt",
  "code": "def login(...): ...",
  "combined": "# Summary\n\n# Code",
  "embedding_strategy": "combined",
  "tokens": 198,
  "tested": false,
  "created_at": "2025-01-07T12:00:00Z"
}
```

## 🛠️ Customization

### Add New Language Support
1. Update `utils/file_utils.py` with language mapping
2. Extend `chunker.py` with language-specific parsing
3. Update chunking logic in `main.py`

### Change LLM Model
1. Update `LLM_MODEL` in environment
2. Pull new model: `docker exec ollama ollama pull <model>`
3. Restart services

### Change Embedding Model
1. Update `EMBEDDING_MODEL` in environment
2. Restart backend service

## 🚨 Troubleshooting

### Common Issues

1. **Ollama Connection Failed**
   ```bash
   # Check if Ollama is running
   docker logs ollama
   
   # Pull model manually
   docker exec ollama ollama pull codestral
   ```

2. **Qdrant Connection Failed**
   ```bash
   # Check Qdrant logs
   docker logs qdrant
   
   # Restart Qdrant
   docker restart qdrant
   ```

3. **PostgreSQL Connection Failed**
   ```bash
   # Check PostgreSQL logs
   docker logs postgres
   
   # Restart PostgreSQL
   docker restart postgres
   ```

### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "database": "ok",
    "qdrant": "ok",
    "ollama": "ok"
  }
}
```

## 📈 Performance

### Memory Usage
- **Ollama**: ~8GB (Codestral model)
- **Qdrant**: ~2GB (vector storage)
- **PostgreSQL**: ~1GB (metadata)
- **Backend**: ~2GB (sentence-transformers)

### Processing Speed
- **Small project** (<100 files): ~5-10 minutes
- **Medium project** (100-1000 files): ~30-60 minutes
- **Large project** (>1000 files): ~2-4 hours

### Storage
- **Vector embeddings**: ~1KB per chunk
- **Code storage**: ~2-5KB per chunk
- **Metadata**: ~1KB per chunk

## 🔐 Security

- All services run in isolated containers
- No external API calls (fully self-hosted)
- Database credentials in environment variables
- No hardcoded secrets

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the health check endpoint
