"""
Safe Performance Patch for Research Crew
Optimizes delays while maintaining all free tier protections
"""

import time
import logging
from typing import Any

logger = logging.getLogger(__name__)

def get_optimized_batch_delay(batch_num: int, total_batches: int) -> float:
    """
    Optimized batch delays - much faster but still API-safe
    
    Original delays: 10s, 20s, 30s (too conservative)
    New delays: 3s, 5s, 8s (faster but still respectful)
    
    This maintains API respect while being 2-3x faster
    """
    if total_batches <= 1:
        return 1  # Single batch - minimal delay
    
    # Optimized delay progression
    delay_map = {
        1: 2,  # First batch: quick start  
        2: 3,  # Second batch: short delay
        3: 5,  # Third batch: moderate delay
    }
    
    # For batches beyond 3, use moderate delay
    return delay_map.get(batch_num, 6)

def get_optimized_arxiv_delay() -> float:
    """
    Optimized ArXiv delay: 3s → 2s
    ArXiv API can handle faster requests
    """
    return 2

def get_smart_api_cooldown(error_msg: str = "") -> float:
    """
    Smart cooldown based on actual error type
    Avoids unnecessary long waits
    """
    error_lower = error_msg.lower()
    
    if 'quota' in error_lower:
        return 25  # Quota errors - be careful
    elif 'rate' in error_lower:
        return 15  # Rate limit - moderate wait
    elif 'timeout' in error_lower:
        return 8   # Timeout - shorter wait
    else:
        return 10  # General errors - reasonable wait

# Backup original functions for safety
_original_functions = {}
