"""
SlideLayoutManager - generates Slidev-compatible markdown strings for each slide type.

Usage example:
    mgr = SlideLayoutManager()
    doc  = mgr.slide_config()
    doc += mgr.greet_and_goodbye_slide("Welcome!", "Prof. Nguyen")
    doc += mgr.table_content_slide("Outline", ["1. Intro", "2. Method"])
    doc += mgr.slide_with_one_side_image("Results", ["Acc 95%"], "/assets/fig.png")
    doc += mgr.greet_and_goodbye_slide("Thank you!", "Q&A")
    # write doc to a .md file and run: slidev <file>.md
"""

from __future__ import annotations
from typing import Dict, List


class SlideLayoutManager:
    """Generates Slidev markdown slide strings for all supported layout types."""

    # ------------------------------------------------------------------ #
    #  Init                                                                #
    # ------------------------------------------------------------------ #
    def __init__(self, title_color_code: str = "#e2b96f"):
        self.title_color_code = title_color_code

    # ------------------------------------------------------------------ helpers
    def _h1(self, text: str, color: str | None = None) -> str:
        """Return an <h1> tag with optional inline color."""
        c = color or self.title_color_code
        return f'<h1 style="color: {c};">{text}</h1>'

    def _h2(self, text: str, color: str | None = None) -> str:
        c = color or self.title_color_code
        return f'<h2 style="color: {c};">{text}</h2>'

    def _bullet_lines(self, contents: List[str]) -> str:
        """Convert a list of strings to markdown bullet lines."""
        return "\n".join(f"- {item}" for item in contents)

    # ------------------------------------------------------------------ #
    #  1. Global slide config (frontmatter for the whole file)             #
    # ------------------------------------------------------------------ #
    def slide_config(
        self,
        theme: str = "seriph",
        title: str = "Demo Slidev",
        info: str = "Slide",
        katex: bool = True,
        font_sans: str = "Roboto",
        font_serif: str = "Roboto",
        font_mono: str = "Roboto",
        background_path: str = "/assets/slide_7_img_00.png",
    ) -> str:
        """
        Return the global frontmatter block (first slide config).
        Must be called first; all other methods append after this.
        """
        katex_str = "true" if katex else "false"
        return (
            f"---\n"
            f"theme: {theme}\n"
            f"title: {title}\n"
            f"info: {info}\n"
            f"katex: {katex_str}\n"
            f"fonts:\n"
            f"  sans: {font_sans}\n"
            f"  serif: {font_serif}\n"
            f"  mono: {font_mono}\n"
            f"background: {background_path}\n"
            f"---\n"
        )

    # ------------------------------------------------------------------ #
    #  2. Greeting / Goodbye slide                                         #
    # ------------------------------------------------------------------ #
    def greeting_slide(
        self,
        title: str,
        speaker_information: str,
        title_color_code: str | None = None,
        speaker_information_color_code: str | None = None,
    ) -> str:
        """
        First slide: plain h1/h2 content that lives in the opening frontmatter
        slide (shares `background:` from slide_config). No layout frontmatter.
        """
        t_color = title_color_code or self.title_color_code
        s_color = speaker_information_color_code or self.title_color_code
        return (
            f"\n"
            f"{self._h1(title, t_color)}\n"
            f"{self._h2(speaker_information, s_color)}\n"
            f"---\n"
        )

    def greet_and_goodbye_slide(
        self,
        title: str,
        speaker_information: str,
        title_color_code: str | None = None,
        speaker_information_color_code: str | None = None,
    ) -> str:
        """
        Goodbye slide using the slide_gate layout (centered, large title).
        """
        t_color = title_color_code or self.title_color_code
        s_color = speaker_information_color_code or self.title_color_code
        return (
            f"layout: slide_gate\n"
            f"---\n"
            f"\n"
            f"::lecture_name::\n"
            f"{self._h1(title, t_color)}\n"
            f"\n"
            f"::speaker_infor::\n"
            f"{self._h2(speaker_information, s_color)}\n"
            f"---\n"
        )


    # ------------------------------------------------------------------ #
    #  3. Table of Contents                                               #
    # ------------------------------------------------------------------ #
    def table_content_slide(self, title: str, contents: List[str]) -> str:
        """
        Chooses single-column (< 600 chars total) or two-column layout
        automatically, then renders the TOC slide.
        """
        total_chars = sum(len(s) for s in contents)

        if total_chars < 600:
            return self._toc_single(title, contents)
        else:
            return self._toc_two_col(title, contents)

    def _toc_single(self, title: str, contents: List[str]) -> str:
        import re as _re

        def _is_major(s: str) -> bool:
            return bool(_re.match(r"^\d+\.\s+\S", s)) and s.split(".")[0].strip().isdigit()

        lines = []
        for i, item in enumerate(contents):
            is_last   = (i == len(contents) - 1)
            next_major = (not is_last) and _is_major(contents[i + 1])
            suffix = " " if is_last or next_major else " \\"
            lines.append(f" {item}{suffix}")
        content_str = "\n".join(lines)
        return (
            f"\n"
            f"{self._h1(title)}\n"
            f"<p></p>\n"
            f"\n"
            f"{content_str}\n"
            f"\n"
        )

    def _toc_two_col(self, title: str, contents: List[str]) -> str:
        # Split roughly in half by count
        mid = (len(contents) + 1) // 2
        left_items = contents[:mid]
        right_items = contents[mid:]

        def _fmt(items: List[str]) -> str:
            lines = []
            for i, item in enumerate(items):
                if i == len(items) - 1:
                    lines.append(f" {item} ")
                else:
                    lines.append(f" {item} \\")
            return "\n".join(lines)

        left_str  = _fmt(left_items)
        right_str = _fmt(right_items)

        return (
            f"\n"
            f"---\n"
            f"layout: two-cols-content\n"
            f"---\n"
            f"\n"
            f"::title::\n"
            f"{self._h1(title)}\n"
            f"\n"
            f"::left::\n"
            f"\n"
            f"{left_str}\n"
            f"\n"
            f"::right::\n"
            f"\n"
            f"{right_str}\n"
        )

    # ------------------------------------------------------------------ #
    #  4. Content-only slide                                              #
    # ------------------------------------------------------------------ #
    def slide_only_content(self, title: str, contents: List[str]) -> str:
        """Single-column slide with title and bullet points."""
        bullets = self._bullet_lines(contents)
        return (
            f"---\n"
            f"\n"
            f"{self._h1(title)}\n"
            f"\n"
            f"{bullets}\n"
        )

    # ------------------------------------------------------------------ #
    #  5. Two-column content slide                                        #
    # ------------------------------------------------------------------ #
    def slide_two_contents(self, title: str, contents: List[str]) -> str:
        """
        Split bullet points across two columns, filling column 1 first.
        The split point is chosen to balance character length visually.
        """
        # Find split index that balances character length
        total = sum(len(s) for s in contents)
        target = total / 2
        running = 0
        mid = 1
        for i, item in enumerate(contents):
            running += len(item)
            if running >= target:
                mid = i + 1
                break

        # Ensure at least one item per column
        mid = max(1, min(mid, len(contents) - 1))
        left_items  = contents[:mid]
        right_items = contents[mid:]

        left_str  = self._bullet_lines(left_items)
        right_str = self._bullet_lines(right_items)

        return (
            f"\n"
            f"---\n"
            f"layout: two-cols-content\n"
            f"---\n"
            f"\n"
            f"::title::\n"
            f"{self._h1(title)}\n"
            f"\n"
            f"::left::\n"
            f"{left_str}\n"
            f"\n"
            f"::right::\n"
            f"{right_str}\n"
        )

    # ------------------------------------------------------------------ #
    #  6. Comparison slide                                                #
    # ------------------------------------------------------------------ #
    def slide_comparison(
        self,
        title: str,
        content: Dict[str, List[str]],
    ) -> str:
        """
        Two-column comparison.
        `content` must be a dict with exactly 2 keys: {label: [bullets]}.
        """
        keys = list(content.keys())
        if len(keys) != 2:
            raise ValueError("slide_comparison requires exactly 2 keys in `content`.")

        left_label,  right_label  = keys[0], keys[1]
        left_bullets  = self._bullet_lines(content[left_label])
        right_bullets = self._bullet_lines(content[right_label])

        return (
            f"\n"
            f"---\n"
            f"layout: comparison\n"
            f"---\n"
            f"\n"
            f"::title::\n"
            f"{self._h1(title)}\n"
            f"\n"
            f"::left-title::\n"
            f"## {left_label}\n"
            f"\n"
            f"::left::\n"
            f"{left_bullets}\n"
            f"\n"
            f"::right-title::\n"
            f"## {right_label}\n"
            f"\n"
            f"::right::\n"
            f"{right_bullets}\n"
        )

    # ------------------------------------------------------------------ #
    #  7. Slides with images                                              #
    # ------------------------------------------------------------------ #
    def slide_with_one_side_image(
        self,
        title: str,
        contents: List[str],
        img_path: str,
        image_width: str = "40%",
    ) -> str:
        """Bullet points on the left, one image on the right (split layout)."""
        bullets = self._bullet_lines(contents)
        return (
            f"\n"
            f"---\n"
            f"layout: split\n"
            f"imageWidth: {image_width}\n"
            f"---\n"
            f"\n"
            f"::title::\n"
            f"{self._h1(title)}\n\n"
            f"::left::\n"
            f"{bullets}\n"
            f"::right::\n"
            f'<img src="{img_path}" class="max-w-full max-h-full mx-auto"/>\n'
            f"\n"
        )

    def slide_with_two_side_image(
        self,
        title: str,
        contents: List[str],
        img_path_1: str,
        img_path_2: str,
        image_width: str = "30%",
    ) -> str:
        """Bullet points on the left, two stacked images on the right."""
        bullets = self._bullet_lines(contents)
        return (
            f"\n"
            f"---\n"
            f"layout: split-2-right-component\n"
            f"imageWidth: {image_width}\n"
            f"---\n"
            f"\n"
            f"::title::\n"
            f"{self._h1(title)}\n"
            f"\n"
            f"::left::\n"
            f"{bullets}\n"
            f"\n"
            f"::right-top::\n"
            f'<img src="{img_path_1}" class="max-w-full max-h-full mx-auto"/>\n'
            f"::right-bottom::\n"
            f'<img src="{img_path_2}" class="max-w-full max-h-full mx-auto"/>\n'
            f"\n"
        )

    def slide_with_one_above_image(
        self,
        title: str,
        contents: List[str],
        img_path: str,
        image_height: str = "50%",
    ) -> str:
        """Image on top, bullet points below (image_above layout)."""
        bullets = self._bullet_lines(contents)
        return (
            f"\n"
            f"---\n"
            f"layout: image_above\n"
            f"imageHeight: {image_height}\n"
            f"---\n"
            f"\n"
            f"::title::\n"
            f"{self._h1(title)}\n"
            f"\n"
            f"::image::\n"
            f'<img src="{img_path}" class="max-w-full max-h-full mx-auto"/>\n'
            f"\n"
            f"::content::\n"
            f"{bullets}\n"
        )
