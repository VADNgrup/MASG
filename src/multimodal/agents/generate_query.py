import llm_extension
from langchain_openai import ChatOpenAI
from typing import List, Dict, Optional
import json
from pathlib import Path
from src.utils.parse_llm_response import parse_json_response


class GenerateQueryAgent:
    def __init__(self, model: str = "qwen3-35b"):
        self.llm = ChatOpenAI(model=model, temperature=0.4, max_tokens=16000)
        self.model = model
    
    def generate_visualization_queries(
        self, 
        lecture_json_path: Optional[str] = None,
        lecture_dict: Optional[Dict[str, any]] = None
    ) -> List[Dict[str, any]]:
        """
        Read a lecture JSON file or dict and generate visualization queries for slides that need them.
        
        Args:
            lecture_json_path: Optional path to the lecture JSON file
            lecture_dict: Optional lecture dictionary (already loaded from JSON)
            
        Returns:
            List of dictionaries with 'slide_number' and 'query' for visualization needs
            
        Example:
            [
                {"slide_number": 1, "query": "CNN architecture diagram with convolutional layers"},
                {"slide_number": 3, "query": "ImageNet dataset statistics bar chart"}
            ]
        """
        # Load lecture data from file or use provided dict
        if lecture_dict is None:
            if lecture_json_path is None:
                raise ValueError("Either lecture_json_path or lecture_dict must be provided")
            with open(lecture_json_path, 'r', encoding='utf-8') as f:
                lecture_data = json.load(f)
        else:
            lecture_data = lecture_dict
        
        slides = lecture_data.get('slides', [])
        
        if not slides:
            return []
        
        # Generate visualization queries using LLM
        need_visualization = self._analyze_slides_for_visualization(slides)
        
        return need_visualization
    
    def _analyze_slides_for_visualization(self, slides: List[Dict]) -> List[Dict[str, any]]:
        """
        Analyze all slides and determine which ones need visualization.
        
        Args:
            slides: List of slide dictionaries from the lecture JSON
            
        Returns:
            List of visualization query objects
        """
        system_prompt = """
You are an expert educational content analyzer specializing in identifying slides that would benefit from visual aids.

Your task is to analyze lecture slides and determine which ones would be significantly enhanced by images, diagrams, charts, or tables.

IDENTIFICATION CRITERIA:
- Slides describing architectures, systems, or structures → need diagrams/images
- Slides with numerical data, comparisons, or statistics → need charts/tables
- Slides explaining processes, workflows, or algorithms → need flowcharts/diagrams
- Slides discussing visual concepts (e.g., image processing, UI design) → need example images
- Slides with mathematical formulas that could be visualized → need graphs/diagrams

QUERY GENERATION RULES:
- Queries should be specific and descriptive
- Include key technical terms from the slide content
- Specify the type of visualization (diagram, chart, table, image, graph)
- Keep queries concise but informative (10-20 words)

IMPORTANT CONSTRAINTS:
- NOT every slide needs visualization
- Slides introducing a new concept for the first time → benefit from illustrative images
- Slides with abstract ideas → benefit from concrete visual examples
- The number of visualizations should be ≤ total number of slides
- Prioritize slides where visuals are most impactful

Return ONLY valid JSON array:
[
  {"slide_number": 1, "query": "specific query for image/chart/diagram"},
  {"slide_number": 3, "query": "another specific query"}
]

If no slides need visualization, return an empty array: []

Do NOT include slide_content in the JSON — that field is added programmatically.
"""
        
        # Prepare slides content for analysis
        slides_summary = self._format_slides_for_analysis(slides)
        
        user_prompt = f"""
Analyze the following lecture slides and identify which ones need visualization.

SLIDES:
{slides_summary}

Generate visualization queries ONLY for slides that would significantly benefit from visual aids.
Remember: len(need_visualization) ≤ len(slides)

Return the JSON array of visualization needs:
"""
        
        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        # Parse the response
        need_visualization = self._parse_json_response(response.content)
        
        # Validate the response
        if not isinstance(need_visualization, list):
            return []
        
        # Build a lookup map: slide_number -> slide_content string
        slide_content_map: Dict[int, str] = {}
        for slide in slides:
            slide_num = slide.get('slide_number')
            title = slide.get('slide_title', '')
            content = slide.get('content', [])
            if isinstance(content, list):
                content_str = ' '.join(content)
            else:
                content_str = str(content)
            slide_content_map[slide_num] = f"{title}. {content_str}".strip()

        # Filter and validate each item
        validated_results = []
        total_slides = len(slides)
        
        for item in need_visualization:
            if isinstance(item, dict) and 'slide_number' in item and 'query' in item:
                slide_num = item['slide_number']
                # Validate slide number is within range
                if 1 <= slide_num <= total_slides:
                    validated_results.append({
                        'slide_number': slide_num,
                        'query': str(item['query']).strip(),
                        'slide_content': slide_content_map.get(slide_num, '')
                    })
        
        return validated_results
    
    def _format_slides_for_analysis(self, slides: List[Dict]) -> str:
        """
        Format slides into a readable summary for LLM analysis.
        
        Args:
            slides: List of slide dictionaries
            
        Returns:
            Formatted string representation of slides
        """
        formatted = []
        
        for slide in slides:
            slide_num = slide.get('slide_number', '?')
            title = slide.get('slide_title', 'Untitled')
            content = slide.get('content', [])
            
            # Format content as bullet points
            if isinstance(content, list):
                content_str = '\n  - ' + '\n  - '.join(content[:3])  # Limit to first 3 points for brevity
                if len(content) > 3:
                    content_str += f'\n  ... ({len(content) - 3} more points)'
            else:
                content_str = str(content)[:200]  # Limit string content
            
            formatted.append(f"Slide {slide_num}: {title}{content_str}")
        
        return '\n\n'.join(formatted)
    
    def _parse_json_response(self, response_content: str) -> List[Dict]:
        return parse_json_response(response_content, self.llm.invoke)
    
    def save_visualization_queries(
        self, 
        lecture_json_path: str, 
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate visualization queries and save them to a JSON file.
        
        Args:
            lecture_json_path: Path to the lecture JSON file
            output_path: Optional path for output file. If None, saves next to input file
            
        Returns:
            Path to the saved output file
        """
        need_visualization = self.generate_visualization_queries(lecture_json_path)
        
        # Determine output path
        if output_path is None:
            input_path = Path(lecture_json_path)
            output_path = input_path.parent / f"{input_path.stem}_visualization_queries.json"
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(need_visualization, f, indent=2, ensure_ascii=False)
        
        return str(output_path)


# Example usage
if __name__ == "__main__":
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
