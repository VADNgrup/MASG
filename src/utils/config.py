import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL")
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")
    VLM_BASE_URL = os.getenv("VLM_BASE_URL")
    VLM_API_KEY = os.getenv("VLM_API_KEY")
    VLM_MODEL_NAME = os.getenv("VLM_MODEL_NAME")

    EVAL_LANGUAGE_MODEL = os.getenv("EVAL_LANGUAGE_MODEL")
    EVAL_VISION_MODEL = os.getenv("EVAL_VISION_MODEL")
    EVAL_BASE_URL = os.getenv("EVAL_BASE_URL")
    EVAL_API_KEY = os.getenv("EVAL_API_KEY")
    
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    RAW_DIR = DATA_DIR / "raw"
    ASSETS_DIR = DATA_DIR / "assets"
    CONTEXT_DIR = DATA_DIR / "context"
    LECTURES_DIR = DATA_DIR / "lectures"
    GENERATED_IMAGES_DIR = ASSETS_DIR / "generated"
    THEME_PATH = DATA_DIR / "theme" / "theme.json"
    
    CONFIDENCE_FEEDBACK_THRESHOLD = 0.3

    DEFAULT_IMAGE_FORMAT = "png"
    MAX_IMAGE_SIZE = (2048, 2048)
    
    FEEDBACK_INTERATION_NUMBER = os.getenv("FEEDBACK_INTERATION_NUMBER")
    SEMANTIC_MATCH_THRESHOLD_WEAK = 0.4
    SEMANTIC_MATCH_THRESHOLD_STRONG = 0.6
    IMAGE_QUALITY_THRESHOLD = 0.5
    
    FAITHFULNESS_WEIGHT = 0.4
    PEDAGOGICAL_WEIGHT = 0.35
    VISUAL_WEIGHT = 0.25
    REVIEW_PASS_THRESHOLD = 75
    
    MIN_COVERAGE_PERCENT = 70
    
    @classmethod
    def validate(cls):
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment")
        cls.RAW_DIR.mkdir(parents=True, exist_ok=True)
        cls.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        cls.CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
        cls.LECTURES_DIR.mkdir(parents=True, exist_ok=True)
        cls.GENERATED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

config = Config()

