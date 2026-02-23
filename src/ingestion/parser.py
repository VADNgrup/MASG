import llm_extension
import re
import logging
from PIL import Image
from pathlib import Path
from typing import Dict, List, Any, Optional
from docling.document_converter import DocumentConverter
from src.utils.config import config
from src.ingestion.table_filter import TableFilter
from io import BytesIO
from src.ingestion.image_filter import ImageFilter
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from src.ingestion.vision_model import VisionCaptionGenerator

_log = logging.getLogger(__name__)


IMAGE_RESOLUTION_SCALE = 2.0

class ParsedContent:
    def __init__(self):
        self.text_blocks: List[str] = []
        self.tables: List[Dict[str, Any]] = []  # Changed from List[str] to match actual data
        self.images: List[Dict[str, Any]] = []
        self.page_count: int = 0

class DocumentParser:
    def __init__(self, pdf_path: Path):
        pipeline_options = PdfPipelineOptions()
        pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
        pipeline_options.generate_page_images = True
        pipeline_options.generate_picture_images = True
        pipeline_options.ocr_options.lang = ["vi", "en"]
        doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        self.pdf_path = pdf_path
        self.result = doc_converter.convert(self.pdf_path)
        self.table_filter = TableFilter()
        self.image_filter = ImageFilter()
        
    def parse_document(self) -> ParsedContent:
        content = ParsedContent()
        content.text_blocks = self.extract_texts()
        content.tables = self.extract_tables()
        content.images = self.extract_figures()
        content.page_count = len(self.result.document.pages)
        return content

    def extract_texts(self) -> List[str]:
        doc = self.result.document
        pages_markdown = {}  
        for page_no, page in doc.pages.items():
            page_text_parts = []
            
            for item, level in doc.iterate_items():
                if hasattr(item, 'prov') and item.prov:
                    for prov in item.prov:
                        if hasattr(prov, 'page_no') and prov.page_no == page_no:
                            item_type = type(item).__name__
                            # Handle section headers with proper markdown formatting
                            if item_type == 'SectionHeaderItem':
                                if hasattr(item, 'text') and item.text:
                                    heading_level = min(level + 1, 6)  # Markdown supports h1-h6
                                    heading_prefix = '#' * heading_level
                                    page_text_parts.append(f"{heading_prefix} {item.text}")
                            # Handle regular text
                            elif hasattr(item, 'text') and item.text:
                                page_text_parts.append(item.text)
                            # Handle tables (TableItem only, not PictureItem)
                            elif item_type == 'TableItem' and hasattr(item, 'export_to_markdown'):
                                table_md = item.export_to_markdown()
                                if table_md:
                                    page_text_parts.append(table_md)
                            break
            
            page_markdown = "\n\n".join(page_text_parts)
            pages_markdown[page_no] = page_markdown
        
        # Convert dict to sorted list by page number
        sorted_pages = sorted(pages_markdown.items())
        return [content for _, content in sorted_pages]

    def extract_tables(self) -> List[Dict[str, Any]]:
        tables = []

        # Get main table caption within 2 lines
        def get_main_table_caption(cap):
            CAPTION_RE = re.compile(
                r'^\s*(table|tab\.?,|bảng)\s*\d+\s*[:\.]',
                re.IGNORECASE
            )
            if bool(CAPTION_RE.match(cap)): return True
            else: return False
        lines = self.result.document.export_to_markdown().splitlines()
        for idx, table in enumerate(self.result.document.tables):
            table_markdown = table.export_to_markdown()
            table_arr = table_markdown.splitlines()
            prev_line_table, next_line_table = table_arr[0], table_arr[-1]
            prev_line = ""
            next_line = ""
            table_caption = ""
            for i, line in enumerate(lines):
                if prev_line_table and prev_line_table in line:
                    prev_line = ""
                    for j in range(i - 1, -1, -1):
                        text = lines[j].strip()
                        if text and not text.startswith("<!--"):
                            prev_line = text
                            break
                elif next_line_table and next_line_table in line:
                    next_line = ""
                    for j in range(i + 1, len(lines)):
                        text = lines[j].strip()
                        if text and not text.startswith("<!--"):
                            next_line = text
                            break
            if get_main_table_caption(prev_line): 
                table_caption = prev_line
            elif get_main_table_caption(next_line): 
                table_caption = next_line
            else:
                # If no caption found, use vision caption generator with table context
                table_context = f"Table need caption\n{prev_line}\n{next_line}"
                vision_caption_generator = VisionCaptionGenerator()
                table_caption = vision_caption_generator.generate_table_caption(
                    table_markdown=table_markdown,
                    context=table_context
                )

            # Check if table should be visualized
            should_visualize = self.table_filter.should_visualize_table(table_markdown)
            tables.append({
                'table_id': f"table_{idx+1:03d}",
                'markdown': table_markdown,
                'table_caption': table_caption,
                'should_visualize': should_visualize
            })
        return tables

    def extract_figures(self, ratio = 0.02) -> List[Dict[str, Any]]:
        # Get main caption within 2 lines
        def get_main_image_caption(cap):
            CAPTION_RE = re.compile(
                r'^\s*(figure|fig\.?|hình)\s*\d+\s*[:\.]',
                re.IGNORECASE
            )
            if bool(CAPTION_RE.match(cap)): return True
            else: return False
        
        # Get Every Relevant Image Caption
        vision_caption_generator = VisionCaptionGenerator()
        lines = self.result.document.export_to_markdown().splitlines()
        captions = []
        for i, line in enumerate(lines):
            if "<!-- image -->" in line:
                # Find nearest line above
                prev_line = ""
                for j in range(i - 1, -1, -1):
                    text = lines[j].strip()
                    if text and not text.startswith("<!--"):
                        prev_line = text
                        break
                
                if get_main_image_caption(prev_line):
                    captions.append(prev_line)
                    continue

                # Find nearest line below
                next_line = ""
                for j in range(i + 1, len(lines)):
                    text = lines[j].strip()
                    if text and not text.startswith("<!--"):
                        next_line = text
                        break

                if get_main_image_caption(next_line):
                    captions.append(next_line)
                    continue
                # If no caption found, use vision caption generator
                image_context = "Image need caption" + prev_line + "\n" + next_line
                captions.append(image_context)

        # Find Document Size
        doc_area = 0
        image_index = 0
        for page_no, page in self.result.document.pages.items():
            page_no = page.page_no
            pil_img = page.image.pil_image
            w, h = pil_img.size
            print("\nDocument size: {w} x {h}\n")
            doc_area = w * h
            break
        
        # Get Image having valid size
        image_index = 0
        actual_image_index = 0
        images = []
        for element, _level in self.result.document.iterate_items():
            if isinstance(element, PictureItem):
                img_bytes = BytesIO()
                element.get_image(self.result.document).save(img_bytes, "PNG")
                w, h = Image.open(img_bytes).size
                if (w*h) / doc_area > ratio: # Check Valid Size Image

                    # Check if image need caption
                    if "Image need caption" in captions[actual_image_index]:
                        vision_caption_generator = VisionCaptionGenerator()
                        captions[actual_image_index] = vision_caption_generator.generate_caption(img_bytes.getvalue(), captions[actual_image_index])
                    
                    images.append({
                        'image_index':image_index,
                        'image_bytes':img_bytes.getvalue(),
                        'relevant_caption': captions[actual_image_index],
                    })
                    image_index += 1
                actual_image_index += 1

        return images
