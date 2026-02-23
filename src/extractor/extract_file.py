import llm_extension
import argparse
import uuid
import time
import logging

from pathlib import Path
from tqdm import tqdm
from src.utils.config import config
from src.ingestion.parser import DocumentParser
from src.ingestion.asset_manager import AssetManager
from src.ingestion.vision_model import VisionCaptionGenerator
from src.ingestion.context_builder import ContextWindowBuilder
from src.ingestion.image_filter import ImageFilter
from src.models.context import TableData
from src.ingestion.generate_charts import generate_charts_for_context
from llama_parse import LlamaParse
from src.utils.config import config

def llama_parse_pdf(pdf_path):
    parser = LlamaParse(
        api_key=config.LLAMA_CLOUD_API_KEY,
        result_type="markdown",
        verbose=True,
        language="vi",
    )
    documents = parser.load_data(str(pdf_path))
    full_text = ""
    for doc in documents:
        full_text = full_text + doc.text + "\n"
    return full_text

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
    
    print("[1/6] Parsing document and extract text with LlamaParse...")
    doc_parser = DocumentParser(input_path) #Text Extraction
    parsed_content = doc_parser.parse_document()
    print(f"✓ Extracted {parsed_content.page_count} pages")
    
    print("\n[2/6] Extracting and saving images...")
    asset_manager = AssetManager(document_id)
    images_data = parsed_content.images #Image Extraction
    for img_data in tqdm(images_data, desc="Saving images into assets manager"):
        asset_manager.save_image(
            image_bytes=img_data['image_bytes'],
            image_index=img_data['image_index'],
            caption=img_data['relevant_caption'],
        )          
    all_images = asset_manager.get_all_images()
    print(f"✓ Saved {len(all_images)} valid images")

    print(f"\n[3/6] Found {len(parsed_content.tables)} tables")
    tables_markdown = parsed_content.tables #Table Extraction
    tables_markdown = [TableData(**tbl) for tbl in parsed_content.tables]
    
    print("\n[4/6] Building context window...")
    builder = ContextWindowBuilder(document_id, input_path.name, start_time=processing_start)
    context = builder.build_context(
        parsed_content=parsed_content,
        tables_markdown=tables_markdown,
        images=all_images
    )
     ## Bonus: LLama Parse support PDF OCR on Vietnamese
    full_text = llama_parse_pdf(input_path)
    context.text_content.markdown = full_text

    print("\n[5/6] Saving context JSON...")
    output_path = builder.save_context(context)
    print(f"✓ Context saved to: {output_path}")
    
    print("\n[6/6] Generating charts for visualizable tables...")
    try:
        context = generate_charts_for_context(str(output_path))
        charts_generated = sum(1 for t in context.tables if t.chart_path is not None)
        print(f"✓ Generated {charts_generated} charts")
    except Exception as e:
        print(f"Warning: Chart generation failed: {e}")
        print("  Continuing without charts...")
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Document ID:     {document_id}")
    print(f"Pages:           {context.text_content.page_count}")
    print(f"Tables:          {context.metadata.total_tables}")
    print(f"Images (valid):  {context.metadata.total_images}")
    print(f"Processing Time: {context.metadata.processing_time_seconds}s")
    print(f"Output:          {output_path}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()

