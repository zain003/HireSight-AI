"""
Embedding generation using Sentence-BERT.
Provides semantic similarity capabilities for skill matching.
"""
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

from app.core.config import settings


class EmbeddingService:
    """Service for generating and comparing embeddings"""
    
    def __init__(self):
        """Initialize SBERT model"""
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Lazy load the SBERT model"""
        if self.model is None:
            print(f"Loading SBERT model: {settings.SBERT_MODEL}")
            self.model = SentenceTransformer(settings.SBERT_MODEL)
            print("✓ SBERT model loaded successfully")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Numpy array of embeddings
        """
        return self.model.encode(text, convert_to_numpy=True)
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            Numpy array of embeddings
        """
        return self.model.encode(texts, convert_to_numpy=True)
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        emb1 = self.generate_embedding(text1)
        emb2 = self.generate_embedding(text2)
        
        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)
    
    def find_similar_skills(self, skill: str, skill_database: List[str], threshold: float = 0.7) -> List[tuple]:
        """
        Find similar skills from a database using semantic similarity.
        
        Args:
            skill: Input skill to match
            skill_database: List of known skills
            threshold: Minimum similarity threshold
            
        Returns:
            List of (skill, similarity_score) tuples
        """
        skill_emb = self.generate_embedding(skill)
        db_embs = self.generate_embeddings(skill_database)
        
        # Compute similarities
        similarities = np.dot(db_embs, skill_emb) / (
            np.linalg.norm(db_embs, axis=1) * np.linalg.norm(skill_emb)
        )
        
        # Filter by threshold and sort
        results = [
            (skill_database[i], float(similarities[i]))
            for i in range(len(skill_database))
            if similarities[i] >= threshold
        ]
        
        return sorted(results, key=lambda x: x[1], reverse=True)


# Singleton instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
