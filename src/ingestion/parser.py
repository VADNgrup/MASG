import os
import fitz
import base64
import requests
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from tqdm import tqdm
from src.utils.config import config

_log = logging.getLogger(__name__)

class ParsedContent:
    def __init__(self):
        self.full_text: str = ''
        self.tables: List[Dict[str, Any]] = []
        self.images: List[Dict[str, Any]] = []
        self.page_count: int = 0

class DocumentParser:
    def __init__(self, pdf_path):
        self.pdf_path = Path(pdf_path) if isinstance(pdf_path, str) else pdf_path
        self.doc = fitz.open(str(self.pdf_path))
        self.model_url = config.VLM_BASE_URL
        if self.model_url and not self.model_url.endswith("/chat/completions"):
            self.model_url = f"{self.model_url.rstrip('/')}/chat/completions"
        
        self.model_key = config.VLM_API_KEY
        self.model_name = config.VLM_MODEL_NAME

    def _encode_image(self, img_bytes):
        return base64.b64encode(img_bytes).decode('utf-8')

    def parse_document(self, document_id: str = '') -> ParsedContent:
        content = ParsedContent()
        content.page_count = len(self.doc)
        
        assets_images_dir = config.ASSETS_DIR / document_id / 'images'
        assets_images_dir.mkdir(parents=True, exist_ok=True)

        full_markdown_parts = []
        all_extracted_images = []

        print(f"\n--- Starting VLM Conversion: {self.pdf_path.name} ---")

        for i in tqdm(range(content.page_count), desc="Processing Pages"):
            page = self.doc.load_page(i)
            
            text_blocks = page.get_text("dict")["blocks"]
            page_map = []
            for b in text_blocks:
                if b["type"] == 0:
                    text_content = ""
                    for line in b["lines"]:
                        for span in line["spans"]:
                            text_content += span["text"]
                        text_content += "\n"
                    if text_content.strip():
                        page_map.append({
                            "type": "text",
                            "content": text_content.strip(),
                            "bbox": b["bbox"]
                        })

            image_info_list = page.get_images(full=True)
            for img_idx, img in enumerate(image_info_list):
                xref = img[0]
                rects = page.get_image_rects(xref)
                if not rects: continue
                
                base_image = self.doc.extract_image(xref)
                img_ext = base_image["ext"]
                img_filename = f"page_{i+1}_img_{img_idx+1}.{img_ext}"
                img_path = assets_images_dir / img_filename
                
                if rects[0].width < 20 or rects[0].height < 20:
                    continue

                with open(img_path, "wb") as f_img:
                    f_img.write(base_image["image"])
                
                rel_img_path = f"assets/{document_id}/images/{img_filename}"
                
                page_map.append({
                    "type": "image",
                    "content": rel_img_path,
                    "bbox": rects[0]
                })
                
                all_extracted_images.append({
                    'image_id': f"img_{len(all_extracted_images) + 1:03d}",
                    'file_path': rel_img_path,
                    'caption': '', 
                    'reference_context': '',
                    'metadata': {
                        'width': int(rects[0].width),
                        'height': int(rects[0].height),
                        'format': img_ext,
                        'file_size_kb': len(base_image["image"]) / 1024
                    }
                })

            page_map.sort(key=lambda x: x["bbox"][1])

            layout_map_str = ""
            for idx, item in enumerate(page_map):
                if item["type"] == "text":
                    layout_map_str += f"\n[BLOCK {idx} - TEXT]\n{item['content']}\n"
                else:
                    layout_map_str += f"\n[BLOCK {idx} - IMAGE: {item['content']}]\n"

            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            b64_img = self._encode_image(pix.tobytes("png"))

            page_markdown = self._call_vlm(layout_map_str, b64_img)
            full_markdown_parts.append(f"<!-- PAGE {i+1} -->\n\n{page_markdown}")

        content.full_text = "\n\n---\n\n".join(full_markdown_parts)
        content.images = all_extracted_images
        content.tables = [] 
        
        self.doc.close()
        return content

    def _call_vlm(self, layout_map, b64_image) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.model_key}"
        }

        prompt = (
            "You are a professional document converter. I have provided a 'Layout Map' of a PDF page with sorted blocks.\n\n"
            "STRICT FORMATTING RULES:\n"
            "1. Output ONLY Markdown content. No conversational filler.\n"
            "2. For [BLOCK X - TEXT]: \n"
            "   - Convert to high-quality Markdown.\n"
            "   - Use LaTeX ($$ ... $$) for ALL mathematical formulas and variables.\n"
            "   - Use proper Markdown headers (#, ##, ###) for titles.\n"
            "   - Reconstruct tables using Markdown table syntax.\n"
            "3. For [BLOCK X - IMAGE: assets/...]: \n"
            "   - STEP 1: Look at the surrounding [TEXT] blocks in the Layout Map to see how the document refers to this image (look for 'Figure X', 'Table Y', or descriptive sentences nearby).\n"
            "   - STEP 2: Analyze the visual content of the image and read any text inside it.\n"
            "   - STEP 3: Generate a HIGHLY CONTEXTUAL caption that aligns with the document's text and the visual evidence.\n"
            "   - Insert it as: ![Contextual Caption](assets/...)\n"
            "   - Also add a visible caption below it: *Figure: Contextual Caption*\n"
            "   - IMPORTANT: USE THE EXACT FILENAME AND EXTENSION PROVIDED. NEVER CHANGE IT.\n"
            "4. Follow the EXACT sequence of blocks from the Layout Map.\n\n"
            f"LAYOUT MAP:\n{layout_map}"
        )

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
                    ]
                }
            ],
            "temperature": 0.1
        }

        try:
            response = requests.post(self.model_url, headers=headers, json=payload, timeout=180)
            response.raise_for_status()
            resp_data = response.json()
            content = resp_data['choices'][0]['message']['content']
            
            if content.startswith("```markdown"): content = content[11:]
            if content.startswith("```"): content = content[3:]
            if content.endswith("```"): content = content[:-3]
            
            return content.strip()
        except Exception as e:
            _log.error(f"Error calling VLM: {e}")
            return f"Error processing page. Details: {str(e)}"