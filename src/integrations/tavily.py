import httpx
from typing import Optional, List
from src.utils.config import config

class TavilyClient:
    def __init__(self):
        self.api_key = config.TAVILY_API_KEY
        self.base_url = "https://api.tavily.com"
    
    def _is_vietnamese(self, text: str) -> bool:
        vietnamese_chars = ['ă', 'â', 'đ', 'ê', 'ô', 'ơ', 'ư', 'á', 'à', 'ả', 'ã', 'ạ']
        text_lower = text[:500].lower()
        return any(char in text_lower for char in vietnamese_chars)
    
    def _enhance_query_for_vietnamese(self, query: str, slide_title: Optional[str] = None, slide_content: Optional[List[str]] = None) -> str:
        if slide_title and self._is_vietnamese(slide_title):
            vietnamese_context = "giáo dục học tập"
            enhanced = f"{query} {vietnamese_context}"
            return enhanced
        elif slide_content:
            content_text = " ".join(slide_content[:3])
            if self._is_vietnamese(content_text):
                vietnamese_context = "giáo dục học tập"
                enhanced = f"{query} {vietnamese_context}"
                return enhanced
        return query
    
    def search(self, query: str, max_results: int = 1, slide_title: Optional[str] = None, slide_content: Optional[List[str]] = None) -> Optional[str]:
        try:
            enhanced_query = self._enhance_query_for_vietnamese(query, slide_title, slide_content)
            
            url = f"{self.base_url}/search"
            headers = {
                "Content-Type": "application/json"
            }
            is_vn = self._is_vietnamese(enhanced_query) or (slide_title and self._is_vietnamese(slide_title))
            
            payload = {
                "api_key": self.api_key,
                "query": enhanced_query,
                "search_depth": "basic",
                "include_images": True,
                "max_results": max_results
            }
            
            if is_vn:
                payload["query"] = f"{enhanced_query} Vietnam Vietnamese"
                payload["search_depth"] = "advanced"
            
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                if "images" in data and len(data["images"]) > 0:
                    return data["images"][0]
                
                if "results" in data and len(data["results"]) > 0:
                    first_result = data["results"][0]
                    if "images" in first_result and len(first_result["images"]) > 0:
                        return first_result["images"][0]
                
                return None
        except Exception as e:
            print(f"Tavily search error: {e}")
            return None

