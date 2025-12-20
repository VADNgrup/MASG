from pathlib import Path
from typing import Literal, Optional

class LightningConfig:
    def __init__(
        self,
        optimization_algorithm: Literal["rl", "prompt_optimization"] = "prompt_optimization",
        training_frequency: int = 10,
        storage_path: Optional[Path] = None
    ):
        self.optimization_algorithm = optimization_algorithm
        self.training_frequency = training_frequency
        self.storage_path = storage_path or Path("data/optimization")
        
        self.reward_weights = {
            "faithfulness": 0.4,
            "pedagogical": 0.35,
            "visual": 0.25,
            "coverage": 0.3
        }
    
    def to_dict(self):
        return {
            "optimization_algorithm": self.optimization_algorithm,
            "training_frequency": self.training_frequency,
            "storage_path": str(self.storage_path),
            "reward_weights": self.reward_weights
        }

default_lightning_config = LightningConfig()

