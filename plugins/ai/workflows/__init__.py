# FILE: plugins/ai/workflows/__init__.py
"""
AI Workflows for Probaah
Complete automated workflows combining multiple tools
"""

from .gas_substitution import GasSubstitutionWorkflow
from .ai_enhanced_analysis import AIEnhancedAnalysis

__all__ = ['GasSubstitutionWorkflow', 'AIEnhancedAnalysis']