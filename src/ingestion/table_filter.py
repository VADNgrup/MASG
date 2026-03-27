import llm_extension 
from openai import OpenAI
from src.utils.config import config
from src.utils.parse_llm_response import clear_think

class TableFilter:
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    def should_visualize_table(
        self, 
        table_markdown: str,
        table_caption: str
    ) -> str:
        try:
            prompt = f"""
                        Review the following data table and assess whether it SHOULD be visualized (i.e., turned into a chart).

                        Evaluation criteria:
                        - Does it contain quantitative (numeric) metrics?
                        - Does it have dimensions for comparison or grouping?
                        - Does it have a time-series or distributional element?
                        - Would a visualization generate meaningful insight, or would it just add noise?

                        Data table:
                        {table_markdown}
                        Table caption:
                        {table_caption}

                        Answer with exactly one word: "Yes" or "No"."""

            response = self.client.chat.completions.create(
                model=config.TABLE_VIZ_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional data analyst. Answer concisely and accurately."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=10
            )
            
            answer = clear_think(response.choices[0].message.content)
            if 'yes' in answer.lower():
                return 'Yes'
            else:
                return 'No'
                
        except Exception as e:
            print(f"Warning: LLM evaluation failed for table visualization: {e}")
            return 'No'

