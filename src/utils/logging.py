import logging
import os
from pathlib import Path
from rich.logging import RichHandler
from rich.console import Console

def setup_logging(log_level: str = None):
    """Setup logging with Rich formatting"""
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            RichHandler(rich_tracebacks=True, console=Console(stderr=True)),
            logging.FileHandler('logs/research_assistant.log')
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()