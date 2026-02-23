import llm_extension
from langchain_openai import ChatOpenAI
from typing import List, Dict, Optional, Any, Set
import json
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO
import torch
from transformers import CLIPProcessor, CLIPModel
from src.utils.config import config


class ImageDistribution:
    def __init__(self, model: str = "gpt-5"):
        self.llm = ChatOpenAI(model=model, temperature=0.4, max_tokens=16000)
        self.model = model
        
        # Initialize CLIP model for image similarity
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        
        # Serper API configuration
        self.serper_api_key = config.SERPER_API_KEY
        self.num_images = 3  # Number of images to fetch per query
    
    def distribute_images(
        self,
        lecture_id: str,
        need_visualization: List[Dict[str, Any]],
        aggregated_media: Dict[str, Any],
        used_images: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Distribute images to slides based on visualization needs.
        
        Args:
            lecture_id: Lecture ID for saving downloaded images
            need_visualization: List of slides needing visualization with queries
            aggregated_media: Aggregated media containing existing images
            used_images: Set of already used image paths
            
        Returns:
            List of image distributions with slide_number, image_path, and clip_score
        """
        distributions = []
        
        # Create directory for downloaded images
        download_dir = Path(f"data/lectures/{lecture_id}/downloaded_images")
        download_dir.mkdir(parents=True, exist_ok=True)
        
        # Get existing images from aggregated media
        existing_images = aggregated_media.get('images', [])
        
        for viz_item in need_visualization:
            slide_number = viz_item['slide_number']
            query = viz_item['query']
            
            print(f"\nProcessing slide {slide_number}: {query[:60]}...")
            
            # Search and download images from Serper
            downloaded_images = self._search_and_download_images(
                query=query,
                download_dir=download_dir,
                slide_number=slide_number
            )
            
            # Combine existing images and downloaded images
            all_candidate_images = []
            
            # Add existing images
            for img in existing_images:
                img_path = img.get('file_path')
                if img_path and Path(img_path).exists():
                    all_candidate_images.append({
                        'path': img_path,
                        'source': 'existing'
                    })
            
            # Add downloaded images
            for img_path in downloaded_images:
                all_candidate_images.append({
                    'path': str(img_path),
                    'source': 'downloaded'
                })
            
            if not all_candidate_images:
                print(f"  No images found for slide {slide_number}")
                continue
            
            # Calculate CLIP scores for all candidates
            scored_images = self._score_images_with_clip(query, all_candidate_images)
            
            # Sort by score (highest first)
            scored_images.sort(key=lambda x: x['clip_score'], reverse=True)
            
            # Find the first unused image
            selected_image = None
            for img in scored_images:
                img_name = Path(img['path']).name
                if img_name not in used_images:
                    selected_image = img
                    used_images.add(img_name)
                    break
            
            if selected_image:
                distributions.append({
                    'slide_number': slide_number,
                    'image_path': selected_image['path'],
                    'clip_score': selected_image['clip_score'],
                    'source': selected_image['source']
                })
                print(f"  Selected: {Path(selected_image['path']).name} (score: {selected_image['clip_score']:.3f})")
            else:
                print(f"  All images already used for slide {slide_number}")
        
        # Save distributions to JSON file
        output_path = Path(f"data/lectures/{lecture_id}_image_distributions.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(distributions, f, indent=2, ensure_ascii=False)
        print(f"\nSaved image distributions to: {output_path}")
        
        return distributions
    
    def _search_and_download_images(
        self,
        query: str,
        download_dir: Path,
        slide_number: int
    ) -> List[Path]:
        """
        Search images using Serper API and download them.
        
        Args:
            query: Search query
            download_dir: Directory to save downloaded images
            slide_number: Slide number for naming files
            
        Returns:
            List of paths to downloaded images
        """
        # Search images via Serper API
        image_urls = self._search_images(query)
        
        if not image_urls:
            print(f"  No images found via Serper for query: {query[:50]}...")
            return []
        
        # Download images
        downloaded_paths = []
        for idx, url in enumerate(image_urls):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                # Verify it's an image
                img = Image.open(BytesIO(response.content))
                
                # Save image
                file_name = f"slide_{slide_number}_serper_{idx+1}.png"
                file_path = download_dir / file_name
                img.save(file_path, 'PNG')
                
                downloaded_paths.append(file_path)
                print(f"  Downloaded: {file_name}")
                
            except Exception as e:
                print(f"  Failed to download image from {url[:50]}...: {e}")
        
        return downloaded_paths
    
    def _search_images(self, query: str) -> List[str]:
        """
        Search images using Google Serper API.
        
        Args:
            query: Search query
            
        Returns:
            List of image URLs
        """
        url = "https://google.serper.dev/images"
        payload = json.dumps({"q": query})
        headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            results = response.json().get('images', [])
            
            # Filter out SVG images and get URLs
            image_urls = [
                r['imageUrl'] for r in results[:self.num_images]
                if r.get('imageUrl') and not r['imageUrl'].lower().endswith('.svg')
            ]
            
            return image_urls
            
        except Exception as e:
            print(f"  Error searching images for '{query[:50]}...': {e}")
            return []
    
    def _score_images_with_clip(
        self,
        query: str,
        candidate_images: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Score images using CLIP model based on query similarity.
        
        Args:
            query: Text query
            candidate_images: List of dicts with 'path' and 'source' keys
            
        Returns:
            List of scored images with clip_score added
        """
        scored_images = []
        
        # Prepare text input
        text_inputs = self.clip_processor(
            text=[query],
            return_tensors="pt",
            padding=True
        )
        
        for img_info in candidate_images:
            try:
                # Load image
                img_path = img_info['path']
                image = Image.open(img_path).convert('RGB')
                
                # Prepare image input
                image_inputs = self.clip_processor(
                    images=image,
                    return_tensors="pt"
                )
                
                # Calculate similarity
                with torch.no_grad():
                    text_features = self.clip_model.get_text_features(**text_inputs)
                    image_features = self.clip_model.get_image_features(**image_inputs)
                    
                    # Normalize features
                    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                    
                    # Calculate cosine similarity
                    similarity = (text_features @ image_features.T).item()
                
                scored_images.append({
                    'path': img_path,
                    'source': img_info['source'],
                    'clip_score': similarity
                })
                
            except Exception as e:
                print(f"  Error scoring image {img_path}: {e}")
                # Add with low score if error
                scored_images.append({
                    'path': img_info['path'],
                    'source': img_info['source'],
                    'clip_score': 0.0
                })
        
        return scored_images


# Main function for testing
def main():
    """Test the VisualDistribution class"""
    print("=" * 60)
    print("Testing VisualDistribution")
    print("=" * 60)
    
    # Initialize the distributor
    distributor = VisualDistribution()
    
    # Sample data
    lecture_id = "lec_607fe87f"
    
    # Load visualization queries
    with open(f"data/lectures/{lecture_id}_visualization_queries.json", 'r') as f:
        need_visualization = json.load(f)
    
    # Load aggregated media
    with open(f"data/media/607fe87f-b0f0-48b2-9c3d-ef5ccea059e1_media.json", 'r') as f:
        aggregated_media = json.load(f)
    
    # Track used images
    used_images = set()
    
    print(f"\nDistributing images for {len(need_visualization)} slides...")
    
    # Distribute images
    distributions = distributor.distribute_images(
        lecture_id=lecture_id,
        need_visualization=need_visualization,
        aggregated_media=aggregated_media,
        used_images=used_images
    )
    
    # Display results
    print("\n" + "=" * 60)
    print("Distribution Results")
    print("=" * 60)
    
    for dist in distributions:
        print(f"\nSlide {dist['slide_number']}:")
        print(f"  Image: {Path(dist['image_path']).name}")
        print(f"  Score: {dist['clip_score']:.3f}")
        print(f"  Source: {dist['source']}")
    
    # Save results
    output_path = Path(f"data/lectures/{lecture_id}_image_distributions.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(distributions, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved distributions to: {output_path}")


if __name__ == "__main__":
    main()
