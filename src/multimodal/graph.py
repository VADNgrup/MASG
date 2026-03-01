from langgraph.graph import StateGraph, END
from typing import Dict, Any
import json
from pathlib import Path

from src.multimodal.state import MultimodalState
from src.multimodal.agents.generate_query import GenerateQueryAgent
from src.multimodal.agents.visual_aggregation import VisualAggregation
from src.multimodal.agents.image_distribution import ImageDistribution
from src.multimodal.agents.table_chart_distribution import TableChartDistribution


def create_multimodal_workflow() -> StateGraph:
    """
    Create a LangGraph workflow for multimodal processing.
    
    Flow:
        load_lecture → generate_queries → aggregate_media → [table_chart_distribution, image_distribution] → END
    
    Returns:
        Compiled StateGraph workflow
    """
    workflow = StateGraph(MultimodalState)
    
    # Initialize agents
    query_agent = GenerateQueryAgent("qwen3-30b-a3b")
    aggregation_agent = VisualAggregation()
    image_distribution_agent = ImageDistribution()
    table_distribution_agent = TableChartDistribution()
    
    def load_lecture_node(state: MultimodalState) -> Dict[str, Any]:
        """Load lecture JSON file into state"""
        lecture_id = state["lecture_id"]
        lecture_path = Path(f"data/lectures/{lecture_id}.json")
        
        if not lecture_path.exists():
            raise FileNotFoundError(f"Lecture file not found: {lecture_path}")
        
        with open(lecture_path, 'r', encoding='utf-8') as f:
            lecture_dict = json.load(f)
        
        print(f"Loaded lecture: {lecture_id}")
        print(f"   Total slides: {lecture_dict.get('metadata', {}).get('total_slides', 'N/A')}")
        
        return {
            "lecture_dict": lecture_dict
        }
    
    def generate_queries_node(state: MultimodalState) -> Dict[str, Any]:
        """Generate visualization queries from lecture slides"""
        lecture_dict = state["lecture_dict"]
        
        print("\nGenerating visualization queries...")
        need_visualization = query_agent.generate_visualization_queries(
            lecture_dict=lecture_dict
        )
        
        print(f"Generated {len(need_visualization)} visualization queries")
        for item in need_visualization[:3]:  # Show first 3
            print(f"   - Slide {item['slide_number']}: {item['query'][:60]}...")
        if len(need_visualization) > 3:
            print(f"   ... and {len(need_visualization) - 3} more")
        
        return {
            "need_visualization": need_visualization
        }
    
    def aggregate_media_node(state: MultimodalState) -> Dict[str, Any]:
        """Aggregate tables and images from context file"""
        lecture_dict = state["lecture_dict"]
        
        print("\nAggregating media (tables and images)...")
        aggregated_media = aggregation_agent.aggregate_media_from_lecture(lecture_dict)
        
        print(f"Aggregated media:")
        print(f"   - Tables: {aggregated_media['total_tables']}")
        print(f"   - Images: {aggregated_media['total_images']}")
        
        return {
            "aggregated_media": aggregated_media
        }
    
    def distribute_images_node(state: MultimodalState) -> Dict[str, Any]:
        """Distribute images to slides using CLIP scoring"""
        lecture_id = state["lecture_id"]
        need_visualization = state["need_visualization"]
        aggregated_media = state["aggregated_media"]
        used_images = state.get("used_images", set())
        
        print("\nDistributing images to slides...")
        distributions = image_distribution_agent.distribute_images(
            lecture_id=lecture_id,
            need_visualization=need_visualization,
            aggregated_media=aggregated_media,
            used_images=used_images
        )
        
        print(f"\nDistributed {len(distributions)} images to slides")
        print(f"   aggregated_media total_images after distribution: {aggregated_media.get('total_images', 0)}")
        
        return {
            "image_distributions": distributions,
            "aggregated_media": aggregated_media,  # propagate mutations (downloaded images added)
            "used_images": used_images
        }
    
    def distribute_tables_node(state: MultimodalState) -> Dict[str, Any]:
        """Distribute tables to slides using LLM scoring"""
        lecture_id = state["lecture_id"]
        lecture_dict = state["lecture_dict"]
        aggregated_media = state["aggregated_media"]
        used_tables = state.get("used_tables", set())
        
        print("\nDistributing tables to slides...")
        distributions = table_distribution_agent.distribute_tables(
            lecture_id=lecture_id,
            lecture_dict=lecture_dict,
            aggregated_media=aggregated_media,
            used_tables=used_tables
        )
        
        print(f"\nDistributed {len(distributions)} tables to slides")
        
        return {
            "table_distributions": distributions,
            "used_tables": used_tables
        }
    
    # Add nodes to workflow
    workflow.add_node("load_lecture", load_lecture_node)
    workflow.add_node("generate_queries", generate_queries_node)
    workflow.add_node("aggregate_media", aggregate_media_node)
    workflow.add_node("distribute_images", distribute_images_node)
    workflow.add_node("distribute_tables", distribute_tables_node)
    
    # Define workflow edges
    workflow.set_entry_point("load_lecture")
    workflow.add_edge("load_lecture", "generate_queries")
    workflow.add_edge("generate_queries", "aggregate_media")
    # Parallel execution: both table and image distribution run after aggregate_media
    workflow.add_edge("aggregate_media", "distribute_images")
    workflow.add_edge("aggregate_media", "distribute_tables")
    # Both converge to END
    workflow.add_edge("distribute_images", END)
    workflow.add_edge("distribute_tables", END)
    
    return workflow.compile()


# Main function for testing
def main():
    """Test the multimodal workflow"""
    print("=" * 60)
    print("Testing Multimodal Workflow")
    print("=" * 60)
    
    # Create workflow
    workflow = create_multimodal_workflow()
    
    # Run workflow with initial state
    initial_state = {
        "lecture_id": "lec_6895e38a",
        "used_images": set(),
        "used_tables": set()
    }
    
    print(f"\nStarting workflow for lecture: {initial_state['lecture_id']}\n")
    
    try:
        # Execute workflow
        result = workflow.invoke(initial_state)
        
        # Display final results
        print("\n" + "=" * 60)
        print("Workflow completed successfully!")
        print("=" * 60)
        
        print(f"\nFinal State Summary:")
        print(f"  Lecture ID: {result['lecture_id']}")
        print(f"  Total Slides: {result['lecture_dict']['metadata']['total_slides']}")
        print(f"  Visualization Queries: {len(result['need_visualization'])}")
        print(f"  Tables: {result['aggregated_media']['total_tables']}")
        print(f"  Images: {result['aggregated_media']['total_images']}")
        print(f"  Distributed Images: {len(result.get('image_distributions', []))}")
        print(f"  Distributed Tables: {len(result.get('table_distributions', []))}")
        
        # Show sample visualization queries
        if result['need_visualization']:
            print(f"\nSample Visualization Queries:")
            for item in result['need_visualization'][:5]:
                print(f"  - Slide {item['slide_number']}: {item['query']}")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
