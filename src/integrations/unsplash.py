from pyunsplash import PyUnsplash
from typing import Optional
from src.utils.config import config
import requests

class UnsplashClient:
    def __init__(self):
        self.api_key = config.UNSPLASH_API_KEY
        self.client = None
        if self.api_key:
            try:
                self.client = PyUnsplash(api_key=self.api_key)
            except Exception as e:
                print(f"Unsplash init error: {e}")
    
    def search(self, query: str, orientation: str = "landscape") -> Optional[str]:
        if not self.client:
            return None
        
        try:
            search = self.client.search(type_='photos', query=query, per_page=1)
            
            entries = list(search.entries)
            if not entries:
                return None
            
            photo = entries[0]
            return photo.link_download
        except Exception as e:
            print(f"Unsplash search error: {e}")
            return None
    
    def search_background(self, query: str = "abstract gradient", orientation: str = "landscape") -> Optional[str]:
        if not self.api_key:
            return self._get_fallback_background()
        
        try:
            url = "https://api.unsplash.com/photos/random"
            params = {
                "query": query,
                "orientation": orientation,
                "client_id": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("urls", {}).get("regular")
            else:
                return self._get_fallback_background()
        except Exception as e:
            print(f"Unsplash background search error: {e}")
            return self._get_fallback_background()
    
    def _get_fallback_background(self) -> str:
        return "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=1920"

