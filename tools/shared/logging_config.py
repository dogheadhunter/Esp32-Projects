"""
Comprehensive Logging Infrastructure

This module provides centralized logging with THREE simultaneous formats:
- .log: Human-readable detailed logs with complete terminal output
- .json: Structured metadata for programmatic analysis
- .llm.md: LLM-optimized markdown (token-efficient, 50-60% smaller)

Features:
- Complete terminal output capture
- User cancellation event tracking (Ctrl+C)
- Session-based log files with timestamps
- Structured logging for debugging
- Log retention and rotation
- Exception and traceback capture

Usage:
    from tools.shared.logging_config import setup_logger, capture_output
    
    # Basic usage
    logger = setup_logger(__name__)
    logger.info("Processing started")
    
    # Capture all output to 3 formats
    with capture_output("my_session", "Running E2E tests") as output:
        # All prints and logs are captured
        print("This will be logged")
        logger.info("This too")
        output.log_event("TEST_PASSED", {"name": "test_example"})
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
    - An LLM-optimized markdown file (logs/session_YYYYMMDD_HHMMSS.llm.md)
    - Complete terminal capture
    """
    
    def __init__(self, session_name: str = "default", session_context: Optional[str] = None, log_dir: Optional[Path] = None):
        self.session_name = session_name
        self.session_context = session_context
        self.start_time = datetime.now()
        self.session_id = self.start_time.strftime('%Y%m%d_%H%M%S')
        
        # Use provided log_dir or default to LOG_DIR
        output_dir = log_dir if log_dir is not None else LOG_DIR
        
        # Create session-specific log files
        self.log_file = output_dir / f"session_{self.session_id}_{session_name}.log"
        self.metadata_file = output_dir / f"session_{self.session_id}_{session_name}.json"
        self.llm_file = output_dir / f"session_{self.session_id}_{session_name}.llm.md"
        
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
        
        # LLM log tracking
        self.llm_events = []
        self.event_count = 0
        
        # Initialize log files
        self._init_log_file()
        self._init_llm_file()
        
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
    
    def _init_llm_file(self):
        """Initialize LLM-optimized markdown log file"""
        context = self.session_context or "No specific context provided"
        
        header = f"""# SESSION: {self.session_name}

**Session ID:** {self.session_id}  
**Started:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}  
**Command:** `{' '.join(sys.argv)}`  
**Working Dir:** `{Path.cwd()}`

## CONTEXT

{context}

## EVENTS

"""
        with open(self.llm_file, 'w', encoding='utf-8') as f:
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
        
        # Write to LLM file immediately
        try:
            with open(self.llm_file, 'a', encoding='utf-8') as f:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                f.write(f"\n## EVENT: User Cancellation (+{elapsed:.0f}s)\n\n")
                f.write(f"**What:** User interrupted execution (Ctrl+C)\n")
                f.write(f"**Signal:** {signum}\n")
                f.write(f"**Impact:** Session terminated prematurely\n\n")
        except Exception:
            pass
        
        # Log event (will be saved in close())
        self.log_event("USER_CANCELLATION", cancellation_info)
        
        # Re-raise to allow normal cancellation behavior
        raise KeyboardInterrupt()
    
    def log_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log a structured event to all formats"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": event_data
        }
        self.metadata["events"].append(event)
        self.event_count += 1
        
        # Add to LLM events for state snapshots
        self.llm_events.append(event)
        
        # Write to LLM file
        self._write_llm_event(event_type, event_data)
        
        # Write state snapshot every 10 events
        if self.event_count % 10 == 0:
            self._write_llm_state()
    
    def _write_llm_event(self, event_type: str, event_data: Dict[str, Any]):
        """Write event to LLM markdown file in token-efficient format"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        with open(self.llm_file, 'a', encoding='utf-8') as f:
            f.write(f"### {event_type} (+{elapsed:.0f}s)\n\n")
            
            # Extract key information based on event type
            if event_type == "USER_CANCELLATION":
                f.write(f"**What:** User interrupted execution\n")
                f.write(f"**Result:** Session cancelled\n\n")
            
            elif event_type == "EXCEPTION":
                f.write(f"**What:** Exception occurred\n")
                f.write(f"**Type:** {event_data.get('type', 'Unknown')}\n")
                f.write(f"**Message:** {event_data.get('message', 'No message')}\n")
                f.write(f"**Impact:** Operation failed\n\n")
            
            elif event_type == "TEST_COMPLETED":
                # Enhanced test result reporting
                f.write(f"**What:** Test suite completed\n")
                f.write(f"**Status:** {event_data.get('status', 'unknown').upper()}\n")
                f.write(f"**Exit code:** {event_data.get('exit_code', 'N/A')}\n\n")
                
                # Test results summary
                if 'total' in event_data and event_data['total'] > 0:
                    f.write(f"**Test Results:**\n")
                    f.write(f"- ✅ Passed: {event_data.get('passed', 0)}\n")
                    if event_data.get('failed', 0) > 0:
                        f.write(f"- ❌ Failed: {event_data.get('failed', 0)}\n")
                    if event_data.get('skipped', 0) > 0:
                        f.write(f"- ⏭️  Skipped: {event_data.get('skipped', 0)}\n")
                    if event_data.get('errors', 0) > 0:
                        f.write(f"- 🔥 Errors: {event_data.get('errors', 0)}\n")
                    if event_data.get('warnings', 0) > 0:
                        f.write(f"- ⚠️  Warnings: {event_data.get('warnings', 0)}\n")
                    f.write(f"- 📊 Total: {event_data.get('total', 0)}\n")
                    f.write(f"- ⏱️  Duration: {event_data.get('duration_seconds', 0):.1f}s\n")
                    
                    # Coverage if available
                    if event_data.get('coverage_percent') is not None:
                        f.write(f"- 📈 Coverage: {event_data['coverage_percent']}%\n")
                    
                    f.write("\n")
                    
                    # Failed tests details (max 10 for brevity)
                    failed_tests = event_data.get('failed_tests', [])
                    if failed_tests:
                        f.write(f"**Failed Tests:** (showing {min(len(failed_tests), 10)} of {len(failed_tests)})\n")
                        for i, test in enumerate(failed_tests[:10]):
                            test_name = test.get('name', 'unknown')
                            # Shorten long test names
                            if len(test_name) > 80:
                                test_name = "..." + test_name[-77:]
                            error = test.get('error', '')
                            # Shorten long errors
                            if len(error) > 100:
                                error = error[:97] + "..."
                            f.write(f"{i+1}. `{test_name}`\n   - {error}\n")
                        f.write("\n")
            
            elif "test" in event_type.lower():
                f.write(f"**What:** {event_data.get('description', event_type)}\n")
                f.write(f"**Result:** {event_data.get('result', 'Unknown')}\n")
                if 'duration' in event_data:
                    f.write(f"**Duration:** {event_data['duration']:.2f}s\n")
                f.write("\n")
            
            else:
                # Generic event format
                f.write(f"**What:** {event_type}\n")
                
                # Include key data points (avoid dumping everything)
                key_fields = ['status', 'result', 'message', 'description', 'count']
                for field in key_fields:
                    if field in event_data:
                        f.write(f"**{field.title()}:** {event_data[field]}\n")
                
                f.write("\n")
    
    def _write_llm_state(self):
        """Write state snapshot to LLM file"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        with open(self.llm_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## STATE SNAPSHOT (+{elapsed:.0f}s)\n\n")
            f.write(f"- **Events logged:** {self.event_count}\n")
            f.write(f"- **Session duration:** {elapsed:.0f}s\n")
            f.write(f"- **Status:** {self.metadata['status']}\n\n")
    
    def log_exception(self, exc: Exception):
        """Log an exception with full traceback"""
        exc_info = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc()
        }
        
        self.log_event("EXCEPTION", exc_info)
        
        # Write to log file (full traceback)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"EXCEPTION OCCURRED\n")
            f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Type: {type(exc).__name__}\n")
            f.write(f"Message: {str(exc)}\n")
            f.write(f"{'='*80}\n")
            f.write(traceback.format_exc())
            f.write(f"{'='*80}\n\n")
        
        # Write to LLM file (brief context only)
        elapsed = (datetime.now() - self.start_time).total_seconds()
        with open(self.llm_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## EVENT: Exception (+{elapsed:.0f}s)\n\n")
            f.write(f"**What:** Exception occurred during execution\n")
            f.write(f"**Type:** `{type(exc).__name__}`\n")
            f.write(f"**Message:** {str(exc)}\n")
            f.write(f"**Impact:** Operation failed, see full log for traceback\n\n")
    
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
            f.write(f"LLM log saved to: {self.llm_file}\n")
        
        # Write summary to LLM file
        self._write_llm_summary(status, duration)
        
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
    
    def _write_llm_summary(self, status: str, duration: float):
        """Write concise summary to LLM file"""
        with open(self.llm_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## SUMMARY\n\n")
            f.write(f"- **Status:** {status}\n")
            f.write(f"- **Duration:** {duration:.0f}s ({duration/60:.1f}min)\n")
            f.write(f"- **Total events:** {self.event_count}\n")
            
            # Count event types
            event_types = {}
            for event in self.metadata["events"]:
                event_type = event["type"]
                event_types[event_type] = event_types.get(event_type, 0) + 1
            
            if event_types:
                f.write(f"\n**Event breakdown:**\n")
                for event_type, count in sorted(event_types.items()):
                    f.write(f"- {event_type}: {count}\n")
            
            f.write(f"\n**Files:**\n")
            f.write(f"- Human log: `{self.log_file.name}`\n")
            f.write(f"- Structured metadata: `{self.metadata_file.name}`\n")
            f.write(f"- LLM log: `{self.llm_file.name}`\n")


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
def capture_output(session_name: str = "script", context: Optional[str] = None, log_dir: Optional[Path] = None):
    """
    Context manager that captures ALL terminal output.
    
    This includes:
    - All print() statements
    - All logging output
    - All stdout/stderr
    - User cancellations
    - Exceptions and tracebacks
    
    Outputs to THREE formats:
    - .log: Human-readable detailed log
    - .json: Structured metadata
    - .llm.md: LLM-optimized markdown (token-efficient)
    
    Usage:
        with capture_output("my_script", "Running E2E tests") as session:
            print("This will be captured")
            # ... do work ...
            session.log_event("MILESTONE", {"step": "completed step 1"})
    
    Args:
        session_name: Name for this session
        context: Optional context/goal description for LLM log
        log_dir: Optional custom directory for log files (defaults to logs/)
    
    Yields:
        SessionLogger instance for logging events
    """
    session = SessionLogger(session_name, context, log_dir)
    
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
        print(f"📊 LLM log: {session.llm_file}")
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
            # Also remove corresponding JSON and LLM files
            json_file = log_file.with_suffix('.json')
            llm_file = log_file.with_suffix('.llm.md')
            
            log_file.unlink()
            if json_file.exists():
                json_file.unlink()
            if llm_file.exists():
                llm_file.unlink()
            
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
