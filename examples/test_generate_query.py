"""
Example script demonstrating how to use GenerateQueryAgent
to generate visualization queries from lecture JSON files.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.multimodal.agents.generate_query import GenerateQueryAgent


def main():
    # Initialize the agent
    agent = GenerateQueryAgent(model="gpt-4o-mini")
    
    # Path to the lecture JSON file
    lecture_path = "data/lectures/lec_607fe87f.json"
    
    print(f"Analyzing lecture: {lecture_path}")
    print("-" * 60)
    
    # Generate visualization queries
    visualization_queries = agent.generate_visualization_queries(lecture_path)
    
    # Display results
    print(f"\nFound {len(visualization_queries)} slides that need visualization:\n")
    
    for item in visualization_queries:
        slide_num = item['slide_number']
        query = item['query']
        print(f"Slide {slide_num}:")
        print(f"  Query: {query}\n")
    
    # Save to file
    output_path = agent.save_visualization_queries(lecture_path)
    print(f"Visualization queries saved to: {output_path}")


if __name__ == "__main__":
    main()
