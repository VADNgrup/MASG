import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY")
    
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    RAW_DIR = DATA_DIR / "raw"
    ASSETS_DIR = DATA_DIR / "assets"
    CONTEXT_DIR = DATA_DIR / "context"
    LECTURES_DIR = DATA_DIR / "lectures"
    GENERATED_IMAGES_DIR = ASSETS_DIR / "generated"
    
    DEFAULT_IMAGE_FORMAT = "png"
    MAX_IMAGE_SIZE = (2048, 2048)
    
    VISION_MODEL = "gpt-4o"
    VISION_MAX_TOKENS = 500
    VISION_TEMPERATURE = 0.3
    
    WORKFLOW_MAX_ITERATIONS = 3
    SEMANTIC_MATCH_THRESHOLD_WEAK = 0.4
    SEMANTIC_MATCH_THRESHOLD_STRONG = 0.6
    IMAGE_QUALITY_THRESHOLD = 0.5
    
    FAITHFULNESS_WEIGHT = 0.4
    PEDAGOGICAL_WEIGHT = 0.35
    VISUAL_WEIGHT = 0.25
    REVIEW_PASS_THRESHOLD = 75
    
    PLANNER_MODEL = "gpt-4o"
    WRITER_MODEL = "gpt-4o"
    REVIEWER_MODEL = "gpt-4o"
    REFINER_MODEL = "gpt-4o"
    CLASSIFIER_MODEL = "gpt-4o-mini"
    
    MIN_COVERAGE_PERCENT = 70
    
    IMAGE_GEN_PROVIDER = "dalle3"
    IMAGE_GEN_SIZE = "1792x1024"
    
    @classmethod
    def validate(cls):
        if not cls.LLAMA_CLOUD_API_KEY:
            raise ValueError("LLAMA_CLOUD_API_KEY not found in environment")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        cls.RAW_DIR.mkdir(parents=True, exist_ok=True)
        cls.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        cls.CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
        cls.LECTURES_DIR.mkdir(parents=True, exist_ok=True)
        cls.GENERATED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

config = Config()

