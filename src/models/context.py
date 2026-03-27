from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from .asset import AssetCollection

class TextContent(BaseModel):
    markdown: str
    page_count: int

class TableData(BaseModel):
    table_id: str
    markdown: str
    table_caption: str
    should_visualize: str
    chart_path: Optional[str] = None  
    chart_type: Optional[str] = None  
    image_table_path: Optional[str] = None

class ProcessingMetadata(BaseModel):
    total_images: int
    total_tables: int
    processing_time_seconds: float

class DocumentContext(BaseModel):
    document_id: str
    source_file: str
    processed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    text_content: TextContent
    tables: List[TableData] = Field(default_factory=list)
    assets: AssetCollection = Field(default_factory=AssetCollection)
    metadata: ProcessingMetadata

