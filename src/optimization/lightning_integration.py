try:
    import agentlightning as agl
    AGENT_LIGHTNING_AVAILABLE = True
except ImportError:
    AGENT_LIGHTNING_AVAILABLE = False
    agl = None

from typing import Optional, Dict, Any
from src.optimization.lightning_setup import lightning_setup

class LightningIntegration:
    def __init__(self):
        self.enabled = lightning_setup.is_available()
    
    def emit_prompt(self, prompt: str, model: str, metadata: Optional[Dict[str, Any]] = None):
        if not self.enabled or not agl:
            return
        
        try:
            if hasattr(agl, 'emit_prompt'):
                agl.emit_prompt(
                    prompt=prompt,
                    model=model,
                    metadata=metadata or {}
                )
        except Exception as e:
            print(f"Agent Lightning emit_prompt error: {e}")
    
    def emit_tool_call(self, tool_name: str, args: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        if not self.enabled or not agl:
            return
        
        try:
            if hasattr(agl, 'emit_tool_call'):
                agl.emit_tool_call(
                    tool_name=tool_name,
                    args=args,
                    metadata=metadata or {}
                )
        except Exception as e:
            print(f"Agent Lightning emit_tool_call error: {e}")
    
    def emit_reward(self, reward: float, task_id: str, metadata: Optional[Dict[str, Any]] = None):
        if not self.enabled or not agl:
            return
        
        try:
            if hasattr(agl, 'emit_reward'):
                agl.emit_reward(reward=reward)
        except Exception as e:
            print(f"Agent Lightning emit_reward error: {e}")

lightning_integration = LightningIntegration()

