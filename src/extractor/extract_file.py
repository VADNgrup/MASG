import argparse
import uuid
import time
import logging
import os
from pathlib import Path
from tqdm import tqdm
from src.utils.config import config, Config
from src.ingestion.parser import DocumentParser
from src.ingestion.asset_manager import AssetManager
from src.ingestion.vision_model import VisionCaptionGenerator
from src.ingestion.context_builder import ContextWindowBuilder
from src.ingestion.image_filter import ImageFilter
from src.models.context import TableData
from src.ingestion.generate_charts import generate_charts_for_context
from src.ingestion.vector_store import VectorStoreManager

def extract_file(input_path):
    config.validate()
    processing_start = time.time()
    document_id = Path(input_path).stem
    print(f"\n{'=' * 60}")
    print(f'Phase 1: Document Extraction for {document_id}')
    print(f"{'=' * 60}\n")
    parsed_context_path = Path(Config.CONTEXT_DIR / f'{document_id}.json')
    if parsed_context_path.exists():
        print(f'Document {document_id} already exists in raw directory')
        print(f"\n{'=' * 60}")
        print(f'End Phase 1: Document Extraction for {document_id}')
        print(f"{'=' * 60}\n")
        return parsed_context_path
    print('[1/6] Marker Parsing...')
    doc_parser = DocumentParser(input_path)
    parsed_content = doc_parser.parse_document(document_id)
    print('\n[2/6] Generating VLM captions and saving images...')
    asset_manager = AssetManager(document_id)
    vlm = VisionCaptionGenerator()
    images_data = parsed_content.images
    for img_data in tqdm(images_data, desc='Saving images & captions'):
        vlm_caption = vlm.generate_caption(img_data['image_bytes'], img_data['reference_context'])
        asset_manager.save_image(image_bytes=img_data['image_bytes'], image_index=img_data['image_index'], caption=vlm_caption, reference_context=img_data['reference_context'])
    all_images = asset_manager.get_all_images()
    print(f'Saved {len(all_images)} valid images with VLM captions')
    print(f'\n[3/6] Found {len(parsed_content.tables)} tables')
    tables_markdown = parsed_content.tables
    tables_markdown = [TableData(**tbl) for tbl in parsed_content.tables]
    print('\n[4/6] Building context window...')
    builder = ContextWindowBuilder(document_id, Path(input_path).name, start_time=processing_start)
    context = builder.build_context(parsed_content=parsed_content, tables_markdown=tables_markdown, images=all_images)
    print('\n[5/6] Saving context JSON...')
    output_path = builder.save_context(context)
    print(f'Context saved to: {output_path}')
    print('\n[6/6] Generating charts for visualizable tables...')
    try:
        context = generate_charts_for_context(str(output_path))
        charts_generated = sum((1 for t in context.tables if t.chart_path is not None))
        print(f'Generated {charts_generated} charts')
    except Exception as e:
        print(f'Warning: Chart generation failed: {e}')
        print('  Continuing without charts...')

    print('\n[7/7] Chunking Markdown & Building Local FAISS Vector Store...')
    vsm = VectorStoreManager(document_id)
    vsm.build_and_save(parsed_content.full_text)
    print(f"\n{'=' * 60}")
    print('SUMMARY')
    print(f"{'=' * 60}")
    print(f'Document ID:     {document_id}')
    print(f'Pages:           {context.text_content.page_count}')
    print(f'Tables:          {context.metadata.total_tables}')
    print(f'Images (valid):  {context.metadata.total_images}')
    print(f'Processing Time: {context.metadata.processing_time_seconds}s')
    print(f'Output:          {output_path}')
    print(f"\n{'=' * 60}")
    print(f'End Phase 1: Document Extraction for {document_id}')
    print(f"{'=' * 60}\n")
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Phase 1: Multimodal Ingestion Pipeline')
    parser.add_argument('--input', required=True, help='Path to input PDF/Docx file')
    args = parser.parse_args()
    input_path = args.input
    if not os.path.exists(input_path):
        print(f'Error: Input file not found: {input_path}')
        return
    else:
        extract_file(input_path)
if __name__ == '__main__':
    main()