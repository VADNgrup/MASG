from pathlib import Path
from typing import Dict, Tuple, List, Any
from datetime import datetime
from src.models.context import DocumentContext
from src.models.asset import ImageAsset
from src.models.slide import ImageReference
from src.integrations.vision_classifier import VisionImageClassifier
from src.integrations.abstract_classifier import AbstractConceptClassifier
from src.integrations.tavily import TavilyClient
from src.integrations.genai_image import GenAIImageGenerator
from src.utils.semantic_match import SemanticMatcher
from src.utils.image_quality import ImageQualityAssessor
from src.utils.config import config

class AssetManager:
    def __init__(self):
        self.vision_classifier = VisionImageClassifier()
        self.semantic_matcher = SemanticMatcher()
        self.abstract_classifier = AbstractConceptClassifier()
        self.tavily_client = TavilyClient()
        self.genai_generator = GenAIImageGenerator()
        self.quality_assessor = ImageQualityAssessor()
    
    async def resolve_image(
        self, 
        query: str, 
        context: DocumentContext,
        slide_title: str = None,
        slide_content: List[str] = None
    ) -> Tuple[ImageReference, Dict[str, Any]]:
        decision_log = {
            "query": query,
            "timestamp": datetime.now().isoformat()
        }
        
        original_candidates = self._semantic_search_originals(query, context.assets.images)
        
        if not original_candidates:
            return await self._handle_no_original_match(query, decision_log, slide_title, slide_content)
        
        best_match = original_candidates[0]
        decision_log["best_original_match"] = {
            "image_id": best_match["image_id"],
            "similarity_score": best_match["score"]
        }
        
        image_path = config.BASE_DIR / best_match["image_path"]
        
        original_asset = next((img for img in context.assets.images if img.image_id == best_match["image_id"]), None)
        
        if original_asset and original_asset.content_type in ["table_image", "data_chart", "screenshot_code"]:
            decision_log["decision"] = "FORCE_ORIGINAL_BY_CONTENT_TYPE"
            decision_log["reason"] = f"Content type '{original_asset.content_type}' from Phase 1 - contains specific data, must use original"
            decision_log["phase1_content_type"] = original_asset.content_type
            
            return ImageReference(
                source="original",
                priority=1,
                image_id=best_match["image_id"],
                metadata={"forced_by_content_type": True, "content_type": original_asset.content_type}
            ), decision_log
        
        classification = self.vision_classifier.classify_info_density(image_path)
        
        decision_log["classification"] = classification
        
        if classification["type"] in ["technical_diagram", "data_chart", "screenshot_code"]:
            decision_log["decision"] = "FORCE_ORIGINAL"
            decision_log["reason"] = f"Critical {classification['type']} - contains irreplaceable data"
            
            return ImageReference(
                source="original",
                priority=1,
                image_id=best_match["image_id"],
                metadata={"forced": True, "confidence": classification["confidence"]}
            ), decision_log
        
        quality_score = self.quality_assessor.assess_quality(image_path)
        decision_log["quality_score"] = quality_score
        
        if quality_score < 0.4 or classification["type"] == "decorative_photo":
            decision_log["decision"] = "SEARCH_BETTER"
            decision_log["reason"] = f"Low quality ({quality_score:.2f}) or decorative"
            
            return await self._search_better_version(query, decision_log, slide_title, slide_content)
        
        if original_asset and original_asset.content_type in ["diagram", "technical_diagram"]:
            if best_match["score"] >= 0.55:
                decision_log["decision"] = "USE_ORIGINAL_DIAGRAM"
                decision_log["reason"] = f"Diagram from original document with reasonable match ({best_match['score']:.2f}) - prefer original over external"
                
                return ImageReference(
                    source="original",
                    priority=1,
                    image_id=best_match["image_id"],
                    metadata={"diagram_from_source": True, "match_score": best_match["score"]}
                ), decision_log
        
        if best_match["score"] >= 0.55:
            decision_log["decision"] = "USE_ORIGINAL"
            decision_log["reason"] = f"Good semantic match ({best_match['score']:.2f}) - using original image"
            
            return ImageReference(
                source="original",
                priority=1,
                image_id=best_match["image_id"]
            ), decision_log
        else:
            decision_log["decision"] = "SEARCH_BETTER_MATCH"
            decision_log["reason"] = f"Match score {best_match['score']:.2f} below threshold (0.55) - searching for better image"
            return await self._search_better_version(query, decision_log, slide_title, slide_content)
    
    def _semantic_search_originals(self, query: str, images: List[ImageAsset]) -> List[Dict]:
        candidates = []
        
        for img in images:
            if not img.caption_rag or img.is_decoration:
                continue
            
            score = self.semantic_matcher.compute_similarity(query, img.caption_rag)
            
            if score >= 0.4:
                candidates.append({
                    "image_id": img.image_id,
                    "image_path": img.file_path,
                    "score": score,
                    "caption": img.caption_rag,
                    "content_type": img.content_type
                })
        
        return sorted(candidates, key=lambda x: x["score"], reverse=True)
    
    async def _search_better_version(self, query: str, decision_log: Dict, slide_title: str = None, slide_content: List[str] = None) -> Tuple[ImageReference, Dict]:
        decision_log["final_source"] = "tavily"
        
        tavily_url = self.tavily_client.search(query, slide_title=slide_title, slide_content=slide_content)
        
        if tavily_url:
            return ImageReference(
                source="tavily",
                priority=2,
                url=tavily_url
            ), decision_log
        
        is_abstract = self.abstract_classifier.is_abstract(query)
        decision_log["is_abstract"] = is_abstract
        decision_log["tavily_failed"] = True
        
        if is_abstract:
            decision_log["final_source"] = "generated"
            enhanced_prompt = f"Educational illustration for: {query}. Modern, clean, professional style for academic presentation."
            
            generated_path = await self.genai_generator.generate(enhanced_prompt)
            
            return ImageReference(
                source="generated",
                priority=3,
                path=generated_path,
                generation_prompt=enhanced_prompt
            ), decision_log
        else:
            decision_log["final_source"] = "none"
            return ImageReference(
                source="tavily",
                priority=2,
                url=None
            ), decision_log
    
    async def _handle_no_original_match(self, query: str, decision_log: Dict, slide_title: str = None, slide_content: List[str] = None) -> Tuple[ImageReference, Dict]:
        decision_log["decision"] = "NO_ORIGINAL_MATCH"
        return await self._search_better_version(query, decision_log, slide_title, slide_content)

