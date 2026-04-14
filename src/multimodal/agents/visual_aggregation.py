from typing import List, Dict, Optional, Any
import json
from pathlib import Path


class VisualAggregation:
    
    def aggregate_media_from_lecture(self, lecture_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and aggregate tables and images from the context file associated with a lecture.
        
        Args:
            lecture_dict: Dictionary loaded from lecture JSON file (e.g., lec_607fe87f.json)
            
        Returns:
            Dictionary containing tables and images:
            {
                "tables": [...],
                "images": [...]
            }
        """
        metadata = lecture_dict.get('metadata', {})
        source_document_id = metadata.get('source_document_id')
        
        if not source_document_id:
            raise ValueError("No source_document_id found in lecture metadata")
        
        context_data = self._load_context_file(source_document_id)
        
        tables = context_data.get('tables', [])
        
        assets = context_data.get('assets', {})
        images = assets.get('images', [])
        
        result = {
            "tables": tables,
            "images": images,
            "source_document_id": source_document_id,
            "total_tables": len(tables),
            "total_images": len(images)
        }
        
        return result
    
    def _load_context_file(self, source_document_id: str) -> Dict[str, Any]:
        """
        Load the context JSON file for a given source document ID.
        
        Args:
            source_document_id: The source document ID (e.g., "607fe87f-b0f0-48b2-9c3d-ef5ccea059e1")
            
        Returns:
            Dictionary containing context data with tables and images
        """
        context_path = Path("data/context") / f"{source_document_id}.json"
        
        if not context_path.exists():
            raise FileNotFoundError(f"Context file not found: {context_path}")
        
        with open(context_path, 'r', encoding='utf-8') as f:
            context_data = json.load(f)
        
        return context_data
    
    def aggregate_from_lecture_file(self, lecture_json_path: str) -> Dict[str, Any]:
        """
        Load a lecture JSON file and aggregate its media.
        
        Args:
            lecture_json_path: Path to the lecture JSON file
            
        Returns:
            Dictionary containing tables and images
        """
        with open(lecture_json_path, 'r', encoding='utf-8') as f:
            lecture_dict = json.load(f)
        
        return self.aggregate_media_from_lecture(lecture_dict)
    
    def save_aggregated_media(
        self, 
        lecture_dict: Dict[str, Any], 
        output_path: Optional[str] = None
    ) -> str:
        """
        Aggregate media and save to a JSON file.
        
        Args:
            lecture_dict: Dictionary loaded from lecture JSON file
            output_path: Optional path for output file. If None, saves to data/media/
            
        Returns:
            Path to the saved output file
        """
        aggregated = self.aggregate_media_from_lecture(lecture_dict)
        
        if output_path is None:
            output_dir = Path("data/media")
            output_dir.mkdir(parents=True, exist_ok=True)
            source_id = aggregated['source_document_id']
            output_path = output_dir / f"{source_id}_media.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(aggregated, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
