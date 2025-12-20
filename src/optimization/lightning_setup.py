try:
    import agentlightning as agl
    AGENT_LIGHTNING_AVAILABLE = True
except ImportError:
    AGENT_LIGHTNING_AVAILABLE = False
    agl = None

from typing import Optional
from pathlib import Path

class LightningSetup:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("data/optimization")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.available = AGENT_LIGHTNING_AVAILABLE
        
    def is_available(self):
        return self.available

lightning_setup = LightningSetup()

