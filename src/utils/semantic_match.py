from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Optional, Tuple
from src.models.asset import ImageAsset

class SemanticMatcher:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.cache = {}
    
    def compute_similarity(self, query: str, caption: str) -> float:
        query_embedding = self._get_embedding(query)
        caption_embedding = self._get_embedding(caption)
        
        similarity = cosine_similarity(
            query_embedding.reshape(1, -1),
            caption_embedding.reshape(1, -1)
        )[0][0]
        
        return float(similarity)
    
    def find_best_match(
        self, 
        query: str, 
        candidates: List[ImageAsset],
        threshold: float = 0.6
    ) -> Optional[Tuple[str, float, str]]:
        best_score = 0
        best_id = None
        best_path = None
        
        for img in candidates:
            if not img.caption_rag or img.is_decoration:
                continue
            
            score = self.compute_similarity(query, img.caption_rag)
            
            if score > best_score:
                best_score = score
                best_id = img.image_id
                best_path = img.file_path
        
        if best_score >= threshold:
            return (best_id, best_score, best_path)
        return None
    
    def _get_embedding(self, text: str) -> np.ndarray:
        if text in self.cache:
            return self.cache[text]
        
        embedding = self.model.encode(text)
        self.cache[text] = embedding
        return embedding

