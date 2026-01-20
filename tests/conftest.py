"""
Test Configuration and Fixtures

Centralized test configuration, fixtures, and utilities for the entire project.
"""

import pytest
import sys
import json
from pathlib import Path
from typing import Dict, Any, Generator

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
