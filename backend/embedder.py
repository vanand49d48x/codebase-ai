from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import numpy as np
from config import settings


class CodeEmbedder:
    def __init__(self):
        self.embedding_provider = settings.embedding_provider
        self.embedding_model = settings.embedding_model
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model."""
        if self.embedding_provider == "sentence-transformers":
            try:
                self.model = SentenceTransformer(self.embedding_model)
            except Exception as e:
                raise Exception(f"Failed to load embedding model {self.embedding_model}: {str(e)}")
        else:
            raise ValueError(f"Unsupported embedding provider: {self.embedding_provider}")
    
    def embed_text(self, text: str) -> Dict[str, Any]:
        """Generate embedding for a text."""
        if not self.model:
            raise Exception("Embedding model not loaded")
        
        try:
            # Generate embedding
            embedding = self.model.encode(text)
            
            # Convert to list for JSON serialization
            embedding_list = embedding.tolist()
            
            # Estimate token count (rough approximation)
            tokens = len(text.split())
            
            return {
                "embedding": embedding_list,
                "tokens": tokens,
                "model": self.embedding_model,
                "dimension": len(embedding_list)
            }
            
        except Exception as e:
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    def embed_code(self, combined_text: str) -> Dict[str, Any]:
        """Generate embedding for code with summary."""
        return self.embed_text(combined_text)
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors."""
        if not self.model:
            raise Exception("Embedding model not loaded")
        
        # Generate a dummy embedding to get dimension
        dummy_embedding = self.model.encode("test")
        return len(dummy_embedding)
    
    def batch_embed(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Generate embeddings for multiple texts efficiently."""
        if not self.model:
            raise Exception("Embedding model not loaded")
        
        try:
            # Generate embeddings in batch
            embeddings = self.model.encode(texts)
            
            results = []
            for i, embedding in enumerate(embeddings):
                embedding_list = embedding.tolist()
                tokens = len(texts[i].split())
                
                results.append({
                    "embedding": embedding_list,
                    "tokens": tokens,
                    "model": self.embedding_model,
                    "dimension": len(embedding_list)
                })
            
            return results
            
        except Exception as e:
            raise Exception(f"Failed to generate batch embeddings: {str(e)}")
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


# Global embedder instance
embedder = CodeEmbedder()
