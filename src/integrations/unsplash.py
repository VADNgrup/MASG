from pyunsplash import PyUnsplash
from typing import Optional
from src.utils.config import config

class UnsplashClient:
    def __init__(self):
        self.client = PyUnsplash(api_key=config.UNSPLASH_API_KEY)
    
    def search(self, query: str, orientation: str = "landscape") -> Optional[str]:
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

