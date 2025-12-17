from typing import List, Dict, Any
import re

class TableToMarkdownConverter:
    @staticmethod
    def convert(table_text: str) -> str:
        lines = table_text.strip().split('\n')
        
        if not lines:
            return ""
        
        if '|' in table_text:
            return table_text
        
        rows = []
        for line in lines:
            cells = re.split(r'\s{2,}|\t', line.strip())
            cells = [cell.strip() for cell in cells if cell.strip()]
            if cells:
                rows.append(cells)
        
        if not rows:
            return table_text
        
        markdown_lines = []
        
        header = rows[0]
        markdown_lines.append('| ' + ' | '.join(header) + ' |')
        markdown_lines.append('| ' + ' | '.join(['---'] * len(header)) + ' |')
        
        for row in rows[1:]:
            while len(row) < len(header):
                row.append('')
            markdown_lines.append('| ' + ' | '.join(row[:len(header)]) + ' |')
        
        return '\n'.join(markdown_lines)
    
    @staticmethod
    def parse_and_convert(table_data: Dict[str, Any]) -> str:
        content = table_data.get('content', '')
        return TableToMarkdownConverter.convert(content)

