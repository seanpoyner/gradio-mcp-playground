"""Core components for the GMP Agent"""

from .agent import GMPAgent
from .server_builder import ServerBuilder
from .registry import EnhancedRegistry
from .knowledge import KnowledgeBase
from .agent_runner import AgentRunner, get_agent_runner

# Apply fixes on import
try:
    from .event_handlers_fix import patch_gradio_components
    from .unified_dashboard_fix import fix_unified_dashboard_integration
    
    # Apply patches
    patch_gradio_components()
    fix_unified_dashboard_integration()
except ImportError:
    pass

try:
    from .agent_builder import AgentBuilder
    __all__ = ["GMPAgent", "ServerBuilder", "EnhancedRegistry", "KnowledgeBase", "AgentRunner", "get_agent_runner", "AgentBuilder"]
except ImportError:
    __all__ = ["GMPAgent", "ServerBuilder", "EnhancedRegistry", "KnowledgeBase", "AgentRunner", "get_agent_runner"]