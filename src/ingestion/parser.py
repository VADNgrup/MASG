from pathlib import Path
from typing import Dict, List, Any, Optional
from llama_parse import LlamaParse
from src.utils.config import config

class ParsedContent:
    def __init__(self):
        self.text_blocks: List[str] = []
        self.tables: List[Dict[str, Any]] = []
        self.images: List[Dict[str, Any]] = []
        self.page_count: int = 0

class DocumentParser:
    def __init__(self):
        self.parser = LlamaParse(
            api_key=config.LLAMA_CLOUD_API_KEY,
            result_type="markdown",
            verbose=True,
            language="vi",
        )
    
    def parse_document(self, file_path: Path) -> ParsedContent:
        documents = self.parser.load_data(str(file_path))
        
        content = ParsedContent()
        
        for doc in documents:
            content.text_blocks.append(doc.text)
            
            if hasattr(doc, 'metadata'):
                metadata = doc.metadata
                
                if 'page_number' in metadata:
                    content.page_count = max(content.page_count, metadata.get('page_number', 0))
                
                if metadata.get('type') == 'table':
                    content.tables.append({
                        'content': doc.text,
                        'page_number': metadata.get('page_number', 0),
                        'metadata': metadata
                    })
                
                if metadata.get('type') == 'image' or 'image' in metadata:
                    content.images.append({
                        'page_number': metadata.get('page_number', 0),
                        'metadata': metadata,
                        'data': metadata.get('image_data')
                    })
        
        return content
    
    def extract_images_from_pdf(self, file_path: Path) -> List[Dict[str, Any]]:
        import fitz
        
        images = []
        pdf_document = fitz.open(str(file_path))
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            image_list = page.get_images(full=True)
            
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                base_image = pdf_document.extract_image(xref)
                
                images.append({
                    'page_number': page_num + 1,
                    'image_index': img_index,
                    'image_bytes': base_image['image'],
                    'image_ext': base_image['ext'],
                    'width': base_image.get('width', 0),
                    'height': base_image.get('height', 0)
                })
        
        pdf_document.close()
        return images

