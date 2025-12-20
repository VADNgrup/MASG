try:
    import agentlightning as agl
    AGENT_LIGHTNING_AVAILABLE = True
except ImportError:
    AGENT_LIGHTNING_AVAILABLE = False
    agl = None

from typing import Dict, Any, Optional
from pathlib import Path
from src.optimization.lightning_config import LightningConfig
from src.optimization.lightning_setup import lightning_setup

class LightningManager:
    def __init__(self, config: Optional[LightningConfig] = None):
        self.config = config or LightningConfig()
        self.store = None
        self.trainer = None
        self.trace_count = 0
        self.available = AGENT_LIGHTNING_AVAILABLE
        
    def should_train(self) -> bool:
        if not self.available:
            return False
        return self.trace_count > 0 and self.trace_count % self.config.training_frequency == 0
    
    def train(self):
        if not self.available or not agl:
            return
        
        if not self.should_train():
            return
        
        try:
            if hasattr(agl, 'Trainer'):
                if self.trainer is None:
                    if self.config.optimization_algorithm == "rl":
                        self.trainer = agl.Trainer(algorithm="rl")
                    else:
                        self.trainer = agl.Trainer(algorithm="prompt_optimization")
                
                if self.trainer and hasattr(self.trainer, 'train'):
                    self.trainer.train()
        except Exception as e:
            print(f"Agent Lightning training error: {e}")
    
    def get_optimized_prompts(self) -> Dict[str, str]:
        return {}
    
    def increment_trace_count(self):
        self.trace_count += 1
        if self.should_train():
            self.train()

lightning_manager = LightningManager()

