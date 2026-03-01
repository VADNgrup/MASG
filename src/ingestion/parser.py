import os
import llm_extension
import re
import logging
from PIL import Image
from pathlib import Path
from typing import Dict, List, Any, Optional
from src.utils.config import config
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
            "use_llm": True,
            # Ép dùng OpenAIService
            "llm_service": "marker.services.openai.OpenAIService",
            # Ollama config
            "openai_base_url": config.VLM_BASE_URL,
            "openai_api_key": config.VLM_API_KEY,
            "openai_model": config.VLM_MODEL_NAME,
        }
        parser = ConfigParser(config_dict)

        converter = PdfConverter(
            config=parser.generate_config_dict(),
            artifact_dict=create_model_dict(),
            processor_list=parser.get_processors(),
            renderer=parser.get_renderer(),
            llm_service=parser.get_llm_service(),
        )

        print("🔍 Converting PDF with Ollama LLM...")
        self.pdf_path = pdf_path
        self.doc = fitz.open(self.pdf_path)
        rendered = converter(self.pdf_path)
        self.full_text, _, self.images = text_from_rendered(rendered)
        self.table_filter = TableFilter()
        
    def parse_document(self) -> ParsedContent:
        content = ParsedContent()
        content.full_text = self.extract_texts()
        content.tables = self.extract_tables()
        content.images = self.extract_figures()
        content.page_count = len(self.doc)
        self.doc.close()
        return content

    def extract_texts(self) -> str:
        return self.full_text
        
    def extract_tables(self) -> List[Dict[str, Any]]:
        tables = []
        table_page_information = self.get_table_page_information()
        table_index = 0
        for table_page in table_page_information:
            table_markdown = table_page['table']
            table_caption = table_page['caption']
            should_visualize = self.table_filter.should_visualize_table(table_markdown)
            tables.append({
                'table_id': f"table_{table_index+1:03d}",
                'markdown': table_markdown,
                'table_caption': table_caption,
                'should_visualize': should_visualize
            })
            table_index += 1
        return tables

    def extract_figures(self) -> List[Dict[str, Any]]:
        images = []
        image_page_information = self.get_image_page_information(self.images)
        image_index = 0
        for image_page in image_page_information:
            img_bytes = BytesIO()
            img = image_page['image']
            img.save(img_bytes, format='PNG')
            images.append({
                'image_index':image_index,
                'image_bytes':img_bytes.getvalue(),
                'page_number': image_page['page'],
                'raw_name': image_page['raw_name'],
                'relevant_caption': image_page['caption'],
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
            table_page = {"page": tables[i].page_id, "table": tables_content[i]}
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
        raw_content = response.choices[0].message.content.strip()
        match = re.search(r'\[.*\]', raw_content, re.DOTALL)
        if match:
            captions: List[str] = json.loads(match.group())
        else:
            captions = []
        # Đảm bảo đúng object_number phần tử
        captions = captions[:object_number]
        captions += ["No Caption"] * (object_number - len(captions))
        return captions
    
