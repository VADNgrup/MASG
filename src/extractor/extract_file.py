import argparse
import time
import os
from pathlib import Path
from src.utils.config import config, Config
from src.ingestion.parser import DocumentParser
from src.ingestion.context_builder import ContextWindowBuilder
from src.ingestion.compact_context import build_compact_context, save_compact_context, compact_context_path
from src.utils.file_utils import load_json
from src.models.context import DocumentContext

def extract_file(input_path):
    config.validate()
    processing_start = time.time()
    document_id = Path(input_path).stem
    
    print(f"\n{'=' * 60}")
    print(f'Phase 1: Hybrid VLM Extraction for {document_id}')
    print(f"{'=' * 60}\n")
    
    parsed_context_path = Path(Config.CONTEXT_DIR / f'{document_id}.json')
    if parsed_context_path.exists():
        print(f'Document {document_id} already exists in context directory. Skipping...')
        if not compact_context_path(document_id).exists():
            context = DocumentContext(**load_json(parsed_context_path))
            compact = build_compact_context(
                document_id=context.document_id,
                source_file=context.source_file,
                markdown=context.text_content.markdown,
                page_count=context.text_content.page_count,
            )
            compact_path = save_compact_context(compact)
            print(f'Compact context saved to: {compact_path}')
        return parsed_context_path

    print('[1/3] Parsing document with Hybrid VLM logic...')
    doc_parser = DocumentParser(input_path)
    parsed_content = doc_parser.parse_document(document_id)

    print('\n[2/3] Building context JSON...')
    builder = ContextWindowBuilder(document_id, Path(input_path).name, start_time=processing_start)
    
    context = builder.build_context(
        parsed_content=parsed_content, 
        tables_markdown=[], 
        images=parsed_content.images
    )
    
    output_path = builder.save_context(context)
    print(f'Context saved to: {output_path}')
    compact = build_compact_context(
        document_id=document_id,
        source_file=Path(input_path).name,
        markdown=parsed_content.full_text,
        page_count=parsed_content.page_count,
    )
    compact_path = save_compact_context(compact)
    print(f'Compact context saved to: {compact_path}')

    print(f"\n{'=' * 60}")
    print('SUMMARY')
    print(f"{'=' * 60}")
    print(f'Document ID:     {document_id}')
    print(f'Pages:           {parsed_content.page_count}')
    print(f'Processing Time: {time.time() - processing_start:.2f}s')
    print(f'Output:          {output_path}')
    print(f"\n{'=' * 60}\n")
    
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Phase 1: Hybrid VLM Ingestion Pipeline')
    parser.add_argument('--input', required=True, help='Path to input PDF file')
    args = parser.parse_args()
    input_path = args.input
    if not os.path.exists(input_path):
        print(f'Error: Input file not found: {input_path}')
        return
    else:
        extract_file(input_path)

if __name__ == '__main__':
    main()
