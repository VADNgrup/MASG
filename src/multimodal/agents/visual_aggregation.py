import llm_extension
from langchain_openai import ChatOpenAI
from typing import List, Dict, Optional, Any
import json
from pathlib import Path


class VisualAggregation:
    def __init__(self, model: str = "gpt-4.1-nano"):
        self.llm = ChatOpenAI(model=model, temperature=0.4, max_tokens=16000)
        self.model = model
    
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
        # Extract source document ID from metadata
        metadata = lecture_dict.get('metadata', {})
        source_document_id = metadata.get('source_document_id')
        
        if not source_document_id:
            raise ValueError("No source_document_id found in lecture metadata")
        
        # Load the context file
        context_data = self._load_context_file(source_document_id)
        
        # Extract tables (at top level)
        tables = context_data.get('tables', [])
        
        # Extract images (from assets.images)
        assets = context_data.get('assets', {})
        images = assets.get('images', [])
        
        # Organize and return
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
        # Construct the context file path
        context_path = Path("data/context") / f"{source_document_id}.json"
        
        if not context_path.exists():
            raise FileNotFoundError(f"Context file not found: {context_path}")
        
        # Load and return the context data
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
        # Load the lecture file
        with open(lecture_json_path, 'r', encoding='utf-8') as f:
            lecture_dict = json.load(f)
        
        # Aggregate media
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
        
        # Determine output path
        if output_path is None:
            output_dir = Path("data/media")
            output_dir.mkdir(parents=True, exist_ok=True)
            source_id = aggregated['source_document_id']
            output_path = output_dir / f"{source_id}_media.json"
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(aggregated, f, indent=2, ensure_ascii=False)
        
        return str(output_path)


# Main function for testing
def main():
    """Test the ImageAggregation class"""
    print("=" * 60)
    print("Testing ImageAggregation")
    print("=" * 60)
    
    # Initialize the aggregator
    aggregator = VisualAggregation()
    
    # Path to the lecture JSON file
    lecture_path = "data/lectures/lec_607fe87f.json"
    
    print(f"\nLoading lecture: {lecture_path}")
    
    try:
        # Aggregate media from lecture file
        result = aggregator.aggregate_from_lecture_file(lecture_path)
        
        # Display results
        print(f"\n✅ Successfully aggregated media!")
        print(f"\nSource Document ID: {result['source_document_id']}")
        print(f"Total Tables: {result['total_tables']}")
        print(f"Total Images: {result['total_images']}")
        
        # Show sample tables
        if result['tables']:
            print(f"\n📊 Sample Tables (showing first 2):")
            for i, table in enumerate(result['tables'][:2], 1):
                print(f"\n  Table {i}:")
                print(f"    Page: {table.get('page_number', 'N/A')}")
                print(f"    Caption: {table.get('caption', 'No caption')[:80]}...")
                if 'bbox' in table:
                    print(f"    BBox: {table['bbox']}")
        
        # Show sample images
        if result['images']:
            print(f"\n🖼️  Sample Images (showing first 2):")
            for i, image in enumerate(result['images'][:2], 1):
                print(f"\n  Image {i}:")
                print(f"    Page: {image.get('page_number', 'N/A')}")
                print(f"    Caption: {image.get('caption', 'No caption')[:80]}...")
                if 'bbox' in image:
                    print(f"    BBox: {image['bbox']}")
        
        # Save to file
        print("\n" + "=" * 60)
        print("Saving aggregated media to file...")
        
        with open(lecture_path, 'r', encoding='utf-8') as f:
            lecture_dict = json.load(f)
        
        output_path = aggregator.save_aggregated_media(lecture_dict)
        print(f"✅ Saved to: {output_path}")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()