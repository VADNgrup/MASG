import html
import re
from typing import List, Optional

class SlideLayoutManager:

    def __init__(self, theme: str='frankfurt', title: str='Main Ttile', author: str='Slidev With Multi-agent System', font_sans: str='Roboto', font_serif: str='Roboto', font_mono: str='Roboto', heading_color_code: str='#e2b96f'):
        self.theme = theme
        self.title = title
        self.author = author
        self.font_sans = font_sans
        self.font_serif = font_serif
        self.font_mono = font_mono
        self.heading_color_code = heading_color_code

    def _h1(self, text: str) -> str:
        safe = html.escape(str(text or ""))
        return (
            '<div class="generated-slide-title" data-slide-title="true" '
            'style="box-sizing: border-box; width: 100%; max-width: 100%; '
            'margin: 1.6rem 0 0.65rem 0; padding: 0; '
            f'color: {self.heading_color_code}; '
            'font-size: clamp(1.02rem, 2.15vw, 1.58rem); line-height: 1.12; '
            'font-weight: 700; white-space: normal; overflow-wrap: anywhere; '
            'word-break: normal; text-wrap: balance;">'
            f'{safe}</div>'
        )

    def _slide_sep(self) -> str:
        return '---'

    def _html_list(self, content: List[str], font_size: Optional[str]=None) -> str:
        content = self._clean_content_items(content)
        if not font_size:
            estimated = sum(len(item) for item in content)
            if len(content) >= 6 or estimated > 520:
                font_size = '0.94rem'
            elif len(content) >= 5 or estimated > 400:
                font_size = '1.02rem'
            elif estimated > 280:
                font_size = '1.12rem'
            else:
                font_size = '1.22rem'
                
        li_items = '\n'.join(
            (
                '        <li style="margin: 0 0 0.65rem 0; line-height: 1.35; overflow-wrap: anywhere; hyphens: auto;">'
                f'{html.escape(item)}</li>'
            )
            for item in content
        )
        return (
            f'<ul style="margin: 0.5rem 0 0 0; padding-left: 1.3rem; font-size: {font_size}; '
            'line-height: 1.35; max-width: 100%;">\n'
            f'{li_items}\n'
            '</ul>'
        )

    @staticmethod
    def _clean_content_items(content: List[str]) -> List[str]:
        if not isinstance(content, list):
            return []
        cleaned = []
        for item in content:
            text = re.sub(r"\s+", " ", str(item or "")).strip()
            if not text:
                continue
            cleaned.append(text)
        return cleaned

    def config_and_greeting_slide(self, short_title: Optional[str]=None) -> str:
        safe_title = (self.title or '').replace('"', '\\"')
        author_text = (self.author or "").strip()
        safe_short = (short_title or '').replace('"', '\\"')
        full_title = self.title or ""
        display_title = full_title
        subtitle = ""
        
        if ":" in full_title:
            parts = full_title.split(":", 1)
            display_title = parts[0].strip()
            subtitle = parts[1].strip()
            
        display_title = html.escape(display_title)
        subtitle_html = ""
        if subtitle:
            subtitle_html = (
                '<div style="max-width: 62rem; margin-top: 1.1rem; color: rgba(241, 245, 249, 0.85); '
                'font-size: clamp(1.1rem, 1.6vw, 1.45rem); line-height: 1.35; font-weight: 500; text-wrap: balance;">'
                f'{html.escape(subtitle)}</div>'
            )
            
        style = """
<style>
.slidev-layout h1 {
  max-width: 100%;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: normal;
  line-height: 1.12;
}
.slidev-layout .generated-slide-title {
  display: block !important;
  max-width: 100% !important;
  white-space: normal !important;
  overflow-wrap: anywhere !important;
  word-break: normal !important;
  margin-top: 1.6rem !important;
}
.slidev-layout li {
  overflow-wrap: anywhere;
}
footer, 
footer *, 
.info-line, 
.info-line *, 
.slidev-layout footer, 
.slidev-layout footer * {
  color: #ffffff !important;
  opacity: 1 !important;
}
</style>
""".strip()
        
        import datetime
        current_date = datetime.date.today().strftime("%B %d, %Y")
        current_date_inflow = datetime.date.today().strftime("%Y/%m/%d")
        speaker_val = author_text or 'Slidev with Slide Generation System'
        
        speaker_name = speaker_val
        institution = ""
        for sep in [' - ', ' | ', ' @ ', ', ']:
            if sep in speaker_val:
                parts = speaker_val.split(sep, 1)
                speaker_name = parts[0].strip()
                institution = parts[1].strip()
                break
                
        inst_html = ""
        if institution:
            inst_html = f'  <div style="color: rgba(248, 250, 252, 0.8); font-size: 0.88rem; margin-top: 0.15rem;">{html.escape(institution)}</div>'
            
        meta_html = (
            '<div style="margin-top: 2.2rem; border-left: 3px solid #e2b96f; padding-left: 1.2rem; line-height: 1.5; text-align: left;">'
            f'  <div style="color: rgba(226, 185, 111, 0.95); font-size: 1.15rem; font-weight: 600; letter-spacing: 0.02em;">{html.escape(speaker_name)}</div>'
            f'{inst_html}'
            f'  <div style="color: rgba(248, 250, 252, 0.55); font-size: 0.78rem; margin-top: 0.35rem;">Date: {current_date}</div>'
            '</div>'
        )
        
        cover = (
            '<div style="position: absolute; inset: 0; padding: 3.2rem 3.4rem; '
            'display: flex; align-items: center; background: linear-gradient(135deg, #0f172a 0%, #172554 46%, #1d4ed8 100%); overflow: hidden;">'
            '<div style="max-width: 70rem;">'
            '<div style="width: 5rem; height: 0.34rem; border-radius: 999px; background: #e2b96f; margin-bottom: 1.35rem;"></div>'
            '<div style="max-width: 64rem; color: #f8fafc; font-size: clamp(2.2rem, 4.5vw, 4.2rem); '
            'line-height: 1.08; font-weight: 750; text-wrap: balance;">'
            f'{display_title}'
            '</div>'
            f'{subtitle_html}'
            f'{meta_html}'
            '</div>'
            '</div>'
        )
        lines = [
            '---', 
            f'theme: {self.theme}', 
            f'title: "{safe_short}"', 
            f'author: "{speaker_val}"', 
            f'date: "{current_date_inflow}"',
            'infoLine: true',
            'katex: true', 
            'fonts:', 
            f'  sans: {self.font_sans}', 
            f'  serif: {self.font_serif}', 
            f'  mono: {self.font_mono}', 
            '---', 
            '', 
            style, 
            '', 
            cover, 
            '---'
        ]
        return '\n'.join(lines)

    def toc_layout(self, toc_content: List[str], heading: str='') -> str:
        def _strip_number_prefix(item: str) -> str:
            return __import__('re').sub(r'^\s*\d+(?:\.\d+)*\.\s*', '', str(item or '')).strip()

        # If there are many items, we use a 2-column grid to look neat and clean on a single slide!
        use_two_cols = len(toc_content) > 6 or sum(len(item) for item in toc_content) > 300
        
        if use_two_cols:
            list_style = "display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem 2.5rem; font-size: 1.05rem; line-height: 1.3; padding-left: 1.4rem; margin: 0.5rem 0 0 0;"
            items_html = '\n'.join(
                f'<li style="margin: 0; line-height: 1.3;">{_strip_number_prefix(item)}</li>'
                for item in toc_content
            )
        else:
            list_style = "font-size: 1.25rem; line-height: 1.35; padding-left: 1.4rem; margin: 0.6rem 0 0 0;"
            items_html = '\n'.join(
                f'<li style="margin: 0 0 0.85rem 0; line-height: 1.35;">{_strip_number_prefix(item)}</li>'
                for item in toc_content
            )

        title_html = self._h1(heading) if heading else ''
        parts = [
            '\n\n',
            '<div style="height: 100%; display: flex; align-items: flex-start; justify-content: center;">\n',
            '  <div style="width: min(88%, 1100px); margin-top: 1.4rem;">\n',
        ]
        if title_html:
            parts.append(f'    {title_html}\n')
        parts.extend([
            f'    <ol style="{list_style}">\n',
            f'      {items_html}\n',
            '    </ol>\n',
            '  </div>\n',
            '</div>\n',
            self._slide_sep(),
        ])
        return ''.join(parts)

    def image_right_layout(self, title: str, content: List[str], img_path: str, image_width: str='40%', caption: Optional[str]=None) -> str:
        list_html = self._html_list(content, font_size='0.96rem')
        caption_html = f'\n      <p style="text-align:center; line-height: 1.2; margin: 0.1rem 0 0 0; font-size: 2.5cqw;"><b>{caption}</b></p>' if caption else ''
        return f'\n\n<div style="\n    --image-width: {image_width};\n    display: flex; flex-direction: column; height: 100%;">\n\n  <!-- Title -->\n  <div>\n    {self._h1(title)}\n  </div>\n\n  <!-- Two columns -->\n  <div style="display: grid;\n              grid-template-columns: 1fr var(--image-width);\n              align-items: start;\n              gap: 2.5rem;\n              flex: 1; min-height: 0;">\n    <!-- Left: text -->\n    <div style="overflow: auto;">\n      {list_html}\n    </div>\n    <!-- Right: image -->\n    <div style="container-type: inline-size;">\n      <img src="{img_path}" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />{caption_html}\n    </div>\n\n  </div>\n</div>\n' + self._slide_sep()

    def image_left_layout(self, title: str, content: List[str], img_path: str, image_width: str='40%', caption: Optional[str]=None) -> str:
        list_html = self._html_list(content, font_size='0.96rem')
        caption_html = f'\n      <p style="text-align:center; line-height: 1.2; margin: 0.1rem 0 0 0; font-size: 2.5cqw;"><b>{caption}</b></p>' if caption else ''
        return f'\n\n<div style="\n    --image-width: {image_width};\n    display: flex; flex-direction: column; height: 100%;">\n\n  <!-- Title -->\n  <div>\n    {self._h1(title)}\n  </div>\n\n  <!-- Two columns -->\n  <div style="display: grid;\n              grid-template-columns: var(--image-width) 1fr;\n              align-items: start;\n              gap: 2.5rem;\n              flex: 1; min-height: 0;">\n    <!-- Left: image -->\n    <div style="container-type: inline-size;">\n      <img src="{img_path}" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />{caption_html}\n    </div>\n    <!-- Right: text -->\n    <div style="overflow: auto;">\n      {list_html}\n    </div>\n  </div>\n</div>\n' + self._slide_sep()

    def image_above_layout(self, title: str, content: List[str], img_path: str, image_width: str='60%', caption: Optional[str]=None) -> str:
        list_html = self._html_list(content, font_size='0.96rem')
        caption_html = f'\n  <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0"><b>{caption}</b></p>' if caption else ''
        max_h = '55vh' if not content else '38vh'
        return '\n\n' + self._h1(title) + '\n\n' + f'<div style="width: {image_width}; margin: auto; container-type: inline-size; display: flex; flex-direction: column; align-items: center;">\n' + f'  <img src="{img_path}" style="width: 100%; max-width: 100%; max-height: {max_h}; display: block; object-fit: contain;" />{caption_html}\n' + '</div>\n\n' + list_html + '\n' + self._slide_sep()

    def image_below_layout(self, title: str, content: List[str], img_path: str, image_width: str='60%', caption: Optional[str]=None) -> str:
        list_html = self._html_list(content, font_size='0.96rem')
        caption_html = f'\n  <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0"><b>{caption}</b></p>' if caption else ''
        max_h = '55vh' if not content else '38vh'
        return '\n\n' + self._h1(title) + '\n\n' + list_html + '\n\n' + f'<div style="width: {image_width}; margin: auto; container-type: inline-size; display: flex; flex-direction: column; align-items: center;">\n' + f'  <img src="{img_path}" style="width: 100%; max-width: 100%; max-height: {max_h}; display: block; object-fit: contain;" />{caption_html}\n' + '</div>\n' + self._slide_sep()

    def only_content(self, title: str, content: List[str]) -> str:
        return '\n\n' + self._h1(title) + '\n\n' + self._html_list(content, font_size='0.98rem') + '\n' + self._slide_sep()

    def comparison_layout(self, title: str, table_markdown: str) -> str:
        style_block = """
<style scoped>
table {
  font-size: 0.75rem;
  display: block;
  max-height: 60vh;
  overflow-y: auto;
  width: 100%;
}
</style>
"""
        return '\n\n' + self._h1(title) + '\n\n' + table_markdown + '\n' + style_block + '\n' + self._slide_sep()

    def two_contents_in_a_slide_layout(self, title: str, sub_title_1: str, sub_title_2: str, sub_content_1: List[str], sub_content_2: List[str]) -> str:
        li_left = '\n'.join((f'        <li>{html.escape(str(item))}</li>' for item in self._clean_content_items(sub_content_1)))
        li_right = '\n'.join((f'        <li>{html.escape(str(item))}</li>' for item in self._clean_content_items(sub_content_2)))
        return f'\n\n<div style="\n    --left-width: 45%;\n    --right-width: 45%;\n    display: flex; flex-direction: column; height: 100%;">\n\n  <!-- Title -->\n  <div>\n    {self._h1(title)}\n  </div>\n\n  <div style="display: grid;\n              grid-template-columns: var(--left-width) var(--right-width);\n              align-items: start;\n              gap: 2.5rem;\n              flex: 1; min-height: 0;">\n    <!-- Left -->\n    <div style="overflow: auto;">\n      <h2>{sub_title_1}</h2>\n      <ul>\n{li_left}\n      </ul>\n    </div>\n    <!-- Right -->\n    <div style="overflow: auto;">\n      <h2>{sub_title_2}</h2>\n      <ul>\n{li_right}\n      </ul>\n    </div>\n  </div>\n</div>\n' + self._slide_sep()

    def formula_below_layout(self, title: str, latex_formula_block: str, content: List[str]) -> str:
        return '\n\n' + self._h1(title) + '\n\n' + self._html_list(content, font_size='0.96rem') + '\n\n' + '<div class="formula-container" style="font-size: 1.2rem; margin-top: 1rem;">\n\n' + '$$\n' + latex_formula_block + '\n$$\n\n' + '</div>\n' + self._slide_sep()

    def formula_top_layout(self, title: str, latex_formula_block: str, content: List[str]) -> str:
        return '\n\n' + self._h1(title) + '\n\n' + '<div class="formula-container" style="font-size: 1.2rem; margin-bottom: 1rem;">\n\n' + '$$\n' + latex_formula_block + '\n$$\n\n' + '</div>\n\n' + self._html_list(content, font_size='0.96rem') + '\n' + self._slide_sep()

    def two_image_right_layout(self, title: str, content: List[str], img1_path: str, img2_path: str, image_width: str='22.5%', caption1: Optional[str]=None, caption2: Optional[str]=None) -> str:
        li_items = '\n'.join((f'        <li>{html.escape(str(item))}</li>' for item in self._clean_content_items(content)))
        caption1_html = f'\n        <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>{caption1}</b></p>' if caption1 else ''
        caption2_html = f'\n        <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>{caption2}</b></p>' if caption2 else ''
        return f'\n\n<div style="\n    --image-width: {image_width};\n    display: flex; flex-direction: column; height: 100%;">\n\n  <!-- Title -->\n  <div>\n    {self._h1(title)}\n  </div>\n\n  <div style="display: grid;\n              grid-template-columns: 1fr var(--image-width);\n              align-items: start;\n              gap: 1rem;\n              flex: 1; min-height: 0;">\n    <!-- Left: text -->\n    <div style="overflow: auto;">\n      <ul>\n{li_items}\n      </ul>\n    </div>\n    <!-- Right: images -->\n    <div style="container-type: inline-size;">\n      <div>\n        <img src="{img1_path}" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />{caption1_html}\n      </div>\n      <div>\n        <img src="{img2_path}" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />{caption2_html}\n      </div>\n    </div>\n\n  </div>\n</div>\n' + self._slide_sep()

    def two_image_left_layout(self, title: str, content: List[str], img1_path: str, img2_path: str, image_width: str='22.5%', caption1: Optional[str]=None, caption2: Optional[str]=None) -> str:
        li_items = '\n'.join((f'        <li>{html.escape(str(item))}</li>' for item in self._clean_content_items(content)))
        caption1_html = f'\n        <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0; "><b>{caption1}</b></p>' if caption1 else ''
        caption2_html = f'\n        <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0; "><b>{caption2}</b></p>' if caption2 else ''
        return f'\n\n<div style="\n    --image-width: {image_width};\n    display: flex; flex-direction: column; height: 100%;">\n\n  <!-- Title -->\n  <div>\n    {self._h1(title)}\n  </div>\n\n  <div style="display: grid;\n              grid-template-columns: var(--image-width) 1fr;\n              align-items: start;\n              gap: 1rem;\n              flex: 1; min-height: 0;">\n    <!-- Left: images -->\n    <div style="container-type: inline-size;">\n      <div>\n        <img src="{img1_path}" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />{caption1_html}\n      </div>\n      <div>\n        <img src="{img2_path}" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />{caption2_html}\n      </div>\n    </div>\n    <!-- Right: text -->\n    <div style="overflow: auto; font-size: 1rem">\n      <ul>\n{li_items}\n      </ul>\n    </div>\n  </div>\n</div>\n' + self._slide_sep()

    def two_image_above_layout(self, title: str, content: List[str], img1_path: str, img2_path: str, image_width: str='60%', caption1: Optional[str]=None, caption2: Optional[str]=None) -> str:
        bullet_lines = '\n'.join((f'- {item}' for item in content))
        caption1_html = f'\n    <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>{caption1}</b></p>' if caption1 else ''
        caption2_html = f'\n    <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>{caption2}</b></p>' if caption2 else ''
        return '\n\n' + self._h1(title) + '\n\n' + f'<div style="width: {image_width}; margin: auto; display: flex; gap: 1rem; align-items: start;">\n' + '  <div style="flex: 1; container-type: inline-size; display: flex; flex-direction: column; align-items: center;">\n' + f'    <img src="{img1_path}" style="width: auto; max-width: 100%; max-height: 30vh; display: block; object-fit: contain;" />{caption1_html}\n' + '  </div>\n' + '  <div style="flex: 1; container-type: inline-size; display: flex; flex-direction: column; align-items: center;">\n' + f'    <img src="{img2_path}" style="width: auto; max-width: 100%; max-height: 30vh; display: block; object-fit: contain;" />{caption2_html}\n' + '  </div>\n' + '</div>\n' + '\n' + bullet_lines + '\n' + self._slide_sep()

    def two_image_below_layout(self, title: str, content: List[str], img1_path: str, img2_path: str, image_width: str='60%', caption1: Optional[str]=None, caption2: Optional[str]=None) -> str:
        bullet_lines = '\n'.join((f'- {item}' for item in content))
        caption1_html = f'\n    <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>{caption1}</b></p>' if caption1 else ''
        caption2_html = f'\n    <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>{caption2}</b></p>' if caption2 else ''
        return '\n\n' + self._h1(title) + '\n\n' + bullet_lines + '\n\n' + f'<div style="width: {image_width}; margin: auto; display: flex; gap: 1rem; align-items: start;">\n' + '  <div style="flex: 1; container-type: inline-size; display: flex; flex-direction: column; align-items: center;">\n' + f'    <img src="{img1_path}" style="width: auto; max-width: 100%; max-height: 30vh; display: block; object-fit: contain;" />{caption1_html}\n' + '  </div>\n' + '  <div style="flex: 1; container-type: inline-size; display: flex; flex-direction: column; align-items: center;">\n' + f'    <img src="{img2_path}" style="width: auto; max-width: 100%; max-height: 30vh; display: block; object-fit: contain;" />{caption2_html}\n' + '  </div>\n' + '</div>\n' + self._slide_sep()

    def two_cols_content_layout(self, title: str, content: List[str]) -> str:
        content = self._clean_content_items(content)
        mid = (len(content) + 1) // 2
        left_items = content[:mid]
        right_items = content[mid:]
        left_html = self._html_list(left_items)
        right_html = self._html_list(right_items)
        return f'\n\n<div style="\n    --left-width: 47%;\n    --right-width: 47%;\n    display: flex; flex-direction: column; height: 100%;">\n\n  <!-- Title -->\n  <div>\n    {self._h1(title)}\n  </div>\n\n  <div style="display: grid;\n              grid-template-columns: var(--left-width) var(--right-width);\n              align-items: start;\n              gap: 1.4rem;\n              flex: 1; min-height: 0;">\n    <!-- Left -->\n    <div style="overflow: auto;">\n      {left_html}\n    </div>\n    <!-- Right -->\n    <div style="overflow: auto;">\n      {right_html}\n    </div>\n  </div>\n</div>\n' + self._slide_sep()
    def end_layout(self, end_text: str='') -> str:
        safe_end = html.escape(end_text or "Thank You")
        speaker_val = self.author or 'Slidev with Slide Generation System'
        
        # Dynamically split speaker name and institution if present
        speaker_name = speaker_val
        institution = ""
        for sep in [' - ', ' | ', ' @ ', ', ']:
            if sep in speaker_val:
                parts = speaker_val.split(sep, 1)
                speaker_name = parts[0].strip()
                institution = parts[1].strip()
                break
                
        inst_html = ""
        if institution:
            inst_html = f'<div style="color: rgba(248, 250, 252, 0.7); font-size: 0.88rem; margin-top: 0.25rem;">{html.escape(institution)}</div>'
            
        end_block = (
            '<div style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; '
            'background: radial-gradient(circle at top, #1e3a8a 0%, #0f172a 72%); overflow: hidden;">'
            '<div style="text-align: center;">'
            '<div style="width: 4.5rem; height: 0.32rem; border-radius: 999px; background: #e2b96f; margin: 0 auto 1.2rem auto;"></div>'
            '<div style="color: #f8fafc; font-size: clamp(2.4rem, 5vw, 4rem); font-weight: 720; letter-spacing: 0.01em; margin-bottom: 1rem;">'
            f'{safe_end}'
            '</div>'
            f'<div style="color: rgba(226, 185, 111, 0.9); font-size: 1.05rem; font-weight: 500;">Presented by: {html.escape(speaker_name)}</div>'
            f'{inst_html}'
            '<div style="color: rgba(248, 250, 252, 0.6); font-size: 0.85rem; margin-top: 0.5rem;">Q&A Session & Discussion</div>'
            '</div>'
            '</div>'
        )
        lines = ['---', '', '<!-- END_SLIDE -->', '', end_block]
        return '\n'.join(lines)
