"""
Logging configuration for the LLM Swarm system.
"""

import logging
import sys
from pathlib import Path
from rich.logging import RichHandler
from rich.console import Console


def setup_logging(level: int = logging.INFO, log_file: str = None) -> None:
    """
    Setup logging configuration with rich formatting.
    
    Args:
        level: Logging level (default: INFO)
        log_file: Optional file to write logs to
    """
    # Create console for rich output
    console = Console()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create rich handler for console output
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True
    )
    rich_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(message)s",
        datefmt="[%X]"
    )
    rich_handler.setFormatter(formatter)
    
    # Add console handler
    root_logger.addHandler(rich_handler)
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        
        file_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)