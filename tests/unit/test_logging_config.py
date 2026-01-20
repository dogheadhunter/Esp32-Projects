"""
Unit Tests for Logging Infrastructure

Tests comprehensive logging including:
- Terminal output capture
- User cancellation handling
- Session-based logging
- Structured logging
- Exception tracking
"""

import pytest
import sys
import os
import signal
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from tools.shared.logging_config import (
    setup_logger,
    capture_output,
    SessionLogger,
    TerminalCapture,
    cleanup_old_logs,
    LOG_DIR
)


class TestSetupLogger:
    """Tests for logger setup"""
    
    def test_basic_logger_creation(self):
        """Test creating a basic logger"""
        logger = setup_logger("test_logger")
        
        assert logger is not None
        assert logger.name == "test_logger"
        assert len(logger.handlers) > 0
    
    def test_logger_with_custom_level(self):
        """Test logger with custom log level"""
        import logging
        logger = setup_logger("debug_logger", level=logging.DEBUG)
        
        assert logger.level == logging.DEBUG
    
    def test_logger_file_creation(self, tmp_path):
        """Test that logger creates log file"""
        log_file = tmp_path / "test.log"
        logger = setup_logger("file_test", log_file=log_file)
        
        logger.info("Test message")
        
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content
    
    def test_structured_logging(self, tmp_path):
        """Test structured JSON logging"""
        log_file = tmp_path / "structured.log"
        logger = setup_logger("structured_test", log_file=log_file, structured=True)
        
        logger.info("Structured message", extra={"key": "value"})
        
        content = log_file.read_text()
        # Should be valid JSON
        for line in content.strip().split('\n'):
            if line:
                data = json.loads(line)
                assert "timestamp" in data
                assert "level" in data
                assert "message" in data
    
    def test_logger_singleton(self):
        """Test that same logger name returns same instance"""
        logger1 = setup_logger("singleton_test")
        logger2 = setup_logger("singleton_test")
        
        assert logger1 is logger2


class TestTerminalCapture:
    """Tests for terminal output capture"""
    
    def test_capture_print_statements(self, tmp_path):
        """Test capturing print statements"""
        log_file = tmp_path / "capture.log"
        original_stdout = sys.stdout
        
        capture = TerminalCapture(log_file, original_stdout)
        sys.stdout = capture
        
        try:
            print("Test output")
            
            # Check it was written to file
            assert log_file.exists()
            content = log_file.read_text()
            assert "Test output" in content
            
            # Check it was captured in buffer
            captured = capture.get_captured()
            assert "Test output" in captured
        finally:
            sys.stdout = original_stdout
    
    def test_capture_multiple_writes(self, tmp_path):
        """Test capturing multiple write operations"""
        log_file = tmp_path / "multi.log"
        original_stdout = sys.stdout
        
        capture = TerminalCapture(log_file, original_stdout)
        sys.stdout = capture
        
        try:
            print("Line 1")
            print("Line 2")
            print("Line 3")
            
            captured = capture.get_captured()
            assert "Line 1" in captured
            assert "Line 2" in captured
            assert "Line 3" in captured
        finally:
            sys.stdout = original_stdout


