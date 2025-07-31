"""
WhatsApp Conversational Scheduling Agent.

A PydanticAI-based agent for handling appointment scheduling through WhatsApp.
"""

from .agent import scheduling_agent, chat_with_scheduler, chat_with_scheduler_sync
from .dependencies import create_scheduling_dependencies, SchedulingDependencies
from .settings import settings
from .providers import get_llm_model, get_model_info

__version__ = "1.0.0"
__all__ = [
    "scheduling_agent",
    "chat_with_scheduler", 
    "chat_with_scheduler_sync",
    "create_scheduling_dependencies",
    "SchedulingDependencies",
    "settings",
    "get_llm_model",
    "get_model_info"
]