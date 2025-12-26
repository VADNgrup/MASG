try:
    import agentlightning as agl
    AGENT_LIGHTNING_AVAILABLE = True
except ImportError:
    AGENT_LIGHTNING_AVAILABLE = False
    agl = None

from typing import Optional
from pathlib import Path
from datetime import datetime
from agentlightning.instrumentation import instrument_all

class LightningSetup:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("data/optimization")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.available = AGENT_LIGHTNING_AVAILABLE
        self.tracer = None
        self.store = None
        
        if self.available and agl:
            try:
                instrument_all()
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
    
    def save_traces(self, output_path: Optional[Path] = None) -> Optional[Path]:
        if not self.available or not self.tracer or not self.store:
            return None
        
        try:
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.storage_path / f"traces_{timestamp}.json"
            
            traces = self.tracer.get_last_trace()
            
            if not traces:
                return None
            
            import json
            
            trace_data = {
                "timestamp": datetime.now().isoformat(),
                "trace_count": len(traces),
                "traces": [
                    {
                        "name": getattr(span, "name", "unknown"),
                        "attributes": dict(getattr(span, "attributes", {}) or {}),
                        "start_time": getattr(span, "start_time", None),
                        "end_time": getattr(span, "end_time", None),
                        "status": str(getattr(span, "status", {}).status_code) if hasattr(getattr(span, "status", None), "status_code") else None
                    }
                    for span in traces
                ]
            }
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(trace_data, f, indent=2, ensure_ascii=False, default=str)
            
            return output_path
        except Exception as e:
            print(f"Failed to save traces: {e}")
            return None

lightning_setup = LightningSetup()

