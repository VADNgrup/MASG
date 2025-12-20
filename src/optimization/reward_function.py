from typing import Dict, Any
from src.optimization.lightning_integration import lightning_integration

def compute_and_emit_reward(
    rubric_scores: Dict[str, Any],
    coverage_metrics: Dict[str, Any],
    task_id: str
) -> float:
    faithfulness = rubric_scores.get("faithfulness", {}).get("score", 0) if isinstance(rubric_scores.get("faithfulness"), dict) else 0
    pedagogical = rubric_scores.get("pedagogical_flow", {}).get("score", 0) if isinstance(rubric_scores.get("pedagogical_flow"), dict) else 0
    visual = rubric_scores.get("visual_alignment", {}).get("score", 0) if isinstance(rubric_scores.get("visual_alignment"), dict) else 0
    coverage = coverage_metrics.get("coverage_percent", 0)
    
    if isinstance(faithfulness, dict):
        faithfulness = faithfulness.get("score", 0)
    if isinstance(pedagogical, dict):
        pedagogical = pedagogical.get("score", 0)
    if isinstance(visual, dict):
        visual = visual.get("score", 0)
    
    faithfulness = float(faithfulness) if faithfulness else 0
    pedagogical = float(pedagogical) if pedagogical else 0
    visual = float(visual) if visual else 0
    coverage = float(coverage) if coverage else 0
    
    reward = (faithfulness * 0.4 + pedagogical * 0.35 + visual * 0.25) * 0.7 + coverage * 0.3
    normalized_reward = reward / 100.0
    
    if normalized_reward > 1.0:
        normalized_reward = 1.0
    if normalized_reward < 0.0:
        normalized_reward = 0.0
    
    lightning_integration.emit_reward(
        reward=normalized_reward,
        task_id=task_id,
        metadata={
            "faithfulness": faithfulness,
            "pedagogical": pedagogical,
            "visual": visual,
            "coverage": coverage,
            "raw_reward": reward
        }
    )
    
    return normalized_reward

