"""
Generate charts for tables in a document context using LLM + Matplotlib

This script processes a DocumentContext JSON file and generates charts
for all tables marked with should_visualize="Yes"

Usage:
    python -m src.preprocessor.generate_charts --context data/context/{doc_id}.json
"""

import argparse
import json
from pathlib import Path
from src.models.context import DocumentContext
from src.integrations.matplotlib_chart_generator import MatplotlibChartGenerator
from src.utils.file_utils import load_json, save_json

def generate_charts_for_context(context_path: str) -> DocumentContext:
    """
    Load context, generate charts for visualizable tables, update and save context
    
    Args:
        context_path: Path to context JSON file
        
    Returns:
        Updated DocumentContext with chart paths
    """
    print(f"\n{'='*70}")
    print(f"CHART GENERATION FOR CONTEXT")
    print(f"{'='*70}")
    print(f"Context: {context_path}\n")
    
    # Load context
    context_data = load_json(context_path)
    context = DocumentContext(**context_data)
    
    print(f"Document ID: {context.document_id}")
    print(f"Total tables: {len(context.tables)}")
    
    # Count visualizable tables
    visualizable_count = sum(1 for t in context.tables if t.should_visualize == "Yes")
    print(f"Visualizable tables: {visualizable_count}")
    
    if visualizable_count == 0:
        print("\n⚠ No tables marked for visualization. Skipping chart generation.")
        return context
    
    # Initialize chart generator (NEW: using matplotlib instead of LIDA)
    chart_generator = MatplotlibChartGenerator()
    
    # Convert tables to dict format for generator
    tables_dict = [
        {
            "table_id": t.table_id,
            "markdown": t.markdown,
            "should_visualize": t.should_visualize
        }
        for t in context.tables
    ]
    
    # Generate charts
    updated_tables_dict = chart_generator.generate_charts_for_tables(
        tables=tables_dict,
        document_id=context.document_id
    )
    
    # Update context with chart information
    for i, table in enumerate(context.tables):
        updated_table = updated_tables_dict[i]
        if 'chart_path' in updated_table:
            table.chart_path = updated_table['chart_path']
            table.chart_type = updated_table['chart_type']
    
    # Save updated context
    context_path_obj = Path(context_path)
    updated_context_data = context.model_dump()
    save_json(updated_context_data, context_path)
    
    print(f"\n✓ Context updated and saved: {context_path}")
    
    # Print summary
    charts_generated = sum(1 for t in context.tables if t.chart_path is not None)
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Charts generated: {charts_generated}/{visualizable_count}")
    print(f"Charts saved to: data/assets/{context.document_id}/charts/")
    print(f"{'='*70}\n")
    
    return context

def main():
    parser = argparse.ArgumentParser(description="Generate charts for tables in document context")
    parser.add_argument(
        "--context",
        type=str,
        required=True,
        help="Path to context JSON file (e.g., data/context/doc_id.json)"
    )
    
    args = parser.parse_args()
    
    # Validate context file exists
    context_path = Path(args.context)
    if not context_path.exists():
        print(f"✗ Error: Context file not found: {context_path}")
        return
    
    # Generate charts
    try:
        generate_charts_for_context(str(context_path))
    except Exception as e:
        print(f"\n✗ Error during chart generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
