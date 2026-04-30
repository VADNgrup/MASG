import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME')
    LLM_BASE_URL = os.getenv('LLM_BASE_URL')
    TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
    VLM_BASE_URL = os.getenv('VLM_BASE_URL')
    VLM_API_KEY = os.getenv('VLM_API_KEY')
    VLM_MODEL_NAME = os.getenv('VLM_MODEL_NAME')
    EVAL_LANGUAGE_MODEL = os.getenv('EVAL_LANGUAGE_MODEL')
    EVAL_VISION_MODEL = os.getenv('EVAL_VISION_MODEL')
    EVAL_BASE_URL = os.getenv('EVAL_BASE_URL')
    EVAL_API_KEY = os.getenv('EVAL_API_KEY')
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / 'data'
    OUTPUT_DIR = BASE_DIR / 'output'
    RAW_DIR = DATA_DIR / 'raw'
    ASSETS_DIR = DATA_DIR / 'assets'
    CONTEXT_DIR = DATA_DIR / 'context'
    LECTURES_DIR = DATA_DIR / 'lectures'
    THEME_PATH = DATA_DIR / 'theme' / 'theme.json'
    VISION_MAX_TOKENS = 2000
    VISION_TEMPERATURE = 0.3
    DEFAULT_IMAGE_FORMAT = 'png'
    MAX_IMAGE_SIZE = (2048, 2048)
    MIN_WH_RATIO_IMAGE_DOWNLOAD = 0.556
    CRITICAL_CONFIDENCE_THRESHOLD = 0.95
    MAJOR_CONFIDENCE_THRESHOLD = 0.92
    MINOR_CONFIDENCE_THRESHOLD = 0.92
    @classmethod
    def get_log_path(cls):
        sanitized_model = (cls.LLM_MODEL_NAME or 'default').replace('/', '_').replace(':', '_')
        log_dir = cls.BASE_DIR / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / f'llm_calls_{sanitized_model}.jsonl'

    @classmethod
    def validate(cls):
        if not cls.OPENAI_API_KEY:
            raise ValueError('OPENAI_API_KEY not found in environment')
        cls.RAW_DIR.mkdir(parents=True, exist_ok=True)
        cls.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        cls.CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
        cls.LECTURES_DIR.mkdir(parents=True, exist_ok=True)
config = Config()