class TestSessionLogger:
    """Tests for session-based logging"""
    
    def test_session_creation(self, tmp_path):
        """Test session logger creation"""
        # Temporarily change LOG_DIR for testing
        import tools.shared.logging_config as log_config
        original_log_dir = log_config.LOG_DIR
        log_config.LOG_DIR = tmp_path
        
        try:
            session = SessionLogger("test_session")
            
            assert session.session_name == "test_session"
            assert session.log_file.exists()
            assert session.metadata_file.parent == tmp_path
        finally:
            log_config.LOG_DIR = original_log_dir
    
    def test_session_metadata(self, tmp_path):
        """Test session metadata tracking"""
        import tools.shared.logging_config as log_config
        original_log_dir = log_config.LOG_DIR
        log_config.LOG_DIR = tmp_path
        
        try:
            session = SessionLogger("metadata_test")
            
            metadata = session.metadata
            assert metadata["session_name"] == "metadata_test"
            assert "start_time" in metadata
            assert "command" in metadata
            assert "events" in metadata
            assert metadata["status"] == "running"
        finally:
            log_config.LOG_DIR = original_log_dir
    
    def test_log_event(self, tmp_path):
        """Test logging structured events"""
        import tools.shared.logging_config as log_config
        original_log_dir = log_config.LOG_DIR
        log_config.LOG_DIR = tmp_path
        
        try:
            session = SessionLogger("event_test")
            
            session.log_event("TEST_EVENT", {
                "key": "value",
                "number": 42
            })
            
            assert len(session.metadata["events"]) == 1
            event = session.metadata["events"][0]
            assert event["type"] == "TEST_EVENT"
            assert event["data"]["key"] == "value"
            assert event["data"]["number"] == 42
        finally:
            log_config.LOG_DIR = original_log_dir
    
    def test_log_exception(self, tmp_path):
        """Test logging exceptions with traceback"""
        import tools.shared.logging_config as log_config
        original_log_dir = log_config.LOG_DIR
        log_config.LOG_DIR = tmp_path
        
        try:
            session = SessionLogger("exception_test")
            
            try:
                raise ValueError("Test exception")
            except ValueError as e:
                session.log_exception(e)
            
            # Check event was logged
            assert len(session.metadata["events"]) == 1
            event = session.metadata["events"][0]
            assert event["type"] == "EXCEPTION"
            assert "ValueError" in event["data"]["type"]
            assert "Test exception" in event["data"]["message"]
            assert "traceback" in event["data"]
            
            # Check it was written to log file
            content = session.log_file.read_text()
            assert "EXCEPTION OCCURRED" in content
            assert "ValueError" in content
        finally:
            log_config.LOG_DIR = original_log_dir
    
    def test_session_close(self, tmp_path):
        """Test session closing and metadata save"""
        import tools.shared.logging_config as log_config
        original_log_dir = log_config.LOG_DIR
        log_config.LOG_DIR = tmp_path
        
        try:
            session = SessionLogger("close_test")
            session.close(status="completed")
            
            # Check metadata file was created
            assert session.metadata_file.exists()
            
            # Load and verify metadata
            with open(session.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            assert metadata["status"] == "completed"
            assert "end_time" in metadata
            assert "duration_seconds" in metadata
        finally:
            log_config.LOG_DIR = original_log_dir


class TestCaptureOutput:
    """Tests for capture_output context manager"""
    
    def test_basic_capture(self, tmp_path):
        """Test basic output capture"""
        import tools.shared.logging_config as log_config
        original_log_dir = log_config.LOG_DIR
        log_config.LOG_DIR = tmp_path
        
        try:
            with capture_output("basic_test") as session:
                print("Captured output")
                assert session.session_name == "basic_test"
            
            # Check log file was created
            log_files = list(tmp_path.glob("session_*_basic_test.log"))
            assert len(log_files) == 1
            
            content = log_files[0].read_text()
            assert "Captured output" in content
            assert "Starting session" in content
            assert "SESSION ENDED" in content
        finally:
            log_config.LOG_DIR = original_log_dir
    
    def test_capture_with_events(self, tmp_path):
        """Test capture with custom events"""
        import tools.shared.logging_config as log_config
        original_log_dir = log_config.LOG_DIR
        log_config.LOG_DIR = tmp_path
        
        try:
            with capture_output("event_capture") as session:
                print("Step 1")
                session.log_event("STEP_1_COMPLETE", {"status": "ok"})
                
                print("Step 2")
                session.log_event("STEP_2_COMPLETE", {"status": "ok"})
            
            # Check metadata
            json_files = list(tmp_path.glob("session_*_event_capture.json"))
            assert len(json_files) == 1
            
            with open(json_files[0], 'r') as f:
                metadata = json.load(f)
            
            assert len(metadata["events"]) == 2
            assert metadata["events"][0]["type"] == "STEP_1_COMPLETE"
            assert metadata["events"][1]["type"] == "STEP_2_COMPLETE"
        finally:
            log_config.LOG_DIR = original_log_dir
    
    def test_capture_exception_handling(self, tmp_path):
        """Test that exceptions are captured and logged"""
        import tools.shared.logging_config as log_config
        original_log_dir = log_config.LOG_DIR
        log_config.LOG_DIR = tmp_path
        
        try:
            with pytest.raises(ValueError):
                with capture_output("exception_capture") as session:
                    print("About to fail")
                    raise ValueError("Test error")
            
            # Check that exception was logged
            json_files = list(tmp_path.glob("session_*_exception_capture.json"))
            assert len(json_files) == 1
            
            with open(json_files[0], 'r') as f:
                metadata = json.load(f)
            
            assert metadata["status"] == "failed"
            
            # Check log file has exception details
            log_files = list(tmp_path.glob("session_*_exception_capture.log"))
            content = log_files[0].read_text()
            assert "EXCEPTION OCCURRED" in content
            assert "ValueError" in content
        finally:
            log_config.LOG_DIR = original_log_dir
    
    def test_stream_restoration(self, tmp_path):
        """Test that stdout/stderr are restored after capture"""
        import tools.shared.logging_config as log_config
        original_log_dir = log_config.LOG_DIR
        log_config.LOG_DIR = tmp_path
        
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        try:
            with capture_output("restore_test"):
                # Streams should be replaced during capture
                assert sys.stdout != original_stdout
                assert sys.stderr != original_stderr
            
            # Streams should be restored after capture
            assert sys.stdout == original_stdout
            assert sys.stderr == original_stderr
        finally:
            log_config.LOG_DIR = original_log_dir
    
    def test_capture_both_stdout_and_stderr(self, tmp_path):
        """Test capturing both stdout and stderr"""
        import tools.shared.logging_config as log_config
        original_log_dir = log_config.LOG_DIR
        log_config.LOG_DIR = tmp_path
        
        try:
            with capture_output("both_streams") as session:
                print("stdout message")
                print("stderr message", file=sys.stderr)
            
            log_files = list(tmp_path.glob("session_*_both_streams.log"))
            content = log_files[0].read_text()
            
            assert "stdout message" in content
            assert "stderr message" in content
        finally:
            log_config.LOG_DIR = original_log_dir


class TestCleanupOldLogs:
    """Tests for log cleanup functionality"""
    
    def test_cleanup_old_files(self, tmp_path):
        """Test cleaning up old log files"""
        import tools.shared.logging_config as log_config
        original_log_dir = log_config.LOG_DIR
        log_config.LOG_DIR = tmp_path
        
        try:
            # Create some test files
            old_log = tmp_path / "session_20200101_120000_old.log"
            old_json = tmp_path / "session_20200101_120000_old.json"
            recent_log = tmp_path / "session_20260120_120000_recent.log"
            
            old_log.touch()
            old_json.touch()
            recent_log.touch()
            
            # Make old files actually old
            import time
            old_time = time.time() - (60 * 24 * 60 * 60)  # 60 days ago
            os.utime(old_log, (old_time, old_time))
            os.utime(old_json, (old_time, old_time))
            
            # Cleanup files older than 30 days
            cleanup_old_logs(days=30)
            
            # Old files should be removed
            assert not old_log.exists()
            assert not old_json.exists()
            
            # Recent files should still exist
            assert recent_log.exists()
        finally:
            log_config.LOG_DIR = original_log_dir


class TestLoggingIntegration:
    """Integration tests for logging system"""
    
    def test_complete_workflow(self, tmp_path):
        """Test complete logging workflow from start to finish"""
        import tools.shared.logging_config as log_config
        original_log_dir = log_config.LOG_DIR
        log_config.LOG_DIR = tmp_path
        
        try:
            with capture_output("workflow_test") as session:
                print("Starting workflow")
                
                # Log some events
                session.log_event("INIT", {"status": "started"})
                
                # Simulate some work
                print("Processing step 1...")
                session.log_event("STEP_1", {"progress": 33})
                
                print("Processing step 2...")
                session.log_event("STEP_2", {"progress": 66})
                
                print("Processing step 3...")
                session.log_event("STEP_3", {"progress": 100})
                
                print("Workflow complete")
            
            # Verify all outputs were captured
            log_files = list(tmp_path.glob("session_*_workflow_test.log"))
            assert len(log_files) == 1
            
            content = log_files[0].read_text()
            assert "Starting workflow" in content
            assert "Processing step 1" in content
            assert "Processing step 2" in content
            assert "Processing step 3" in content
            assert "Workflow complete" in content
            assert "SESSION ENDED" in content
            
            # Verify metadata
            json_files = list(tmp_path.glob("session_*_workflow_test.json"))
            with open(json_files[0], 'r') as f:
                metadata = json.load(f)
            
            assert metadata["status"] == "completed"
            assert len(metadata["events"]) == 4
            assert metadata["events"][0]["type"] == "INIT"
            assert metadata["events"][3]["type"] == "STEP_3"
        finally:
            log_config.LOG_DIR = original_log_dir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
