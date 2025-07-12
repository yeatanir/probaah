# FILE: plugins/ai/__init__.py
"""
AI-Powered Workflow Automation for Probaah
Modern interfaces to molecular tools with natural language processing
"""

__version__ = "1.0.0"
__author__ = "Anirban Pal"

from .orchestrator import ProbaahAIOrchestrator
from .packmol_wrapper import ProbaahPackmol
from .visual_validation import VIAMDIntegration
from .mdcrow_agent import MDCrowAgent

__all__ = [
    'ProbaahAIOrchestrator',
    'ProbaahPackmol', 
    'VIAMDIntegration',
    'MDCrowAgent'
]