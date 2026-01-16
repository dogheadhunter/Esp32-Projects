"""
Logging Configuration for Wiki-to-ChromaDB Pipeline

Structured logging with context support.
"""

import logging
import sys
from typing import Optional
from pathlib import Path
from datetime import datetime


class PipelineLogger:
    """Centralized logging for the pipeline"""
    
    _instance: Optional['PipelineLogger'] = None
    _loggers: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def setup(cls, level: str = "INFO", log_file: Optional[str] = None) -> None:
        """
        Setup logging configuration.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR)
            log_file: Optional file path for logging
        """
        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Setup root logger
        root_logger = logging.getLogger('wiki_to_chromadb')
        root_logger.setLevel(getattr(logging, level.upper()))
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use unbuffered file handler for immediate writes
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_handler.setFormatter(formatter)
            # Flush after every log entry to ensure data persists even on crash/interrupt
            file_handler.flush = lambda: file_handler.stream.flush()
            root_logger.addHandler(file_handler)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger for a specific module.
        
        Args:
            name: Logger name (usually __name__)
        
        Returns:
            Logger instance
        """
        if name not in cls._loggers:
            logger = logging.getLogger(f'wiki_to_chromadb.{name}')
            cls._loggers[name] = logger
        return cls._loggers[name]


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger"""
    return PipelineLogger.get_logger(name)
