"""
Test Configuration and Fixtures

Centralized test configuration, fixtures, and utilities for the entire project.
"""

import pytest
import sys
import json
import os
import functools
from pathlib import Path
from typing import Dict, Any, Generator, Callable

# Add tools to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "script-generator"))
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "wiki_to_chromadb"))
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "shared"))

# Import mocks
from tools.shared.mock_ollama_client import MockOllamaClient, MockOllamaScenarios
from tools.shared.logging_config import setup_logger, capture_output


@pytest.fixture
def mock_ollama_client() -> MockOllamaClient:
    """Basic mock Ollama client"""
    return MockOllamaClient()


@pytest.fixture
def mock_ollama_broadcast() -> MockOllamaClient:
    """Mock Ollama client configured for broadcast generation"""
    return MockOllamaScenarios.broadcast_generation()


@pytest.fixture
def mock_ollama_flaky() -> MockOllamaClient:
    """Mock Ollama client that fails intermittently"""
    return MockOllamaScenarios.flaky_connection()


@pytest.fixture
def mock_llm() -> MockOllamaClient:
    """Alias for mock_ollama_client (used by llm_validator tests)"""
    return MockOllamaClient()


@pytest.fixture
def project_root() -> Path:
    """Project root directory"""
    return PROJECT_ROOT


@pytest.fixture
def test_data_dir(project_root) -> Path:
    """Test data directory"""
    data_dir = project_root / "tests" / "fixtures" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def test_output_dir(project_root, tmp_path) -> Path:
    """Temporary output directory for tests"""
    return tmp_path / "test_output"


@pytest.fixture
def sample_dj_profile() -> Dict[str, Any]:
    """Sample DJ profile for testing"""
    return {
        "name": "Julie (2102, Appalachia)",
        "era": "2102",
        "location": "Appalachia",
        "personality": {
            "traits": ["optimistic", "friendly", "helpful"],
            "speaking_style": "casual and upbeat",
            "catchphrases": ["Good morning, Appalachia!", "Stay safe out there!"]
        },
        "knowledge_base": {
            "specialties": ["Appalachian lore", "Vault 76", "Reclamation Day"],
            "topics": ["weather", "news", "gossip"]
        }
    }


@pytest.fixture
def sample_broadcast_segment() -> Dict[str, Any]:
    """Sample broadcast segment for testing"""
    return {
        "id": "test_segment_001",
        "segment_type": "news",
        "timestamp": "2102-11-01T08:00:00",
        "dj": "Julie (2102, Appalachia)",
        "content": "Good morning, Appalachia! This is Julie bringing you the latest news...",
        "metadata": {
            "duration_seconds": 45,
            "generated_at": "2026-01-20T10:00:00",
            "model": "test-model"
        }
    }


@pytest.fixture
def sample_weather_data() -> Dict[str, Any]:
    """Sample weather data for testing"""
    return {
        "condition": "Partly cloudy with a chance of radstorms",
        "temperature": 68,
        "radiation_level": "Moderate",
        "wind": "Light breeze from the east",
        "forecast": "Clearing up by evening",
        "warnings": ["Wear radiation protection if traveling east"]
    }


@pytest.fixture
def test_logger():
    """Test logger with minimal configuration"""
    return setup_logger("test_logger")


@pytest.fixture
def capture_test_output(tmp_path) -> Generator:
    """Capture all output during test execution"""
    with capture_output("test_session") as session:
        yield session


@pytest.fixture
def mock_chromadb_collection():
    """Mock ChromaDB collection for testing"""
    class MockCollection:
        def __init__(self):
            self.documents = []
            self.metadatas = []
            self.ids = []
        
        def add(self, documents, metadatas, ids):
            self.documents.extend(documents)
            self.metadatas.extend(metadatas)
            self.ids.extend(ids)
        
        def query(self, query_texts, n_results=10, where=None):
            # Return mock results
            return {
                "documents": [self.documents[:n_results] if self.documents else []],
                "metadatas": [self.metadatas[:n_results] if self.metadatas else []],
                "ids": [self.ids[:n_results] if self.ids else []],
                "distances": [[0.1] * min(n_results, len(self.documents))]
            }
        
        def count(self):
            return len(self.documents)
    
    return MockCollection()


# Markers for test organization
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "mock: tests using mock clients (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: integration tests requiring multiple components"
    )
    config.addinivalue_line(
        "markers", "slow: slow-running tests (e.g., full pipeline tests)"
    )
    config.addinivalue_line(
        "markers", "e2e: end-to-end tests with real external services"
    )
    config.addinivalue_line(
        "markers", "requires_ollama: tests requiring real Ollama server (skip in CI)"
    )
    config.addinivalue_line(
        "markers", "requires_chromadb: tests requiring real ChromaDB (skip in CI)"
    )


# Test utilities
class TestHelpers:
    """Helper utilities for tests"""
    
    @staticmethod
    def assert_valid_json(text: str) -> Dict[str, Any]:
        """Assert text is valid JSON and return parsed result"""
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON: {e}")
    
    @staticmethod
    def assert_contains_all(text: str, *keywords: str):
        """Assert text contains all specified keywords"""
        text_lower = text.lower()
        for keyword in keywords:
            assert keyword.lower() in text_lower, f"Missing keyword: {keyword}"
    
    @staticmethod
    def assert_file_exists(path: Path):
        """Assert file exists and is not empty"""
        assert path.exists(), f"File does not exist: {path}"
        assert path.stat().st_size > 0, f"File is empty: {path}"
    
    @staticmethod
    def load_json_file(path: Path) -> Dict[str, Any]:
        """Load and parse JSON file"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def save_json_file(path: Path, data: Dict[str, Any]):
        """Save data as JSON file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)


@pytest.fixture
def helpers():
    """Test helper utilities"""
    return TestHelpers()


# ============================================================================
# Test Decorators for Conditional Execution
# ============================================================================

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
