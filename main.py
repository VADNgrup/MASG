import argparse
import uuid
from pathlib import Path
from tqdm import tqdm
import time

from src.utils.config import config
from src.ingestion.parser import DocumentParser
from src.ingestion.table_converter import TableToMarkdownConverter
from src.ingestion.asset_manager import AssetManager
from src.ingestion.vision_model import VisionCaptionGenerator
from src.ingestion.context_builder import ContextWindowBuilder
from src.ingestion.image_filter import ImageFilter
from src.models.context import TableData

def main():
    parser = argparse.ArgumentParser(description="Phase 1: Multimodal Ingestion Pipeline")
    parser.add_argument("--input", required=True, help="Path to input PDF/Docx file")
    parser.add_argument("--output", default=None, help="Output directory for context JSON")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return
    
    config.validate()
    processing_start = time.time()
    
    document_id = str(uuid.uuid4())
    print(f"\n{'='*60}")
    print(f"Document ID: {document_id}")
    print(f"Source: {input_path.name}")
    print(f"{'='*60}\n")
    
    print("[1/6] Parsing document with LlamaParse...")
    doc_parser = DocumentParser()
    parsed_content = doc_parser.parse_document(input_path)
    print(f"✓ Extracted {parsed_content.page_count} pages")
    print(f"✓ Found {len(parsed_content.tables)} tables")
    
    print("\n[2/6] Converting tables to Markdown...")
    tables_markdown = []
    for idx, table in enumerate(parsed_content.tables):
        markdown = TableToMarkdownConverter.parse_and_convert(table)
        table_data = TableData(
            table_id=f"table_{idx+1:03d}",
            page_number=table.get('page_number', 0),
            markdown=markdown,
            raw_text=table.get('content', '')
        )
        tables_markdown.append(table_data)
    print(f"✓ Converted {len(tables_markdown)} tables")
    
    print("\n[3/6] Extracting and saving images...")
    asset_manager = AssetManager(document_id)
    image_filter = ImageFilter()
    
    filtered_count = 0
    
    if input_path.suffix.lower() == '.pdf':
        images_data = doc_parser.extract_images_from_pdf(input_path)
        
        for img_data in tqdm(images_data, desc="Filtering & saving images"):
            passed, reason, _ = image_filter.should_caption_image(img_data['image_bytes'])
            
            if not passed:
                filtered_count += 1
                continue
            
            asset_manager.save_image(
                image_bytes=img_data['image_bytes'],
                page_number=img_data['page_number'],
                image_index=img_data['image_index'],
                priority=1
            )
    
    all_images = asset_manager.get_all_images()
    print(f"✓ Saved {len(all_images)} valid images")
    print(f"✓ Filtered out {filtered_count} decoration/noise images (pre-filter)")
    
    print("\n[4/6] Classifying images and generating captions...")
    cache_file = config.ASSETS_DIR / document_id / "caption_cache.json"
    vision_generator = VisionCaptionGenerator(cache_file=cache_file)
    
    valid_images = []
    classified_out = 0
    
    for img in tqdm(all_images, desc="Classifying images"):
        img_path = config.BASE_DIR / img.file_path
        
        category, confidence = image_filter.classify_image_content(img_path)
        
        img.content_type = category
        
        invalid_categories = ["decoration", "header_footer", "noise"]
        if category in invalid_categories or confidence < 0.4:
            img.is_decoration = True
            classified_out += 1
        else:
            valid_images.append(img)
    
    print(f"✓ Classified {len(all_images)} images")
    print(f"✓ Filtered out {classified_out} more decorations (vision classification)")
    
    if valid_images:
        print(f"\nGenerating captions for {len(valid_images)} valid images...")
        
        image_data = [
            (config.BASE_DIR / img.file_path, img.image_id, img.content_type) 
            for img in valid_images
        ]
        
        captions = vision_generator.batch_generate_captions(image_data)
        
        for img in valid_images:
            if img.image_id in captions:
                caption_rag, caption_display = captions[img.image_id]
                img.caption_rag = caption_rag
                img.caption_display = caption_display
        
        print(f"✓ Generated captions for {len(captions)} images")
    else:
        print("✓ No valid images to caption")
    
    print("\n[5/6] Building context window...")
    builder = ContextWindowBuilder(document_id, input_path.name, start_time=processing_start)
    context = builder.build_context(
        parsed_content=parsed_content,
        tables_markdown=tables_markdown,
        images=valid_images
    )
    
    print("\n[6/6] Saving context JSON...")
    output_path = builder.save_context(context)
    print(f"✓ Context saved to: {output_path}")
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Document ID:     {document_id}")
    print(f"Pages:           {context.text_content.page_count}")
    print(f"Tables:          {context.metadata.total_tables}")
    print(f"Images (valid):  {context.metadata.total_images}")
    print(f"Filtered (pre):  {filtered_count}")
    print(f"Filtered (AI):   {classified_out}")
    print(f"Total extracted: {len(all_images) + filtered_count}")
    print(f"Processing Time: {context.metadata.processing_time_seconds}s")
    print(f"Output:          {output_path}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()

