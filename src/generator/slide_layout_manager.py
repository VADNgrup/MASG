from typing import List, Optional


class SlideLayoutManager:
    
    def __init__(
        self,
        theme: str = "frankfurt",
        title: str = "Main Ttile",
        author: str = "Slidev With Multi-agent System",
        font_sans: str = "Roboto",
        font_serif: str = "Roboto",
        font_mono: str = "Roboto",
        heading_color_code: str = "#e2b96f",
    ):
        self.theme = theme
        self.title = title
        self.author = author
        self.font_sans = font_sans
        self.font_serif = font_serif
        self.font_mono = font_mono
        self.heading_color_code = heading_color_code

    def _h1(self, text: str) -> str:
        return f'<h1 style="color: {self.heading_color_code};">{text}</h1>'

    def _slide_sep(self) -> str:
        return "---"

    def config_and_greeting_slide(self) -> str:
        """
        Lines 1-13 of test_1.md: frontmatter + greeting title.
        """
        lines = [
            "---",
            f"theme: {self.theme}",
            f"title: {self.title}",
            f"author: {self.author}",
            "katex: true",
            "fonts:",
            f"  sans: {self.font_sans}",
            f"  serif: {self.font_serif}",
            f"  mono: {self.font_mono}",
            "---",
            "",
            f"# {self.title}",
            "---",
        ]
        return "\n".join(lines)

    def toc_layout(self, toc_content: List[str]) -> str:
        """
        Lines 14-31 of test_1.md: Table of Content slide.
        toc_content: list of strings, one per bullet line.
        Each line except the last is suffixed with ' \\'.
        """
        header = (
            "\n\n"
            + self._h1("Table Of Content")
            + "\n"
            + "<p></p>"
            + "\n\n"
        )

        import re as _re

        def _is_major(s: str) -> bool:
            """True nếu item là đầu section lớn, vd '2. ...' hoặc '3. ...'"""
            return bool(_re.match(r"^\d+\.\s+\S", s)) and s.split(".")[0].strip().isdigit()

        body_lines = []
        for i, item in enumerate(toc_content):
            is_last = i == len(toc_content) - 1
            next_is_major = (not is_last) and _is_major(toc_content[i + 1])
            if is_last or next_is_major:
                body_lines.append(f" {item}")
            else:
                body_lines.append(f" {item} \\")

        content = "\n".join(body_lines)
        return header + '<div style="font-size: 1.5rem;">\n\n' + content + "\n\n</div>\n" + self._slide_sep()

    def image_right_layout(
        self,
        title: str,
        content: List[str],
        img_path: str,
        image_width: str = "40%",
        caption: Optional[str] = None,
    ) -> str:
        """
        Title + text left, image right.
        """
        li_items = "\n".join(f"        <li>{item}</li>" for item in content)
        caption_html = (
            f'\n      <p style="text-align:center; line-height: 1.2; margin: 0.1rem 0 0 0; font-size: 2.5cqw;"><b>{caption}</b></p>'
            if caption else ""
        )

        return (
            "\n\n"
            f'<div style="\n'
            f'    --image-width: {image_width};\n'
            f'    display: flex; flex-direction: column; height: 100%;">\n'
            "\n"
            "  <!-- Title -->\n"
            "  <div>\n"
            f"    {self._h1(title)}\n"
            "  </div>\n"
            "\n"
            "  <!-- Two columns -->\n"
            '  <div style="display: grid;\n'
            "              grid-template-columns: 1fr var(--image-width);\n"
            "              align-items: start;\n"
            "              gap: 2.5rem;\n"
            '              flex: 1; min-height: 0;">\n'
            "    <!-- Left: text -->\n"
            '    <div style="overflow: auto;">\n'
            "      <ul>\n"
            f"{li_items}\n"
            "      </ul>\n"
            "    </div>\n"
            "    <!-- Right: image -->\n"
            '    <div style="container-type: inline-size;">\n'
            f'      <img src="{img_path}" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />{caption_html}\n'
            "    </div>\n"
            "\n"
            "  </div>\n"
            "</div>\n"
            + self._slide_sep()
        )

    def image_left_layout(
        self,
        title: str,
        content: List[str],
        img_path: str,
        image_width: str = "40%",
        caption: Optional[str] = None,
    ) -> str:
        """
        Title + image left, text right.
        """
        li_items = "\n".join(f"        <li>{item}</li>" for item in content)
        caption_html = (
            f'\n      <p style="text-align:center; line-height: 1.2; margin: 0.1rem 0 0 0; font-size: 2.5cqw;"><b>{caption}</b></p>'
            if caption else ""
        )

        return (
            "\n\n"
            f'<div style="\n'
            f'    --image-width: {image_width};\n'
            f'    display: flex; flex-direction: column; height: 100%;">\n'
            "\n"
            "  <!-- Title -->\n"
            "  <div>\n"
            f"    {self._h1(title)}\n"
            "  </div>\n"
            "\n"
            "  <!-- Two columns -->\n"
            '  <div style="display: grid;\n'
            "              grid-template-columns: var(--image-width) 1fr;\n"
            "              align-items: start;\n"
            "              gap: 2.5rem;\n"
            '              flex: 1; min-height: 0;">\n'
            "    <!-- Left: image -->\n"
            '    <div style="container-type: inline-size;">\n'
            f'      <img src="{img_path}" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />{caption_html}\n'
            "    </div>\n"
            "    <!-- Right: text -->\n"
            '    <div style="overflow: auto;">\n'
            "      <ul>\n"
            f"{li_items}\n"
            "      </ul>\n"
            "    </div>\n"
            "  </div>\n"
            "</div>\n"
            + self._slide_sep()
        )

    def image_above_layout(
        self,
        title: str,
        content: List[str],
        img_path: str,
        image_width: str = "60%",
        caption: Optional[str] = None,
    ) -> str:
        """
        Title + centered image above, bullet content below.
        """
        bullet_lines = "\n".join(f"- {item}" for item in content)
        caption_html = (
            f'\n  <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0"><b>{caption}</b></p>'
            if caption else ""
        )

        return (
            "\n\n"
            + self._h1(title)
            + "\n\n"
            + f'<div style="width: {image_width}; margin: auto; container-type: inline-size;">\n'
            + f'  <img src="{img_path}" style="width: 100%; max-height: 100%; max-width: 100%; display: block; object-fit: contain;" />{caption_html}\n'
            + "</div>\n"
            + "\n"
            + bullet_lines
            + "\n"
            + self._slide_sep()
        )

    def image_below_layout(
        self,
        title: str,
        content: List[str],
        img_path: str,
        image_width: str = "60%",
        caption: Optional[str] = None,
    ) -> str:
        """
        Title + bullet content above, centered image below.
        """
        bullet_lines = "\n".join(f"- {item}" for item in content)
        caption_html = (
            f'\n  <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0"><b>{caption}</b></p>'
            if caption else ""
        )

        return (
            "\n\n"
            + self._h1(title)
            + "\n\n"
            + bullet_lines
            + "\n\n"
            + f'<div style="width: {image_width}; margin: auto; container-type: inline-size;">\n'
            + f'  <img src="{img_path}" style="width: 100%; max-height: 100%; max-width: 100%; display: block; object-fit: contain;" />{caption_html}\n'
            + "</div>\n"
            + self._slide_sep()
        )


    def only_content(self, title: str, content: List[str]) -> str:
        """
        Lines 67-74 of test_1.md: title + bullet list only, no image or table.
        """
        bullet_lines = "\n".join(f"- {item}" for item in content)

        return (
            "\n\n"
            + self._h1(title)
            + "\n\n"
            + bullet_lines
            + "\n"
            + self._slide_sep()
        )

    def comparison_layout(
        self,
        title: str,
        table_markdown: str,
    ) -> str:
        """
        Title + comparison table (no caption, no bullet content).
        """
        return (
            "\n\n"
            + self._h1(title)
            + "\n\n"
            + table_markdown
            + "\n"
            + self._slide_sep()
        )

    def two_contents_in_a_slide_layout(
        self,
        title: str,
        sub_title_1: str,
        sub_title_2: str,
        sub_content_1: List[str],
        sub_content_2: List[str],
    ) -> str:
        """
        Title + two columns, each with its own sub-heading and bullet list.
        """
        li_left = "\n".join(f"        <li>{item}</li>" for item in sub_content_1)
        li_right = "\n".join(f"        <li>{item}</li>" for item in sub_content_2)

        return (
            "\n\n"
            f'<div style="\n'
            f'    --left-width: 45%;\n'
            f'    --right-width: 45%;\n'
            f'    display: flex; flex-direction: column; height: 100%;">\n'
            "\n"
            "  <!-- Title -->\n"
            "  <div>\n"
            f"    {self._h1(title)}\n"
            "  </div>\n"
            "\n"
            '  <div style="display: grid;\n'
            "              grid-template-columns: var(--left-width) var(--right-width);\n"
            "              align-items: start;\n"
            "              gap: 2.5rem;\n"
            '              flex: 1; min-height: 0;">\n'
            "    <!-- Left -->\n"
            '    <div style="overflow: auto;">\n'
            f"      <h2>{sub_title_1}</h2>\n"
            "      <ul>\n"
            f"{li_left}\n"
            "      </ul>\n"
            "    </div>\n"
            "    <!-- Right -->\n"
            '    <div style="overflow: auto;">\n'
            f"      <h2>{sub_title_2}</h2>\n"
            "      <ul>\n"
            f"{li_right}\n"
            "      </ul>\n"
            "    </div>\n"
            "  </div>\n"
            "</div>\n"
            + self._slide_sep()
        )

    def formula_below_layout(
        self,
        title: str,
        latex_formula_block: str,
        content: List[str],
    ) -> str:
        """
        Title + bullet content above, LaTeX formula block below.
        """
        bullet_lines = "\n".join(f"- {item}" for item in content)

        return (
            "\n\n"
            + self._h1(title)
            + "\n\n"
            + bullet_lines
            + "\n"
            + "<!-- Latex Formula Block -->\n"
            + "$$\n"
            + latex_formula_block
            + "\n$$\n"
            + self._slide_sep()
        )

    def formula_top_layout(
        self,
        title: str,
        latex_formula_block: str,
        content: List[str],
    ) -> str:
        """
        Title + LaTeX formula block above, bullet content below.
        """
        bullet_lines = "\n".join(f"- {item}" for item in content)

        return (
            "\n\n"
            + self._h1(title)
            + "\n\n"
            + "<!-- Latex Formula Block -->\n"
            + "$$\n"
            + latex_formula_block
            + "\n$$\n"
            + "\n"
            + bullet_lines
            + "\n"
            + self._slide_sep()
        )
    def two_image_right_layout(
        self,
        title: str,
        content: List[str],
        img1_path: str,
        img2_path: str,
        image_width: str = "22.5%",
        caption1: Optional[str] = None,
        caption2: Optional[str] = None,
    ) -> str:
        """
        Title + text left, two stacked images right.
        """
        li_items = "\n".join(f"        <li>{item}</li>" for item in content)
        caption1_html = (
            f'\n        <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>{caption1}</b></p>'
            if caption1 else ""
        )
        caption2_html = (
            f'\n        <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>{caption2}</b></p>'
            if caption2 else ""
        )

        return (
            "\n\n"
            f'<div style="\n'
            f'    --image-width: {image_width};\n'
            f'    display: flex; flex-direction: column; height: 100%;">'  "\n"
            "\n"
            "  <!-- Title -->\n"
            "  <div>\n"
            f"    {self._h1(title)}\n"
            "  </div>\n"
            "\n"
            '  <div style="display: grid;\n'
            "              grid-template-columns: 1fr var(--image-width);\n"
            "              align-items: start;\n"
            "              gap: 1rem;\n"
            '              flex: 1; min-height: 0;">\n'
            "    <!-- Left: text -->\n"
            '    <div style="overflow: auto;">\n'
            "      <ul>\n"
            f"{li_items}\n"
            "      </ul>\n"
            "    </div>\n"
            "    <!-- Right: images -->\n"
            '    <div style="container-type: inline-size;">\n'
            "      <div>\n"
            f'        <img src="{img1_path}" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />{caption1_html}\n'
            "      </div>\n"
            "      <div>\n"
            f'        <img src="{img2_path}" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />{caption2_html}\n'
            "      </div>\n"
            "    </div>\n"
            "\n"
            "  </div>\n"
            "</div>\n"
            + self._slide_sep()
        )
    def two_image_left_layout(
        self,
        title: str,
        content: List[str],
        img1_path: str,
        img2_path: str,
        image_width: str = "22.5%",
        caption1: Optional[str] = None,
        caption2: Optional[str] = None,
    ) -> str:
        """
        Title + two stacked images left, text right.
        """
        li_items = "\n".join(f"        <li>{item}</li>" for item in content)
        caption1_html = (
            f'\n        <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0; "><b>{caption1}</b></p>'
            if caption1 else ""
        )
        caption2_html = (
            f'\n        <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0; "><b>{caption2}</b></p>'
            if caption2 else ""
        )

        return (
            "\n\n"
            f'<div style="\n'
            f'    --image-width: {image_width};\n'
            f'    display: flex; flex-direction: column; height: 100%;">'  "\n"
            "\n"
            "  <!-- Title -->\n"
            "  <div>\n"
            f"    {self._h1(title)}\n"
            "  </div>\n"
            "\n"
            '  <div style="display: grid;\n'
            "              grid-template-columns: var(--image-width) 1fr;\n"
            "              align-items: start;\n"
            "              gap: 1rem;\n"
            '              flex: 1; min-height: 0;">\n'
            "    <!-- Left: images -->\n"
            '    <div style="container-type: inline-size;">\n'
            "      <div>\n"
            f'        <img src="{img1_path}" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />{caption1_html}\n'
            "      </div>\n"
            "      <div>\n"
            f'        <img src="{img2_path}" style="width: 100%; max-width: 100%; max-height: 100%; display: block; object-fit: contain;" />{caption2_html}\n'
            "      </div>\n"
            "    </div>\n"
            "    <!-- Right: text -->\n"
            '    <div style="overflow: auto; font-size: 1rem">\n'
            "      <ul>\n"
            f"{li_items}\n"
            "      </ul>\n"
            "    </div>\n"
            "  </div>\n"
            "</div>\n"
            + self._slide_sep()
        )

    def two_image_above_layout(
        self,
        title: str,
        content: List[str],
        img1_path: str,
        img2_path: str,
        image_width: str = "60%",
        caption1: Optional[str] = None,
        caption2: Optional[str] = None,
    ) -> str:
        """
        Title + two images side-by-side above, bullet content below.
        """
        bullet_lines = "\n".join(f"- {item}" for item in content)
        caption1_html = (
            f'\n    <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>{caption1}</b></p>'
            if caption1 else ""
        )
        caption2_html = (
            f'\n    <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>{caption2}</b></p>'
            if caption2 else ""
        )

        return (
            "\n\n"
            + self._h1(title)
            + "\n\n"
            + f'<div style="width: {image_width}; margin: auto; display: flex; gap: 1rem;">\n'
            + '  <div style="flex: 1; container-type: inline-size;">\n'
            + f'    <img src="{img1_path}" style="width: 100%; max-height: 100%; max-width: 100%; display: block; object-fit: contain;" />{caption1_html}\n'
            + '  </div>\n'
            + '  <div style="flex: 1; container-type: inline-size;">\n'
            + f'    <img src="{img2_path}" style="width: 100%; max-height: 100%; max-width: 100%; display: block; object-fit: contain;" />{caption2_html}\n'
            + '  </div>\n'
            + '</div>\n'
            + "\n"
            + bullet_lines
            + "\n"
            + self._slide_sep()
        )

    def two_image_below_layout(
        self,
        title: str,
        content: List[str],
        img1_path: str,
        img2_path: str,
        image_width: str = "60%",
        caption1: Optional[str] = None,
        caption2: Optional[str] = None,
    ) -> str:
        """
        Title + bullet content above, two images side-by-side below.
        """
        bullet_lines = "\n".join(f"- {item}" for item in content)
        caption1_html = (
            f'\n    <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>{caption1}</b></p>'
            if caption1 else ""
        )
        caption2_html = (
            f'\n    <p style="text-align:center; font-size: 2.5cqw; line-height: 1.2; margin: 0.1rem 0 0 0;"><b>{caption2}</b></p>'
            if caption2 else ""
        )

        return (
            "\n\n"
            + self._h1(title)
            + "\n\n"
            + bullet_lines
            + "\n\n"
            + f'<div style="width: {image_width}; margin: auto; display: flex; gap: 1rem;">\n'
            + '  <div style="flex: 1; container-type: inline-size;">\n'
            + f'    <img src="{img1_path}" style="width: 100%; max-height: 100%; max-width: 100%; display: block; object-fit: contain;" />{caption1_html}\n'
            + '  </div>\n'
            + '  <div style="flex: 1; container-type: inline-size;">\n'
            + f'    <img src="{img2_path}" style="width: 100%; max-height: 100%; max-width: 100%; display: block; object-fit: contain;" />{caption2_html}\n'
            + '  </div>\n'
            + '</div>\n'
            + self._slide_sep()
        )

    def two_cols_content_layout(
        self,
        title: str,
        content: List[str],
    ) -> str:
        """
        Title + content split evenly into two columns.
        The content list is divided in half: first half goes left, second half goes right.
        """
        mid = (len(content) + 1) // 2
        left_items = content[:mid]
        right_items = content[mid:]

        li_left = "\n".join(f"        <li>{item}</li>" for item in left_items)
        li_right = "\n".join(f"        <li>{item}</li>" for item in right_items)

        return (
            "\n\n"
            f'<div style="\n'
            f'    --left-width: 45%;\n'
            f'    --right-width: 45%;\n'
            f'    display: flex; flex-direction: column; height: 100%;">\n'
            "\n"
            "  <!-- Title -->\n"
            "  <div>\n"
            f"    {self._h1(title)}\n"
            "  </div>\n"
            "\n"
            '  <div style="display: grid;\n'
            "              grid-template-columns: var(--left-width) var(--right-width);\n"
            "              align-items: start;\n"
            "              gap: 2.5rem;\n"
            '              flex: 1; min-height: 0;">\n'
            "    <!-- Left -->\n"
            '    <div style="overflow: auto;">\n'
            "      <ul>\n"
            f"{li_left}\n"
            "      </ul>\n"
            "    </div>\n"
            "    <!-- Right -->\n"
            '    <div style="overflow: auto; font-size: 1rem">\n'
            "      <ul>\n"
            f"{li_right}\n"
            "      </ul>\n"
            "    </div>\n"
            "  </div>\n"
            "</div>\n"
            + self._slide_sep()
        )

    def end_layout(self, end_text: str = "Thank you for listening") -> str:
        """
        Closing cover slide.
        """
        lines = [
            "\nlayout: cover",
            "---",
            "",
            f"# {end_text}",
        ]
        return "\n".join(lines)
