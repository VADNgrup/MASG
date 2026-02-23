import llm_extension
from langchain_openai import ChatOpenAI
from typing import List, Dict, Optional, Any, Set
import json
from pathlib import Path
from src.utils.config import config


class TableChartDistribution:
    def __init__(self, model: str = "gpt-5"):
        self.llm = ChatOpenAI(model=model, temperature=0.3, max_tokens=2000)
        self.model = model
    
    def distribute_tables(
        self,
        lecture_id: str,
        lecture_dict: Dict[str, Any],
        aggregated_media: Dict[str, Any],
        used_tables: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Distribute tables to slides based on content relevance using LLM scoring.
        
        Args:
            lecture_id: Lecture ID for saving results
            lecture_dict: Lecture dictionary with slides
            aggregated_media: Aggregated media containing tables
            used_tables: Set of already used table IDs
            
        Returns:
            List of table distributions with slide_number, table_data, and optional chart_path
        """
        distributions = []
        
        # Get tables from aggregated media
        tables = aggregated_media.get('tables', [])
        slides = lecture_dict.get('slides', [])
        
        if not tables or not slides:
            print("No tables or slides found")
            return distributions
        
        print(f"\nDistributing {len(tables)} tables to {len(slides)} slides...")
        
        for table_idx, table in enumerate(tables):
            table_id = f"table_{table_idx}"
            
            # Skip if already used
            if table_id in used_tables:
                print(f"  Table {table_idx} already used, skipping...")
                continue
            
            table_markdown = table.get('markdown', '')
            table_caption = table.get('table_caption', '')
            
            if not table_markdown:
                continue
            
            print(f"\n  Processing table {table_idx}: {table_caption[:50]}...")
            
            # Score table against all slides
            best_slide = self._find_best_slide_for_table(
                table_markdown=table_markdown,
                table_caption=table_caption,
                slides=slides
            )
            
            if best_slide:
                distributions.append({
                    'slide_number': best_slide['slide_number'],
                    'table_data': table_markdown,
                    'table_caption': table_caption,
                    'chart_path': table.get('chart_path', None),
                    'relevance_score': best_slide['score']
                })
                
                used_tables.add(table_id)
                print(f"    → Assigned to slide {best_slide['slide_number']} (score: {best_slide['score']:.2f})")
            else:
                print(f"    → No suitable slide found")
        
        # Save results
        output_path = Path(f"data/lectures/{lecture_id}_table_distribution.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(distributions, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved table distributions to: {output_path}")
        
        return distributions
    
    def _find_best_slide_for_table(
        self,
        table_markdown: str,
        table_caption: str,
        slides: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best matching slide for a table using LLM scoring.
        
        Args:
            table_markdown: Table content in markdown format
            table_caption: Table caption/title
            slides: List of slides with content
            
        Returns:
            Dict with slide_number and score, or None if no good match
        """
        # Prepare slides summary for LLM
        slides_summary = []
        for slide in slides:
            slide_num = slide.get('slide_number', 0)
            slide_title = slide.get('title', 'Untitled')
            slide_content = slide.get('content', '')
            
            slides_summary.append({
                'slide_number': slide_num,
                'title': slide_title,
                'content': slide_content[:500]  # Limit content length
            })
        
        # Create prompt for LLM
        prompt = f"""You are analyzing a table from an educational document and need to determine which slide it best supports.

Table Caption: {table_caption}

Table Content (first 500 chars):
{table_markdown[:500]}

Available Slides:
{json.dumps(slides_summary, indent=2, ensure_ascii=False)}

Task: For each slide, rate how relevant and supportive this table is to the slide's content on a scale of 0-10, where:
- 0-3: Not relevant or unrelated
- 4-6: Somewhat related, provides context
- 7-8: Directly relevant, supports the content
- 9-10: Highly relevant, essential for understanding the slide

Return ONLY a JSON array with scores for each slide:
[
  {{"slide_number": 1, "score": 5, "reason": "brief explanation"}},
  {{"slide_number": 2, "score": 8, "reason": "brief explanation"}}
]

Return ONLY valid JSON, no additional text."""

        try:
            # Call LLM
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Parse JSON response
            # Remove markdown code blocks if present
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            
            scores = json.loads(content)
            
            # Find the slide with highest score
            if not scores:
                return None
            
            best_match = max(scores, key=lambda x: x.get('score', 0))
            
            # Only return if score is above threshold (6.0)
            if best_match.get('score', 0) >= 6.0:
                return {
                    'slide_number': best_match['slide_number'],
                    'score': best_match['score'],
                    'reason': best_match.get('reason', '')
                }
            
            return None
            
        except json.JSONDecodeError as e:
            print(f"    Error parsing LLM response: {e}")
            print(f"    Response: {content[:200]}...")
            return None
        except Exception as e:
            print(f"    Error scoring table: {e}")
            return None


# Main function for testing
def main():
    """Test the TableChartDistribution class"""
    print("=" * 60)
    print("Testing TableChartDistribution")
    print("=" * 60)
    
    # Initialize the distributor
    distributor = TableChartDistribution()
    
    # Sample data
    lecture_id = "lec_607fe87f"
    
    # Load lecture data
    with open(f"data/lectures/{lecture_id}.json", 'r', encoding='utf-8') as f:
        lecture_dict = json.load(f)
    
    # Load aggregated media
    source_id = lecture_dict['metadata']['source_document_id']
    with open(f"data/media/{source_id}_media.json", 'r', encoding='utf-8') as f:
        aggregated_media = json.load(f)
    
    # Track used tables
    used_tables = set()

    print(f"Total slides: {len(lecture_dict['slides'])}")
    print(f"Total tables: {len(aggregated_media['tables'])}")
    
    # Distribute tables
    distributions = distributor.distribute_tables(
        lecture_id=lecture_id,
        lecture_dict=lecture_dict,
        aggregated_media=aggregated_media,
        used_tables=used_tables
    )
    
    # Display results
    print("\n" + "=" * 60)
    print("Distribution Results")
    print("=" * 60)
    
    for dist in distributions:
        print(f"\nSlide {dist['slide_number']}:")
        print(f"  Caption: {dist['table_caption'][:80]}...")
        print(f"  Score: {dist['relevance_score']:.2f}")
        if dist.get('chart_path'):
            print(f"  Chart: {dist['chart_path']}")
    
    print(f"\n✓ Distributed {len(distributions)} tables")


if __name__ == "__main__":
    main()