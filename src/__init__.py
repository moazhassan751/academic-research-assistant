"""
Academic Research Assistant - Optimized Init
"""

# Lazy loading optimization - only import when needed
def get_research_crew():
    from .crew import ResearchCrew
    return ResearchCrew

def get_export_manager():
    from .utils.export_manager import export_manager
    return export_manager

# Core components for immediate use
from .utils.logging import logger

# Note: Other components loaded on-demand for better performance
