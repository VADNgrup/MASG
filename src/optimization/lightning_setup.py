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
        self.tracer = None
        self.store = None
        
        if self.available and agl:
            try:
                self.tracer = agl.OtelTracer()
                self.store = agl.InMemoryLightningStore()
                self.tracer.init_worker(worker_id=0)
            except Exception as e:
                print(f"Agent Lightning setup warning: {e}")
                self.available = False
        
    def is_available(self):
        return self.available and self.tracer is not None
    
    def get_tracer(self):
        return self.tracer
    
    def get_store(self):
        return self.store

lightning_setup = LightningSetup()

