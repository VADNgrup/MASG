"""
LLM-Powered Matplotlib Chart Generator

Uses LLM to analyze tables and generate matplotlib code for visualization.
More flexible and reliable than LIDA approach.
"""

import llm_extension

from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
import io
import re
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from openai import OpenAI
from src.utils.config import config
from src.utils.parse_llm_response import clear_think

class MatplotlibChartGenerator:
    """
    Generate charts from markdown tables using LLM-generated matplotlib code
    """
    
    def __init__(self):
        """Initialize with OpenAI client"""
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL if hasattr(config, 'OPENAI_MODEL') else "qwen3-30b-a3b-instruct-2507"
        print("Matplotlib Chart Generator initialized successfully")
    
    def markdown_to_dataframe(self, markdown: str) -> Optional[pd.DataFrame]:
        """
        Convert markdown table to pandas DataFrame
        
        Args:
            markdown: Markdown table string
            
        Returns:
            pandas DataFrame or None if conversion fails
        """
        try:
            # Clean markdown table
            lines = markdown.strip().split('\n')
            
            # Remove separator line (e.g., |---|---|)
            cleaned_lines = [line for line in lines if not re.match(r'^\s*\|[\s\-:]+\|\s*$', line)]
            
            if len(cleaned_lines) < 2:
                print(f"Table has insufficient rows: {len(cleaned_lines)}")
                return None
            
            # Convert to CSV-like format
            csv_lines = []
            for line in cleaned_lines:
                # Remove leading/trailing pipes and whitespace
                line = line.strip().strip('|')
                # Split by pipe and clean each cell
                cells = [cell.strip() for cell in line.split('|')]
                csv_lines.append(','.join(cells))
            
            csv_string = '\n'.join(csv_lines)
            
            # Read as DataFrame
            df = pd.read_csv(io.StringIO(csv_string))
            
            print(f"Converted table to DataFrame: {df.shape[0]} rows × {df.shape[1]} columns")
            return df
            
        except Exception as e:
            print(f"Failed to convert markdown to DataFrame: {e}")
            return None
    
    def generate_matplotlib_code(self, table_markdown: str, table_id: str) -> Optional[str]:
        """
        Use LLM to analyze table and generate matplotlib code
        
        Args:
            table_markdown: Markdown table string
            table_id: Table identifier
            
        Returns:
            Python matplotlib code as string, or None if generation fails
        """
        try:
            prompt = f"""Analyze this data table and generate Python matplotlib code to visualize it.

Table:
{table_markdown}

Requirements:
1. Choose the MOST APPROPRIATE chart type (bar, line, scatter, pie, grouped bar, etc.)
2. Generate COMPLETE, EXECUTABLE Python code using matplotlib
3. Use clear labels, title, and legend
4. Set figure size to (10, 6)
5. Use professional styling with good colors
6. Save figure as PNG with: plt.savefig(output_path, dpi=150, bbox_inches='tight')
7. Close figure with: plt.close()

IMPORTANT:
- Code must be COMPLETE and EXECUTABLE
- Include all necessary imports (matplotlib.pyplot as plt, pandas as pd, numpy as np if needed)
- Handle data conversion (e.g., remove % signs, convert to numeric)
- Use Vietnamese labels if table has Vietnamese text
- The code will receive 'output_path' variable - use it to save the chart

Return ONLY the Python code, no explanations."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert data visualization engineer. Generate clean, executable matplotlib code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            code = clear_think(response.choices[0].message.content)
            
            # Extract code from markdown if wrapped
            if '```python' in code:
                code = code.split('```python')[1].split('```')[0].strip()
            elif '```' in code:
                code = code.split('```')[1].split('```')[0].strip()
            
            print(f"  ✓ Generated matplotlib code ({len(code)} chars)")
            return code
            
        except Exception as e:
            print(f"  ✗ Failed to generate matplotlib code: {e}")
            return None
    
    def execute_matplotlib_code(
        self,
        code: str,
        table_markdown: str,
        output_path: Path
    ) -> bool:
        """
        Execute matplotlib code to generate chart
        
        Args:
            code: Python matplotlib code
            table_markdown: Original table markdown
            output_path: Path to save chart
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare execution environment
            exec_globals = {
                'plt': plt,
                'pd': pd,
                'output_path': str(output_path),
                'table_markdown': table_markdown,
                '__builtins__': __builtins__,
            }
            
            # Also import numpy in case it's needed
            import numpy as np
            exec_globals['np'] = np
            
            # Execute the code
            exec(code, exec_globals)
            
            if output_path.exists():
                print(f"  ✓ Chart saved: {output_path}")
                return True
            else:
                print(f"  ✗ Chart file not created")
                return False
                
        except Exception as e:
            print(f"  ✗ Failed to execute matplotlib code: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_chart_from_table(
        self,
        table_markdown: str,
        table_id: str,
        output_dir: Path,
        chart_title: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """
        Generate chart from markdown table using LLM + matplotlib
        
        Args:
            table_markdown: Markdown table string
            table_id: Unique identifier for the table
            output_dir: Directory to save chart image
            chart_title: Optional title for the chart
            
        Returns:
            Dict with chart_path and chart_type, or None if generation fails
        """
        try:
            print(f"\n  [Chart Generation] {table_id}")
            
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Generate matplotlib code using LLM
            print(f"  → Generating matplotlib code...")
            code = self.generate_matplotlib_code(table_markdown, table_id)
            
            if not code:
                return None
            
            # Step 2: Execute code to create chart
            chart_filename = f"{table_id}_chart.png"
            chart_path = output_dir / chart_filename
            
            print(f"  → Executing code to generate chart...")
            success = self.execute_matplotlib_code(code, table_markdown, chart_path)
            
            if not success:
                return None
            
            # Determine chart type from code (simple heuristic)
            chart_type = "bar"  # default
            if "plot(" in code or "line" in code.lower():
                chart_type = "line"
            elif "scatter" in code.lower():
                chart_type = "scatter"
            elif "pie" in code.lower():
                chart_type = "pie"
            elif "bar" in code.lower():
                chart_type = "bar"
            
            return {
                "chart_path": str(chart_path),
                "chart_type": chart_type
            }
            
        except Exception as e:
            print(f"  ✗ Chart generation failed for {table_id}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_charts_for_tables(
        self,
        tables: List[Dict[str, Any]],
        document_id: str,
        base_output_dir: Path = Path("data/assets")
    ) -> List[Dict[str, Any]]:
        """
        Generate charts for multiple tables
        
        Args:
            tables: List of table dictionaries with 'table_id', 'markdown', 'should_visualize'
            document_id: Document identifier
            base_output_dir: Base directory for assets
            
        Returns:
            Updated list of tables with chart_path and chart_type added
        """
        output_dir = base_output_dir / document_id / "charts"
        
        print(f"\n{'='*60}")
        print(f"MATPLOTLIB CHART GENERATION")
        print(f"{'='*60}")
        print(f"Document: {document_id}")
        print(f"Output: {output_dir}")
        
        updated_tables = []
        generated_count = 0
        
        for table in tables:
            table_copy = table.copy()
            
            # Only generate for tables marked for visualization
            if table.get('should_visualize', 'No') == 'Yes':
                print(f"\n[{table['table_id']}] Generating chart...")
                
                result = self.generate_chart_from_table(
                    table_markdown=table['markdown'],
                    table_id=table['table_id'],
                    output_dir=output_dir
                )
                
                if result:
                    table_copy['chart_path'] = result['chart_path']
                    table_copy['chart_type'] = result['chart_type']
                    generated_count += 1
                    print(f"  ✓ Success: {result['chart_type']} chart")
                else:
                    print(f"  ✗ Failed to generate chart")
            else:
                print(f"\n[{table['table_id']}] Skipped (should_visualize=No)")
            
            updated_tables.append(table_copy)
        
        print(f"\n{'='*60}")
        print(f"✓ Generated {generated_count}/{len([t for t in tables if t.get('should_visualize') == 'Yes'])} charts")
        print(f"{'='*60}\n")
        
        return updated_tables
