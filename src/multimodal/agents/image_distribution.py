import llm_extension
from langchain_openai import ChatOpenAI
from typing import List, Dict, Optional, Any, Set
import json
import requests
import base64
from pathlib import Path
from PIL import Image
from io import BytesIO
import torch
from transformers import CLIPProcessor, CLIPModel
from openai import OpenAI
from src.utils.config import config


class ImageDistribution:
    def __init__(self):
        
        # Initialize CLIP model for image similarity
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        
        # VLM client for caption generation
        self.vlm_client = OpenAI(
            base_url=config.VLM_BASE_URL,
            api_key=config.VLM_API_KEY
        )
        self.vlm_model = config.VLM_MODEL_NAME
        
        # CCMR hyperparameter: caption prior weight (0.5 ≤ λ ≤ 0.8)
        self.lambda_prior = 0.6
        
        # Serper API configuration
        self.serper_api_key = config.SERPER_API_KEY
        self.num_images = 3  # Number of images to fetch per query

        # Domains to skip when selecting images (thumbnails, paywalls, etc.)
        self.skip_websites = [
            "researchgate.net",
            "huggingface.co"
        ]
    
    def distribute_images(
        self,
        lecture_id: str,
        need_visualization: List[Dict[str, Any]],
        aggregated_media: Dict[str, Any],
        used_images: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Distribute images to slides using Caption-Conditioned Multimodal Retrieval (CCMR).
        
        For each slide needing visualization:
        1. Download candidate images from Serper API
        2. Generate VLM captions for downloaded images
        3. Use CCMR to score all candidates: q' = normalize(q + λ·c), score = cos(q', i)
        4. Select the best unused image
        5. If selected image is downloaded, add it to aggregated_media
        
        Args:
            lecture_id: Lecture ID for saving downloaded images
            need_visualization: List of slides needing visualization with queries
            aggregated_media: Aggregated media containing existing images (mutated in-place
                              when a downloaded image is selected)
            used_images: Set of already used image paths
            
        Returns:
            List of image distributions with slide_number, image_path, and ccmr_score
        """
        distributions = []
        
        # Create directory for downloaded images
        download_dir = Path(f"data/lectures/{lecture_id}/downloaded_images")
        download_dir.mkdir(parents=True, exist_ok=True)
        
        # Get existing images from aggregated media (with their captions from context)
        existing_images = aggregated_media.get('images', [])

        # Build chart candidates from tables that have a rendered chart_path
        chart_candidates = []
        import re as _re
        for tbl in aggregated_media.get('tables', []):
            chart_path = tbl.get('chart_path')
            if chart_path and Path(chart_path).exists():
                raw_caption = tbl.get('table_caption', '')
                # "Table 3: Some caption" → "Chart about: Some caption"
                clean_caption = _re.sub(
                    r'^[Tt]able\s*\d*\s*[:\-]?\s*', '', raw_caption
                ).strip()
                chart_caption = f"Chart about: {clean_caption}" if clean_caption else "Chart about: data visualization"
                chart_candidates.append({
                    'path': chart_path,
                    'source': 'existing',
                    'caption': chart_caption
                })

        if chart_candidates:
            print(f"  Found {len(chart_candidates)} chart image(s) from tables")

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

            # Build candidate pool
            all_candidate_images = []

            # Existing images from document: use caption from context as semantic prior
            for img in existing_images:
                img_path = img.get('file_path')
                if img_path and Path(img_path).exists():
                    all_candidate_images.append({
                        'path': img_path,
                        'source': 'existing',
                        'caption': img.get('caption', '')
                    })

            # Chart images rendered from document tables
            all_candidate_images.extend(chart_candidates)
            
            # Downloaded images: generate caption using VLM
            for img_path in downloaded_images:
                print(f"  [VLM] Generating caption for {Path(img_path).name}...")
                caption = self._generate_caption(str(img_path), query=query)
                all_candidate_images.append({
                    'path': str(img_path),
                    'source': 'downloaded',
                    'caption': caption
                })
            
            if not all_candidate_images:
                print(f"  No images found for slide {slide_number}")
                continue
            
            # Score all candidates with CCMR
            scored_images = self._score_images_with_ccmr(query, all_candidate_images)
            
            # Sort by score (highest first)
            scored_images.sort(key=lambda x: x['ccmr_score'], reverse=True)
            
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
                    'ccmr_score': selected_image['ccmr_score'],
                    'source': selected_image['source'],
                    'caption': selected_image['caption']
                })
                print(f"  Selected: {Path(selected_image['path']).name} "
                      f"(score: {selected_image['ccmr_score']:.3f}, source: {selected_image['source']})")
                
                # If the selected image was downloaded, add it to aggregated_media
                if selected_image['source'] == 'downloaded':
                    img_path = Path(selected_image['path'])
                    try:
                        with Image.open(img_path) as pil_img:
                            width, height = pil_img.size
                            fmt = pil_img.format or 'PNG'
                        file_size_kb = round(img_path.stat().st_size / 1024, 2)
                    except Exception:
                        width, height, fmt, file_size_kb = 0, 0, 'PNG', 0.0
                    
                    new_entry = {
                        'image_id': f"downloaded_slide{slide_number}",
                        'file_path': selected_image['path'],
                        'caption': selected_image['caption'],
                        'metadata': {
                            'width': width,
                            'height': height,
                            'format': fmt.lower(),
                            'file_size_kb': file_size_kb
                        }
                    }
                    aggregated_media['images'].append(new_entry)
                    aggregated_media['total_images'] = len(aggregated_media['images'])
                    print(f"  [aggregated_media] Added downloaded image → total_images: {aggregated_media['total_images']}")
            else:
                print(f"  All images already used for slide {slide_number}")
        
        # Save distributions to JSON file
        output_path = Path(f"data/lectures/{lecture_id}_image_distributions.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(distributions, f, indent=2, ensure_ascii=False)
        print(f"\nSaved image distributions to: {output_path}")
        
        return distributions
    
    def _generate_caption(self, image_path: str, query: str = "") -> str:
        """
        Generate a descriptive caption for an image using the configured VLM.
        
        Args:
            image_path: Path to the image file
            query: Slide image query used as context to guide caption generation
            
        Returns:
            Caption string describing the image content
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Detect MIME type from extension
            ext = Path(image_path).suffix.lower()
            mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                        '.png': 'image/png', '.gif': 'image/gif',
                        '.webp': 'image/webp'}
            mime_type = mime_map.get(ext, 'image/png')
            
            response = self.vlm_client.chat.completions.create(
                model=self.vlm_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                }
                            },
                            {
                                "type": "text",
                                "text": (
                                    f"Context: This image was retrieved for the topic: '{query}'.\n"
                                    "Describe this image concisely in 1-2 sentences, "
                                    "focusing on aspects relevant to the context above, "
                                    "the main subject, visual content, and any text or data it contains. "
                                    "Be specific and informative."
                                ) if query else (
                                    "Describe this image concisely in 1-2 sentences, "
                                    "focusing on the main subject, visual content, and "
                                    "any text or data it contains. Be specific and informative."
                                )
                            }
                        ]
                    }
                ],
                max_tokens=150,
                temperature=0.2
            )
            
            caption = response.choices[0].message.content.strip()
            print(f"    Caption: {caption[:80]}...")
            return caption
            
        except Exception as e:
            print(f"  [VLM] Failed to generate caption for {image_path}: {e}")
            return ""
    
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

            # Collect up to num_images valid URLs, skipping blocked domains and SVGs
            image_urls = []
            for r in results:
                if len(image_urls) >= self.num_images:
                    break
                img_url = r.get('imageUrl', '')
                if not img_url:
                    continue
                if img_url.lower().endswith('.svg'):
                    continue
                # Skip URLs from blocked websites
                if any(domain in img_url.lower() for domain in self.skip_websites):
                    print(f"  [skip] Blocked domain — skipping: {img_url[:60]}...")
                    continue
                image_urls.append(img_url)

            return image_urls
            
        except Exception as e:
            print(f"  Error searching images for '{query[:50]}...': {e}")
            return []
    
    def _score_images_with_ccmr(
        self,
        query: str,
        candidate_images: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Score images using Caption-Conditioned Multimodal Retrieval (CCMR).
        
        Algorithm:
          Step 1 — CLIP encode:
            q = normalize(CLIP_text(query))
            c = normalize(CLIP_text(caption))   # from context file or VLM
            i_j = normalize(CLIP_image(image_j))

          Step 2 — Feature-level fusion:
            q' = normalize(q + λ·c)             # λ = self.lambda_prior

          Step 3 — Ranking:
            score_j = cos(q', i_j)
        
        Args:
            query: Slide image query from GenerateQueryAgent
            candidate_images: List of dicts with 'path', 'source', 'caption' keys
            
        Returns:
            List of candidates with 'ccmr_score' added
        """
        scored_images = []
        
        # Encode query with CLIP text encoder
        query_inputs = self.clip_processor(
            text=[query],
            return_tensors="pt",
            padding=True,
            truncation=True
        )
        with torch.no_grad():
            q = self.clip_model.get_text_features(**query_inputs)
            q = q / q.norm(dim=-1, keepdim=True)  # normalize
        
        for img_info in candidate_images:
            try:
                img_path = img_info['path']
                caption = img_info.get('caption', '')
                
                # Step 1 — Encode caption (if available)
                if caption:
                    cap_inputs = self.clip_processor(
                        text=[caption],
                        return_tensors="pt",
                        padding=True,
                        truncation=True
                    )
                    with torch.no_grad():
                        c = self.clip_model.get_text_features(**cap_inputs)
                        c = c / c.norm(dim=-1, keepdim=True)
                    
                    # Step 2 — Feature-level fusion: q' = normalize(q + λ·c)
                    q_prime = q + self.lambda_prior * c
                    q_prime = q_prime / q_prime.norm(dim=-1, keepdim=True)
                else:
                    # No caption available, fall back to raw query
                    q_prime = q
                
                # Step 3 — Encode image and compute cosine similarity
                image = Image.open(img_path).convert('RGB')
                image_inputs = self.clip_processor(
                    images=image,
                    return_tensors="pt"
                )
                with torch.no_grad():
                    i_j = self.clip_model.get_image_features(**image_inputs)
                    i_j = i_j / i_j.norm(dim=-1, keepdim=True)
                    
                    score = (q_prime @ i_j.T).item()
                
                scored_images.append({
                    'path': img_path,
                    'source': img_info['source'],
                    'caption': caption,
                    'ccmr_score': score
                })
                
            except Exception as e:
                print(f"  Error scoring image {img_info['path']}: {e}")
                scored_images.append({
                    'path': img_info['path'],
                    'source': img_info['source'],
                    'caption': img_info.get('caption', ''),
                    'ccmr_score': 0.0
                })
        
        return scored_images


# Main function for testing
def main():
    """Test the ImageDistribution class with CCMR"""
    print("=" * 60)
    print("Testing ImageDistribution with CCMR")
    print("=" * 60)
    
    # Initialize the distributor
    distributor = ImageDistribution()
    
    # Sample data
    lecture_id = "lec_6895e38a"
    
    # Load visualization queries
    queries_path = f"data/lectures/{lecture_id}_visualization_queries.json"
    with open(queries_path, 'r') as f:
        need_visualization = json.load(f)
    
    # Load aggregated media (from visual_aggregation output)
    from src.multimodal.agents.visual_aggregation import VisualAggregation
    lecture_path = f"data/lectures/{lecture_id}.json"
    with open(lecture_path, 'r', encoding='utf-8') as f:
        lecture_dict = json.load(f)
    
    aggregator = VisualAggregation()
    aggregated_media = aggregator.aggregate_media_from_lecture(lecture_dict)
    
    # Track used images
    used_images = set()
    
    print(f"\nDistributing images for {len(need_visualization)} slides...")
    print(f"Initial total_images in aggregated_media: {aggregated_media['total_images']}")
    
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
        print(f"  CCMR Score: {dist['ccmr_score']:.3f}")
        print(f"  Source: {dist['source']}")
        print(f"  Caption: {dist['caption'][:80]}...")
    
    print(f"\nFinal total_images in aggregated_media: {aggregated_media['total_images']}")
    print(f"Saved distributions to: data/lectures/{lecture_id}_image_distributions.json")


if __name__ == "__main__":
    main()
