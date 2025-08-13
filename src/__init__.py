"""
Academic Research Assistant - Core Package

A comprehensive AI-powered multi-agent system for academic research.
"""

__version__ = "2.1.0"
__author__ = "Academic Research Assistant Team"
__description__ = "AI-powered multi-agent system for academic research automation"

# Import main components for easy access
from .agents import *
from .crew import *
from .storage import *
from .tools import *
from .utils import *

__all__ = [
    "__version__",
    "__author__",
    "__description__",
]
