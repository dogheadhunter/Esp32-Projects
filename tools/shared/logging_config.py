"""
Comprehensive Logging Infrastructure

This module provides centralized logging with:
- Complete terminal output capture
- User cancellation event tracking
- Session-based log files with timestamps
- Structured logging for debugging
- Log retention and rotation
- Exception and traceback capture

Usage:
    from tools.shared.logging_config import setup_logger, capture_output
    
    # Basic usage
    logger = setup_logger(__name__)
    logger.info("Processing started")
    
    # Capture all output context manager
    with capture_output("my_session") as output:
        # All prints and logs are captured
        print("This will be logged")
        logger.info("This too")
"""

import sys
import os
import logging
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, TextIO
from contextlib import contextmanager
import signal


# Project root and log directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)


class TerminalCapture:
    """Captures all terminal output including print statements"""
    
    def __init__(self, log_file: Path, original_stream: TextIO):
        self.log_file = log_file
        self.original_stream = original_stream
        self.buffer = []
        
    def write(self, text: str):
        """Write to both original stream and log file"""
        # Write to original stream
        self.original_stream.write(text)
        
        # Write to log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(text)
        
        # Keep in memory buffer for session
        self.buffer.append(text)
    
    def flush(self):
        """Flush both streams"""
        self.original_stream.flush()
    
    def get_captured(self) -> str:
        """Get all captured output"""
        return ''.join(self.buffer)


