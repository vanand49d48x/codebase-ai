from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from config import settings


class VectorStore:
    def __init__(self):
        self.qdrant_host = settings.qdrant_host
        self.qdrant_port = settings.qdrant_port
        self.collection_name = settings.qdrant_collection
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connect to Qdrant."""
        try:
            self.client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
        except Exception as e:
            raise Exception(f"Failed to connect to Qdrant: {str(e)}")
    
    async def create_collection(self, vector_size: int):
        """Create Qdrant collection if it doesn't exist."""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                print(f"Created Qdrant collection: {self.collection_name}")
            else:
                print(f"Qdrant collection already exists: {self.collection_name}")
                
        except Exception as e:
            raise Exception(f"Failed to create Qdrant collection: {str(e)}")
    
    async def upsert_chunk(self, chunk_data: Dict[str, Any]) -> str:
        """Insert or update a chunk in Qdrant."""
        try:
            # Create point structure
            point = PointStruct(
                id=chunk_data["qdrant_id"],
                vector=chunk_data["embedding"],
                payload={
                    "project_id": str(chunk_data["project_id"]),
                    "file_path": chunk_data["file_path"],
                    "function_name": chunk_data.get("function_name"),
                    "language": chunk_data["language"],
                    "chunk_type": chunk_data["chunk_type"],
                    "summary": chunk_data.get("summary", ""),
                    "code": chunk_data["code"],
                    "combined": chunk_data.get("combined", ""),
                    "embedding_strategy": "combined",
                    "tokens": chunk_data.get("tokens", 0),
                    "tested": chunk_data.get("tested", False),
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            # Upsert point
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            return chunk_data["qdrant_id"]
            
        except Exception as e:
            raise Exception(f"Failed to upsert chunk in Qdrant: {str(e)}")
    
    async def search_similar(self, query_embedding: List[float], limit: int = 10, 
                           project_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Search for similar chunks."""
        try:
            # Build search filter
            search_filter = None
            if project_id:
                search_filter = {
                    "must": [
                        {
                            "key": "project_id",
                            "match": {"value": str(project_id)}
                        }
                    ]
                }
            
            # Search in Qdrant
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=search_filter,
                with_payload=True
            )
            
            # Format results
            results = []
            for point in search_result:
                results.append({
                    "id": point.id,
                    "score": point.score,
                    "payload": point.payload
                })
            
            return results
            
        except Exception as e:
            raise Exception(f"Failed to search in Qdrant: {str(e)}")
    
    async def delete_project_chunks(self, project_id: UUID):
        """Delete all chunks for a project."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector={
                    "filter": {
                        "must": [
                            {
                                "key": "project_id",
                                "match": {"value": str(project_id)}
                            }
                        ]
                    }
                }
            )
        except Exception as e:
            raise Exception(f"Failed to delete project chunks: {str(e)}")
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "name": collection_info.name,
                "vector_size": collection_info.config.params.vectors.size,
                "distance": collection_info.config.params.vectors.distance,
                "points_count": collection_info.points_count
            }
        except Exception as e:
            raise Exception(f"Failed to get collection info: {str(e)}")
    
    async def test_connection(self) -> bool:
        """Test connection to Qdrant."""
        try:
            collections = self.client.get_collections()
            return True
        except Exception:
            return False


# Global vector store instance
vector_store = VectorStore()
