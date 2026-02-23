import llm_extension 
from openai import OpenAI
from src.utils.config import config

class TableFilter:
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    def should_visualize_table(
        self, 
        table_markdown: str
    ) -> str:
        try:
            prompt = f"""Bạn là một data analyst giàu kinh nghiệm.

                        Xem xét bảng dữ liệu sau và đánh giá xem bảng này có NÊN được visualize (vẽ biểu đồ) hay không.

                        Tiêu chí đánh giá:
                        - Có metric định lượng (numeric) không?
                        - Có dimension để so sánh / phân nhóm không?
                        - Có yếu tố thời gian hoặc phân phối không?
                        - Visualize có khả năng tạo insight hay chỉ là nhiễu?

                        Bảng dữ liệu:
                        {table_markdown}

                        Trả lời chỉ bằng một từ: "Yes" hoặc "No"."""

            response = self.client.chat.completions.create(
                model=config.TABLE_VIZ_MODEL,
                messages=[
                    {"role": "system", "content": "Bạn là một data analyst chuyên nghiệp. Trả lời ngắn gọn và chính xác."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=10
            )
            
            answer = response.choices[0].message.content.strip()
            if 'yes' in answer.lower():
                return 'Yes'
            else:
                return 'No'
                
        except Exception as e:
            print(f"Warning: LLM evaluation failed for table visualization: {e}")
            return 'No'

