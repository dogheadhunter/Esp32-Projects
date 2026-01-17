"""
Test decorators for conditional test execution.

Allows tests to be skipped if required dependencies (Ollama, ChromaDB) are not available.

PHASE 4: Testing Infrastructure
"""

import os
import functools
import pytest
from typing import Callable, Any


def requires_ollama(func: Callable) -> Callable:
    """
    Decorator to mark tests that require Ollama to be running.
    
    Tests decorated with this will be skipped if OLLAMA_AVAILABLE environment
    variable is not set or is False.
    
    Usage:
        @requires_ollama
        def test_ollama_integration():
            # This test requires Ollama
            pass
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not os.environ.get('OLLAMA_AVAILABLE', '').lower() in ('true', '1', 'yes'):
            pytest.skip("Ollama not available (set OLLAMA_AVAILABLE=true to run)")
        return func(*args, **kwargs)
    
    return wrapper


def requires_chromadb(func: Callable) -> Callable:
    """
    Decorator to mark tests that require ChromaDB to be available.
    
    Tests decorated with this will be skipped if CHROMADB_AVAILABLE environment
    variable is not set or is False.
    
    Usage:
        @requires_chromadb
        def test_chromadb_integration():
            # This test requires ChromaDB
            pass
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not os.environ.get('CHROMADB_AVAILABLE', '').lower() in ('true', '1', 'yes'):
            pytest.skip("ChromaDB not available (set CHROMADB_AVAILABLE=true to run)")
        return func(*args, **kwargs)
    
    return wrapper


def requires_both(func: Callable) -> Callable:
    """
    Decorator to mark tests that require both Ollama and ChromaDB.
    
    Tests decorated with this will be skipped if either dependency is unavailable.
    
    Usage:
        @requires_both
        def test_full_integration():
            # This test requires both Ollama and ChromaDB
            pass
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        ollama_available = os.environ.get('OLLAMA_AVAILABLE', '').lower() in ('true', '1', 'yes')
        chromadb_available = os.environ.get('CHROMADB_AVAILABLE', '').lower() in ('true', '1', 'yes')
        
        if not (ollama_available and chromadb_available):
            missing = []
            if not ollama_available:
                missing.append("Ollama")
            if not chromadb_available:
                missing.append("ChromaDB")
            
            pytest.skip(f"{', '.join(missing)} not available (set OLLAMA_AVAILABLE=true and CHROMADB_AVAILABLE=true to run)")
        
        return func(*args, **kwargs)
    
    return wrapper


def mark_slow(func: Callable) -> Callable:
    """
    Decorator to mark tests as slow.
    
    Slow tests can be excluded from test runs using:
        pytest -m "not slow"
    
    Usage:
        @mark_slow
        def test_slow_operation():
            # This test takes a long time
            pass
    """
    return pytest.mark.slow(func)


def mark_integration(func: Callable) -> Callable:
    """
    Decorator to mark tests as integration tests.
    
    Integration tests can be excluded using:
        pytest -m "not integration"
    
    Usage:
        @mark_integration
        def test_full_workflow():
            # This test checks integration between components
            pass
    """
    return pytest.mark.integration(func)


def mark_mock(func: Callable) -> Callable:
    """
    Decorator to mark tests as using mocks.
    
    Mock tests can be run exclusively using:
        pytest -m "mock"
    
    Usage:
        @mark_mock
        def test_with_mock_client():
            # This test uses mock clients
            pass
    """
    return pytest.mark.mock(func)


class IntegrationTestContext:
    """
    Context manager for running tests with real Ollama/ChromaDB when available.
    
    Example:
        with IntegrationTestContext(require_ollama=True, require_chromadb=True) as ctx:
            if ctx.should_skip:
                pytest.skip(ctx.skip_reason)
            # Run integration test
    """
    
    def __init__(self,
                require_ollama: bool = False,
                require_chromadb: bool = False):
        """
        Initialize context.
        
        Args:
            require_ollama: Require Ollama to be available
            require_chromadb: Require ChromaDB to be available
        """
        self.require_ollama = require_ollama
        self.require_chromadb = require_chromadb
        self.should_skip = False
        self.skip_reason = ""
    
    def __enter__(self) -> 'IntegrationTestContext':
        """Check dependencies and set skip flags"""
        ollama_available = os.environ.get('OLLAMA_AVAILABLE', '').lower() in ('true', '1', 'yes')
        chromadb_available = os.environ.get('CHROMADB_AVAILABLE', '').lower() in ('true', '1', 'yes')
        
        missing = []
        if self.require_ollama and not ollama_available:
            missing.append("Ollama")
        if self.require_chromadb and not chromadb_available:
            missing.append("ChromaDB")
        
        if missing:
            self.should_skip = True
            self.skip_reason = f"{', '.join(missing)} not available"
        
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Cleanup (no action needed)"""
        pass