class SessionLogger:
    """
    Session-based logger that captures all output including user cancellations.
    
    Each session creates:
    - A timestamped log file (logs/session_YYYYMMDD_HHMMSS.log)
    - A structured JSON metadata file (logs/session_YYYYMMDD_HHMMSS.json)
    - Complete terminal capture
    """
    
    def __init__(self, session_name: str = "default"):
        self.session_name = session_name
        self.start_time = datetime.now()
        self.session_id = self.start_time.strftime('%Y%m%d_%H%M%S')
        
        # Create session-specific log files
        self.log_file = LOG_DIR / f"session_{self.session_id}_{session_name}.log"
        self.metadata_file = LOG_DIR / f"session_{self.session_id}_{session_name}.json"
        
        # Session metadata
        self.metadata: Dict[str, Any] = {
            "session_name": session_name,
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "command": " ".join(sys.argv),
            "working_directory": str(Path.cwd()),
            "python_version": sys.version,
            "events": [],
            "status": "running"
        }
        
        # Initialize log file
        self._init_log_file()
        
        # Setup signal handlers for user cancellation
        self.cancelled = False
        signal.signal(signal.SIGINT, self._handle_cancellation)
        signal.signal(signal.SIGTERM, self._handle_cancellation)
        
    def _init_log_file(self):
        """Initialize log file with header"""
        header = f"""
{'='*80}
SESSION LOG
{'='*80}
Session Name: {self.session_name}
Session ID: {self.session_id}
Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
Command: {' '.join(sys.argv)}
Working Directory: {Path.cwd()}
Python Version: {sys.version.split()[0]}
{'='*80}

"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(header)
    
    def _handle_cancellation(self, signum, frame):
        """Handle user cancellation (Ctrl+C)"""
        self.cancelled = True
        
        cancellation_info = {
            "signal": signum,
            "timestamp": datetime.now().isoformat(),
            "message": "User cancelled script execution"
        }
        
        # Write to log file immediately (atomic operation)
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"USER CANCELLATION DETECTED\n")
                f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Signal: {signum}\n")
                f.write(f"{'='*80}\n\n")
        except Exception:
            pass  # Don't fail on logging during cancellation
        
        # Log event (will be saved in close())
        self.log_event("USER_CANCELLATION", cancellation_info)
        
        # Re-raise to allow normal cancellation behavior
        raise KeyboardInterrupt()
    
    def log_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log a structured event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": event_data
        }
        self.metadata["events"].append(event)
    
    def log_exception(self, exc: Exception):
        """Log an exception with full traceback"""
        exc_info = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc()
        }
        
        self.log_event("EXCEPTION", exc_info)
        
        # Write to log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"EXCEPTION OCCURRED\n")
            f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Type: {type(exc).__name__}\n")
            f.write(f"Message: {str(exc)}\n")
            f.write(f"{'='*80}\n")
            f.write(traceback.format_exc())
            f.write(f"{'='*80}\n\n")
    
    def close(self, status: str = "completed"):
        """Close session and save metadata"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self.metadata["end_time"] = end_time.isoformat()
        self.metadata["duration_seconds"] = duration
        self.metadata["status"] = status
        
        # Write footer to log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"SESSION ENDED\n")
            f.write(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {duration:.2f} seconds\n")
            f.write(f"Status: {status}\n")
            f.write(f"{'='*80}\n")
            # Add log file path to log itself
            f.write(f"\nLog saved to: {self.log_file}\n")
            f.write(f"Metadata saved to: {self.metadata_file}\n")
        
        # Save metadata as JSON (atomic write)
        temp_metadata_file = self.metadata_file.with_suffix('.json.tmp')
        try:
            with open(temp_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
            # Atomic rename
            temp_metadata_file.replace(self.metadata_file)
        except Exception:
            # Clean up temp file if it exists
            if temp_metadata_file.exists():
                temp_metadata_file.unlink()


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": ''.join(traceback.format_exception(*record.exc_info))
            }
        
        return json.dumps(log_data)


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    structured: bool = False
) -> logging.Logger:
    """
    Setup a logger with file and console handlers.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)
        log_file: Optional specific log file path
        structured: Use structured JSON logging (default: False)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler (human-readable)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        log_file = LOG_DIR / f"{name.replace('.', '_')}.log"
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    
    if structured:
        file_handler.setFormatter(StructuredFormatter())
    else:
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
    
    logger.addHandler(file_handler)
    
    return logger


@contextmanager
def capture_output(session_name: str = "script"):
    """
    Context manager that captures ALL terminal output.
    
    This includes:
    - All print() statements
    - All logging output
    - All stdout/stderr
    - User cancellations
    - Exceptions and tracebacks
    
    Usage:
        with capture_output("my_script") as session:
            print("This will be captured")
            # ... do work ...
            session.log_event("MILESTONE", {"step": "completed step 1"})
    
    Args:
        session_name: Name for this session
    
    Yields:
        SessionLogger instance for logging events
    """
    session = SessionLogger(session_name)
    
    # Capture stdout and stderr
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    stdout_capture = TerminalCapture(session.log_file, original_stdout)
    stderr_capture = TerminalCapture(session.log_file, original_stderr)
    
    try:
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        print(f"🚀 Starting session: {session_name}")
        print(f"📋 Logging to: {session.log_file}")
        print()
        
        yield session
        
    except KeyboardInterrupt:
        # Already handled by signal handler
        raise
        
    except Exception as e:
        session.log_exception(e)
        raise
        
    finally:
        # Restore original streams
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        
        # Close session
        if session.cancelled:
            session.close(status="cancelled")
        elif sys.exc_info()[0] is not None:
            session.close(status="failed")
        else:
            session.close(status="completed")


def cleanup_old_logs(days: int = 30):
    """
    Clean up log files older than specified days.
    
    Args:
        days: Keep logs from last N days (default: 30)
    """
    cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
    
    removed_count = 0
    for log_file in LOG_DIR.glob("session_*.log"):
        if log_file.stat().st_mtime < cutoff:
            # Also remove corresponding JSON file
            json_file = log_file.with_suffix('.json')
            
            log_file.unlink()
            if json_file.exists():
                json_file.unlink()
            
            removed_count += 1
    
    if removed_count > 0:
        print(f"🧹 Cleaned up {removed_count} old log files")


if __name__ == "__main__":
    # Example usage
    print("Testing logging infrastructure...\n")
    
    # Test 1: Basic logger
    logger = setup_logger("test_logger")
    logger.info("This is an info message")
    logger.warning("This is a warning")
    logger.error("This is an error")
    
    # Test 2: Capture output
    print("\nTest 2: Capture output context")
    with capture_output("test_session") as session:
        print("This is a print statement")
        logger.info("This is a log message")
        
        session.log_event("TEST_EVENT", {
            "key": "value",
            "number": 42
        })
        
        print("Script completed normally")
    
    # Test 3: Exception handling
    print("\nTest 3: Exception handling")
    try:
        with capture_output("test_exception") as session:
            print("About to raise an exception...")
            raise ValueError("Test exception for logging")
    except ValueError:
        print("Exception was logged and re-raised as expected")
    
    print("\n✅ All logging tests completed!")
    print(f"📁 Check logs in: {LOG_DIR}")
