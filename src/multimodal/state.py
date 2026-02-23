from typing import TypedDict, List, Dict, Any, Optional, Set


class MultimodalState(TypedDict):
    """State for multimodal processing pipeline"""
    lecture_id: str
    lecture_dict: Dict[str, Any]  # Loaded from data/lectures/{lecture_id}.json
    need_visualization: List[Dict[str, Any]]  # Output from GenerateQueryAgent
    aggregated_media: Dict[str, Any]  # Output from ImageAggregation
    used_tables: Set[str]  # Check used table
    used_images: Set[str]  # Check used image
    image_distributions: List[Dict[str, Any]]  # Output from ImageDistribution
    table_distributions: List[Dict[str, Any]]  # Output from TableChartDistribution


