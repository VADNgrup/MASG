"""
LIDA Chart Generator

Automatically generates charts from markdown tables using Microsoft's LIDA library.
LIDA uses LLMs to create intelligent, data-driven visualizations.
"""

import pinkyne_extension

from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
import io
import re
from lida import Manager, TextGenerationConfig, llm
from src.utils.config import config

class LidaChartGenerator:
    """
    Generate charts from markdown tables using LIDA (Microsoft's automatic visualization library)
    """
    
    def __init__(self):
        """Initialize LIDA with OpenAI text generation"""
        try:
            # Initialize LIDA with OpenAI LLM
            self.lida = Manager(text_gen=llm("openai"))
            self.text_gen_config = TextGenerationConfig(
                n=1,
                temperature=0.3,
                model=config.OPENAI_MODEL if hasattr(config, 'OPENAI_MODEL') else "gpt-4o-mini",
                use_cache=True
            )
            print("✓ LIDA Chart Generator initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize LIDA: {e}")
            self.lida = None
    
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
                print(f"  ⚠ Table has insufficient rows: {len(cleaned_lines)}")
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
            
            print(f"  ✓ Converted table to DataFrame: {df.shape[0]} rows × {df.shape[1]} columns")
            return df
            
        except Exception as e:
            print(f"  ✗ Failed to convert markdown to DataFrame: {e}")
            return None
    
    def select_best_chart_type(self, summary: Dict[str, Any], goals: List[Dict]) -> str:
        """
        Select the most appropriate chart type based on data summary and goals
        
        Args:
            summary: LIDA data summary
            goals: List of visualization goals from LIDA
            
        Returns:
            Chart type string (bar, line, scatter, pie, etc.)
        """
        if not goals:
            return "bar"  # Default fallback
        
        # Get the first (highest priority) goal
        top_goal = goals[0]
        
        # Extract chart type from goal if available
        if 'visualization' in top_goal:
            viz_type = top_goal['visualization'].lower()
            if 'bar' in viz_type:
                return 'bar'
            elif 'line' in viz_type:
                return 'line'
            elif 'scatter' in viz_type:
                return 'scatter'
            elif 'pie' in viz_type:
                return 'pie'
        
        # Fallback to bar chart
        return 'bar'
    
    def generate_chart_from_table(
        self,
        table_markdown: str,
        table_id: str,
        output_dir: Path,
        chart_title: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """
        Generate chart from markdown table using LIDA
        
        Args:
            table_markdown: Markdown table string
            table_id: Unique identifier for the table
            output_dir: Directory to save chart image
            chart_title: Optional title for the chart
            
        Returns:
            Dict with chart_path and chart_type, or None if generation fails
        """
        if not self.lida:
            print(f"  ✗ LIDA not initialized, skipping chart generation for {table_id}")
            return None
        
        try:
            print(f"\n  [Chart Generation] {table_id}")
            
            # Step 1: Convert markdown to DataFrame
            df = self.markdown_to_dataframe(table_markdown)
            if df is None:
                return None
            
            # Check if table has numeric data
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) == 0:
                print(f"  ⚠ No numeric columns found, skipping visualization")
                return None
            
            # Step 2: Save DataFrame to temporary CSV for LIDA
            temp_csv = output_dir / f"{table_id}_temp.csv"
            output_dir.mkdir(parents=True, exist_ok=True)
            df.to_csv(temp_csv, index=False)
            
            # Step 3: Use LIDA to summarize data
            print(f"  → Summarizing data...")
            summary = self.lida.summarize(
                str(temp_csv),
                summary_method="default",
                textgen_config=self.text_gen_config
            )
            
            # Step 4: Generate visualization goals
            print(f"  → Generating visualization goals...")
            goals = self.lida.goals(
                summary,
                n=3,  # Generate top 3 goals
                textgen_config=self.text_gen_config
            )
            
            if not goals:
                print(f"  ⚠ No visualization goals generated")
                temp_csv.unlink()  # Clean up temp file
                return None
            
            # Step 5: Select best chart type
            chart_type = self.select_best_chart_type(summary, goals)
            print(f"  → Selected chart type: {chart_type}")
            
            # Step 6: Generate visualization
            print(f"  → Generating visualization...")
            visualizations = self.lida.visualize(
                summary=summary,
                goal=goals[0],  # Use top goal
                textgen_config=self.text_gen_config,
                library="matplotlib"  # Use matplotlib for PNG output
            )
            
            if not visualizations:
                print(f"  ✗ No visualizations generated")
                temp_csv.unlink()
                return None
            
            # Step 7: Save chart as PNG
            chart_filename = f"{table_id}_chart.png"
            chart_path = output_dir / chart_filename
            
            # LIDA returns visualization with code and raster (base64 image)
            viz = visualizations[0]
            
            # Save the chart
            if hasattr(viz, 'raster') and viz.raster:
                # Decode base64 and save
                import base64
                image_data = base64.b64decode(viz.raster)
                with open(chart_path, 'wb') as f:
                    f.write(image_data)
                print(f"  ✓ Chart saved: {chart_path}")
            else:
                print(f"  ✗ No raster image in visualization")
                temp_csv.unlink()
                return None
            
            # Clean up temp CSV
            temp_csv.unlink()
            
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
        print(f"LIDA CHART GENERATION")
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
