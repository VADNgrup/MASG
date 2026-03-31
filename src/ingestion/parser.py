import os
import llm_extension
from src.utils.file_utils import ensure_dir
import re
import logging
from PIL import Image
from pathlib import Path
from typing import Dict, List, Any, Optional
from src.utils.config import config
from src.utils.parse_llm_response import clear_think
from io import BytesIO
from src.ingestion.table_filter import TableFilter
from src.ingestion.image_filter import ImageFilter
from src.ingestion.vision_model import VisionCaptionGenerator
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.config.parser import ConfigParser
from marker.converters.table import TableConverter
from marker.renderers.markdown import MarkdownRenderer
from marker.schema import BlockTypes
from marker.schema.blocks import Table
from marker.schema.document import Document
from marker.models import create_model_dict
import json
import base64
import fitz 
from openai import OpenAI

_log = logging.getLogger(__name__)


IMAGE_RESOLUTION_SCALE = 2.0

os.environ["TORCH_DEVICE"] = "cuda"

class ParsedContent:
    def __init__(self):
        self.full_text: str = ""
        self.tables: List[Dict[str, Any]] = []  # Changed from List[str] to match actual data
        self.images: List[Dict[str, Any]] = []
        self.page_count: int = 0

class DocumentParser:
    def __init__(self, pdf_path: Path):
        config_dict = {
            "output_format": "markdown",
            "use_llm": False,
        }
        parser = ConfigParser(config_dict)

        converter = PdfConverter(
            config=parser.generate_config_dict(),
            artifact_dict=create_model_dict(),
        )

        self.pdf_path = pdf_path
        self.doc = fitz.open(self.pdf_path)
        rendered = converter(self.pdf_path)
        self.full_text, _, self.images = text_from_rendered(rendered)
        self.table_filter = TableFilter()
        
    def parse_document(self, document_id: str = "") -> ParsedContent:
        content = ParsedContent()
        content.full_text = self.extract_texts()
        content.tables = self.extract_tables(document_id)
        content.images = self.extract_figures()
        content.page_count = len(self.doc)
        self.doc.close()
        return content

    def extract_texts(self) -> str:
        return self.full_text
        
    def extract_tables(self, document_id: str = "") -> List[Dict[str, Any]]:
        tables = []
        table_page_information = self.get_table_page_information()
        
        # Save cropped table images if document_id is provided
        table_image_paths = {}
        if document_id:
            table_image_paths = self.save_table_images(table_page_information, document_id)
        
        table_index = 0
        for table_page in table_page_information:
            table_markdown = table_page['table']
            table_caption = table_page['caption']
            should_visualize = self.table_filter.should_visualize_table(table_markdown, table_caption)
            table_id = f"table_{table_index+1:03d}"
            tables.append({
                'table_id': table_id,
                'markdown': table_markdown,
                'table_caption': table_caption,
                'should_visualize': should_visualize,
                'image_table_path': table_image_paths.get(table_index),
            })
            table_index += 1
        return tables

    def extract_figures(self) -> List[Dict[str, Any]]:
        images = []
        image_page_information = self.get_image_page_information(self.images)
        image_index = 0
        for image_page in image_page_information:
            image_with_number = re.search(r'\S+\s+\d+', image_page['caption'])
            if image_with_number:
                image_with_number = image_with_number.group() #Eg: "Table 1"
                # Tìm tất cả các dòng trong full_text có nhắc đến image_with_number
                # Dùng regex linh hoạt để khớp dù có khoảng trắng thừa giữa "Figure" và số
                escaped = re.escape(image_with_number)              # e.g. "Figure\ 3"
                flexible = escaped.replace(r'\ ', r'\s+')          # cho phép nhiều khoảng trắng
                pattern = re.compile(flexible, re.IGNORECASE)

                matched_lines = []
                for line in self.full_text.splitlines():
                    if pattern.search(line):
                        stripped = line.strip()
                        if stripped:
                            matched_lines.append(stripped)

                reference_context = "\n".join(matched_lines)
            else:
                reference_context = ""
            img_bytes = BytesIO()
            img = image_page['image']
            img.save(img_bytes, format='PNG')
            images.append({
                'image_index':image_index,
                'image_bytes':img_bytes.getvalue(),
                'page_number': image_page['page'],
                'raw_name': image_page['raw_name'],
                'relevant_caption': image_page['caption'],
                'reference_context': reference_context,
            })
            image_index += 1
        return images
    
    def get_image_page_information(self, images) -> List[Dict[str, Any]]:
        image_page_information = []
        for key, value in images.items():
            page_index = re.search(r'page_(\d+)', key)
            image_page = {"page": page_index.group(1), "raw_name": key, "image": value}
            image_page_information.append(image_page)

        # Đếm số ảnh trên mỗi trang
        image_page_count = {}
        for image_page in image_page_information:
            page = image_page['page']
            image_page_count[page] = image_page_count.get(page, 0) + 1

        # Lấy caption cho từng trang (gọi get_caption một lần / trang)
        page_captions: Dict[str, List[str]] = {}
        for page, count in image_page_count.items():
            page_captions[page] = self.get_caption(int(page), count, type_search="image")

        # Gán caption vào từng phần tử theo thứ tự xuất hiện trong trang
        page_index_tracker: Dict[str, int] = {}
        for image_page in image_page_information:
            page = image_page['page']
            idx = page_index_tracker.get(page, 0)
            image_page['caption'] = page_captions[page][idx]
            page_index_tracker[page] = idx + 1

        # Postprocessing: sinh caption cho những ảnh bị "No Caption"
        full_text = self.extract_texts()
        text_lines = full_text.splitlines()
        vision_generator = VisionCaptionGenerator()

        for image_page in image_page_information:
            if image_page['caption'].strip().lower() == "no caption":
                raw_name = image_page['raw_name']

                # Tìm dòng chứa raw_name trong full text
                target_line_idx = None
                for i, line in enumerate(text_lines):
                    if raw_name in line:
                        target_line_idx = i
                        break

                # Lấy ±15 dòng làm context
                if target_line_idx is not None:
                    start = max(0, target_line_idx - 15)
                    end = min(len(text_lines), target_line_idx + 15 + 1)
                    context = "\n".join(text_lines[start:end])
                else:
                    context = ""

                # Chuyển ảnh sang bytes PNG
                img_bytes_io = BytesIO()
                img = image_page['image']
                img.save(img_bytes_io, format='PNG')
                img_bytes = img_bytes_io.getvalue()

                # Sinh caption bằng VisionCaptionGenerator
                image_page['caption'] = vision_generator.generate_caption(img_bytes, context)

        return image_page_information

    
    def save_table_images(
        self,
        table_page_information: List[Dict[str, Any]],
        document_id: str,
    ) -> Dict[int, str]:
        """Crop table images from PDF using bbox and save to assets directory.
        Returns a dict mapping table_index -> relative image path.
        """
        from src.utils.config import config as app_config

        image_dir = app_config.ASSETS_DIR / document_id / "images"
        ensure_dir(image_dir)

        table_image_paths: Dict[int, str] = {}
        for idx, table_page in enumerate(table_page_information):
            bbox = table_page.get('bbox')
            if bbox is None:
                continue

            page_index = table_page['page']
            page = self.doc.load_page(page_index)
            clip_rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
            pix = page.get_pixmap(dpi=150, clip=clip_rect)

            file_name = f"table_{idx+1:03d}.png"
            file_path = image_dir / file_name
            pix.save(str(file_path))

            relative_path = str(file_path.relative_to(app_config.BASE_DIR))
            table_image_paths[idx] = relative_path

        return table_image_paths

    def get_table_page_information(self) -> List[Dict[str, Any]]:
        config_parser = ConfigParser({})
        converter = TableConverter(
            artifact_dict=create_model_dict(),
            config=config_parser.generate_config_dict(),
        )
        document = converter.build_document(self.pdf_path)
        renderer = MarkdownRenderer()
        markdown_output = renderer(document)
        tables = document.contained_blocks((BlockTypes.Table,))
        tables_content = markdown_output.markdown.split("\n\n")
        table_page_information = []
        for i in range(len(tables)):
            bbox = tables[i].polygon.bbox if hasattr(tables[i], 'polygon') and tables[i].polygon else None
            table_page = {
                "page": tables[i].page_id,
                "table": tables_content[i],
                "bbox": bbox,
            }
            table_page_information.append(table_page)

        # Đếm số bảng trên mỗi trang
        table_page_count = {}
        for table_page in table_page_information:
            page = table_page['page']
            table_page_count[page] = table_page_count.get(page, 0) + 1

        # Lấy caption cho từng trang (gọi get_caption một lần / trang)
        page_captions: Dict[str, List[str]] = {}
        for page, count in table_page_count.items():
            page_captions[page] = self.get_caption(int(page), count, type_search="table")

        # Gán caption vào từng phần tử theo thứ tự xuất hiện trong trang
        page_index_tracker: Dict[str, int] = {}
        for table_page in table_page_information:
            page = table_page['page']
            idx = page_index_tracker.get(page, 0)
            table_page['caption'] = page_captions[page][idx]
            page_index_tracker[page] = idx + 1

        # Postprocessing: sinh caption cho những bảng bị "No Caption"
        full_text = self.extract_texts()
        text_lines = full_text.splitlines()
        vision_generator = VisionCaptionGenerator()

        for table_page in table_page_information:
            if table_page['caption'].strip().lower() == "no caption":
                table_markdown_content = table_page['table']
                
                # Tìm dòng đầu tiên của bảng trong full text
                first_table_line = table_markdown_content.strip().splitlines()[0] if table_markdown_content.strip() else ""
                target_line_idx = None
                for i, line in enumerate(text_lines):
                    if first_table_line and first_table_line in line:
                        target_line_idx = i
                        break

                # Lấy ±15 dòng làm context
                if target_line_idx is not None:
                    start = max(0, target_line_idx - 15)
                    end = min(len(text_lines), target_line_idx + 15 + 1)
                    context = "\n".join(text_lines[start:end])
                else:
                    context = ""

                # Sinh caption bằng VisionCaptionGenerator
                table_page['caption'] = vision_generator.generate_table_caption(table_markdown_content, context)

        return table_page_information

    
    def get_caption(self, page_id, object_number, type_search = "image") -> List[str]:
        BASE_URL = f"{config.VLM_BASE_URL}v1"
        API_KEY = config.VLM_API_KEY
        MODEL = config.VLM_MODEL_NAME
        page_index = page_id
        page = self.doc.load_page(page_index)
        pix = page.get_pixmap(dpi=200)
        image_bytes = pix.tobytes("png")
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        client = OpenAI(
            base_url=BASE_URL,
            api_key=API_KEY
        )
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""This page contains {object_number} {type_search}. Extract the caption for each {type_search}, if available.
                            Return a JSON array of exactly {object_number} strings, one caption per {type_search}, in the order they appear on the page. If a {type_search} has no caption, use "No Caption" as the value. Do not include any explanation, only output the JSON array.
                            Example output (if the 2nd {type_search} has no caption): ["Caption of first {type_search}", "No Caption", "Caption of third {type_search}"]"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.2
        )
        raw_content = clear_think(response.choices[0].message.content)
        match = re.search(r'\[.*\]', raw_content, re.DOTALL)
        if match:
            captions: List[str] = json.loads(match.group())
        else:
            captions = []
        # Đảm bảo đúng object_number phần tử
        captions = captions[:object_number]
        captions += ["No Caption"] * (object_number - len(captions))
        return captions
    
