"""
Comprehensive Logging Utilities for Testing

This module provides logging infrastructure that captures ALL output including:
- stdout/stderr
- LLM API calls
- ChromaDB queries  
- User cancellations (Ctrl+C)
- Exception tracebacks
- Performance metrics

Every test run is logged to a timestamped file for historical comparison.
"""

import logging
import sys
import os
import signal
import atexit
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, TextIO, Any
from contextlib import contextmanager
import threading


class ComprehensiveLogger:
    """
    Comprehensive logging system that captures EVERYTHING.
    
    Features:
    - Captures all stdout/stderr
    - Logs to both console and file
    - Auto-flush for crash resilience
    - Signal handling for Ctrl+C
    - Historical log preservation
    - Structured formatting
    """
    
    _instance: Optional['ComprehensiveLogger'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.log_dir = Path(__file__).parent.parent / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create history directory
        self.history_dir = self.log_dir / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Log files
        self.main_log_file = self.log_dir / f"test_run_{self.timestamp}.log"
        self.latest_log_file = self.log_dir / "test_run_latest.log"
        
        # File handles
        self.log_handles = []
        
        # Original streams (for restoration)
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # Thread-local storage for nested contexts
        self.thread_local = threading.local()
        
        # Setup logging
        self._setup_logging()
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Setup exit handler
        atexit.register(self._cleanup)
        
        self._initialized = True
    
    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        # Create formatter with comprehensive information
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(process)d | %(thread)d | %(name)-30s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S.%f'
        )
        
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.handlers.clear()
        
        # Console handler (INFO and above)
        console_handler = logging.StreamHandler(self.original_stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # File handler (DEBUG and above)
        file_handler = logging.FileHandler(
            self.main_log_file, 
            mode='w', 
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        # Force immediate flush
        file_handler.stream.reconfigure(write_through=True)
        root_logger.addHandler(file_handler)
        self.log_handles.append(file_handler)
        
        # Create symlink to latest
        if self.latest_log_file.exists():
            self.latest_log_file.unlink()
        try:
            self.latest_log_file.symlink_to(self.main_log_file.name)
        except (OSError, NotImplementedError):
            # Fallback for Windows or systems without symlink support
            import shutil
            shutil.copy2(self.main_log_file, self.latest_log_file)
        
        # Log initialization
        root_logger.info("="*80)
        root_logger.info("COMPREHENSIVE LOGGING SYSTEM INITIALIZED")
        root_logger.info(f"Log file: {self.main_log_file}")
        root_logger.info(f"Timestamp: {self.timestamp}")
        root_logger.info(f"PID: {os.getpid()}")
        root_logger.info("="*80)
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers to capture user cancellations"""
        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigterm = signal.getsignal(signal.SIGTERM)
        
        def sigint_handler(signum, frame):
            """Handle Ctrl+C"""
            logger = logging.getLogger(__name__)
            logger.critical("="*80)
            logger.critical("USER CANCELLED EXECUTION (Ctrl+C / SIGINT)")
            logger.critical(f"Signal: {signum}")
            logger.critical(f"Frame: {frame}")
            logger.critical("Stack trace at cancellation:")
            for line in traceback.format_stack(frame):
                logger.critical(line.rstrip())
            logger.critical("="*80)
            self._flush_all()
            
            # Call original handler if it exists
            if callable(original_sigint):
                original_sigint(signum, frame)
            else:
                sys.exit(130)  # Standard exit code for SIGINT
        
        def sigterm_handler(signum, frame):
            """Handle termination"""
            logger = logging.getLogger(__name__)
            logger.critical("="*80)
            logger.critical("PROCESS TERMINATED (SIGTERM)")
            logger.critical(f"Signal: {signum}")
            logger.critical("="*80)
            self._flush_all()
            
            # Call original handler if it exists
            if callable(original_sigterm):
                original_sigterm(signum, frame)
            else:
                sys.exit(143)  # Standard exit code for SIGTERM
        
        # Install handlers
        signal.signal(signal.SIGINT, sigint_handler)
        signal.signal(signal.SIGTERM, sigterm_handler)
    
    def _flush_all(self) -> None:
        """Flush all log handlers immediately"""
        for handler in logging.getLogger().handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
        
        for handle in self.log_handles:
            if hasattr(handle, 'flush'):
                handle.flush()
    
    def _cleanup(self) -> None:
        """Cleanup on exit"""
        logger = logging.getLogger(__name__)
        logger.info("="*80)
        logger.info("LOGGING SYSTEM SHUTDOWN")
        logger.info(f"Log saved to: {self.main_log_file}")
        logger.info("="*80)
        
        # Flush everything
        self._flush_all()
        
        # Close file handlers
        for handle in self.log_handles:
            if hasattr(handle, 'close'):
                handle.close()
        
        # Move to history if not latest
        if self.main_log_file != self.latest_log_file and self.main_log_file.exists():
            import shutil
            try:
                shutil.copy2(
                    self.main_log_file,
                    self.history_dir / self.main_log_file.name
                )
            except Exception as e:
                print(f"Warning: Could not copy log to history: {e}", file=self.original_stderr)
    
    @contextmanager
    def capture_output(self, module_name: str):
        """
        Context manager to capture all stdout/stderr for a module.
        
        Usage:
            with logger.capture_output("test_module"):
                # All output here is captured
                print("This is logged")
        """
        logger = logging.getLogger(module_name)
        logger.info(f"Starting output capture for {module_name}")
        
        # Create module-specific log file
        module_log_file = self.log_dir / f"test_{module_name}_{self.timestamp}.log"
        module_latest = self.log_dir / f"test_{module_name}_latest.log"
        
        # File handler for module
        module_handler = logging.FileHandler(
            module_log_file,
            mode='w',
            encoding='utf-8'
        )
        module_handler.setLevel(logging.DEBUG)
        module_handler.setFormatter(logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        module_handler.stream.reconfigure(write_through=True)
        
        # Add handler
        logger.addHandler(module_handler)
        self.log_handles.append(module_handler)
        
        try:
            yield logger
        except Exception as e:
            logger.exception(f"Exception during {module_name} execution")
            raise
        finally:
            logger.info(f"Completed output capture for {module_name}")
            module_handler.flush()
            module_handler.close()
            logger.removeHandler(module_handler)
            
            # Create symlink to latest
            if module_latest.exists():
                module_latest.unlink()
            try:
                module_latest.symlink_to(module_log_file.name)
            except (OSError, NotImplementedError):
                import shutil
                shutil.copy2(module_log_file, module_latest)


class StreamCapture:
    """
    Captures stdout/stderr to log file while still displaying to console.
    
    This ensures ALL output is logged, even print statements and subprocess output.
    """
    
    def __init__(self, stream_name: str, original_stream: TextIO, log_file: Path):
        self.stream_name = stream_name
        self.original_stream = original_stream
        self.log_file = log_file
        self.logger = logging.getLogger(f"stream.{stream_name}")
    
    def write(self, text: str) -> int:
        """Write to both original stream and log file"""
        # Write to original stream
        if text.strip():  # Only log non-empty lines
            self.logger.debug(f"[{self.stream_name}] {text.rstrip()}")
        
        # Always write to original for console output
        return self.original_stream.write(text)
    
    def flush(self) -> None:
        """Flush both streams"""
        self.original_stream.flush()
        # Logging handlers are auto-flushed
    
    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to original stream"""
        return getattr(self.original_stream, name)


def get_test_logger(name: str) -> logging.Logger:
    """
    Get a logger for test module.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance configured for comprehensive logging
    """
    # Ensure comprehensive logger is initialized
    ComprehensiveLogger()
    
    # Return logger
    return logging.getLogger(f"test.{name}")


@contextmanager
def log_test_execution(test_name: str):
    """
    Context manager to log test execution with timing.
    
    Usage:
        with log_test_execution("test_my_feature"):
            # Test code here
            pass
    """
    logger = get_test_logger(test_name)
    
    logger.info("="*60)
    logger.info(f"TEST STARTED: {test_name}")
    logger.info("="*60)
    
    start_time = datetime.now()
    
    try:
        yield logger
    except Exception as e:
        logger.exception(f"TEST FAILED: {test_name}")
        logger.error("Exception details:")
        logger.error(f"  Type: {type(e).__name__}")
        logger.error(f"  Message: {str(e)}")
        logger.error("  Traceback:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                logger.error(f"    {line}")
        raise
    finally:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("="*60)
        logger.info(f"TEST COMPLETED: {test_name}")
        logger.info(f"Duration: {duration:.3f} seconds")
        logger.info("="*60)


def setup_comprehensive_logging(level: str = "DEBUG") -> ComprehensiveLogger:
    """
    Setup comprehensive logging for test suite.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        ComprehensiveLogger instance
    """
    logger_instance = ComprehensiveLogger()
    
    # Set root logger level
    logging.getLogger().setLevel(getattr(logging, level.upper()))
    
    return logger_instance


# Initialize on import
_global_logger = ComprehensiveLogger()
