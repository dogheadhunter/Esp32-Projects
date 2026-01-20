"""
Pytest configuration and fixtures for ESP32 AI Radio tests

This file provides:
- Test fixtures for mocked dependencies
- Pytest markers for test organization
- Logging configuration
- Shared test utilities
"""

import pytest
import sys
import os
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import logging utilities
from tests.fixtures.logging_utils import (
    setup_comprehensive_logging,
    get_test_logger,
    log_test_execution
)

# Import mocks
from tests.mocks.mock_llm import MockLLMClient, MockLLMClientWithFailure
from tests.mocks.mock_chromadb import MockChromaDBIngestor, MockChromaDBWithFailure


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Pytest startup configuration"""
    # Setup comprehensive logging
    setup_comprehensive_logging(level="DEBUG")
    
    # Register custom markers
    config.addinivalue_line(
        "markers", "mock: tests using mock clients (no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: tests requiring real Ollama/ChromaDB"
    )
    config.addinivalue_line(
        "markers", "slow: tests that take >5 seconds"
    )
    config.addinivalue_line(
        "markers", "e2e: end-to-end workflow tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Auto-mark tests based on path
    for item in items:
        # Mark tests in integration/ as integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Mark tests in e2e/ as e2e tests
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
        
        # Mark tests using mocks
        if "mock" in str(item.fspath).lower() or "unit" in str(item.fspath):
            item.add_marker(pytest.mark.mock)


# ============================================================================
# LOGGING FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def logger():
    """Session-scoped logger"""
    return get_test_logger("test_session")


@pytest.fixture(scope="function")
def test_logger(request):
    """Function-scoped logger with test name"""
    test_name = request.node.name
    with log_test_execution(test_name) as logger:
        yield logger


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_llm():
    """Fixture providing fresh MockLLMClient instance"""
    client = MockLLMClient()
    yield client
    # Cleanup
    client.clear_call_log()


@pytest.fixture
def mock_llm_with_failure():
    """Fixture providing MockLLMClient that fails after N calls"""
    def _create_failing_client(fail_after_n_calls=3):
        return MockLLMClientWithFailure(fail_after_n_calls=fail_after_n_calls)
    return _create_failing_client


@pytest.fixture
def mock_chromadb():
    """Fixture providing fresh MockChromaDBIngestor instance"""
    db = MockChromaDBIngestor()
    yield db
    # Cleanup
    db.clear_query_log()


@pytest.fixture
def mock_chromadb_with_failure():
    """Fixture providing MockChromaDBIngestor that fails after N queries"""
    def _create_failing_db(fail_after_n_queries=3):
        return MockChromaDBWithFailure(fail_after_n_queries=fail_after_n_queries)
    return _create_failing_db


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def tmp_output_dir(tmp_path):
    """Temporary output directory for test files"""
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def sample_dj_personality():
    """Sample DJ personality configuration"""
    return {
        'name': 'Test DJ',
        'era': '2102',
        'location': 'Test Wasteland',
        'personality_traits': [
            'friendly',
            'informative',
            'optimistic'
        ],
        'voice_style': 'warm and engaging',
        'catchphrases': [
            'Stay safe out there!',
            'This is Test DJ, keeping you company.'
        ]
    }


@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing"""
    return {
        'condition': 'sunny',
        'temperature': 75,
        'radiation_level': 'low',
        'wind_speed': 10,
        'description': 'Clear skies over the wasteland'
    }


@pytest.fixture
def sample_script_segment():
    """Sample script segment for testing"""
    return {
        'segment_type': 'weather',
        'timestamp': '2102-08-15T08:00:00',
        'content': 'Good morning, survivors! The weather today is looking good.',
        'metadata': {
            'dj': 'Test DJ',
            'validated': True,
            'word_count': 12
        }
    }


# ============================================================================
# INTEGRATION TEST HELPERS
# ============================================================================

@pytest.fixture(scope="session")
def check_ollama_available():
    """Check if Ollama is available for integration tests"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def check_chromadb_available():
    """Check if ChromaDB is available for integration tests"""
    try:
        import chromadb
        client = chromadb.Client()
        return True
    except Exception:
        return False


def pytest_runtest_setup(item):
    """Setup hook to skip integration tests if dependencies unavailable"""
    # Check for integration marker
    if "integration" in item.keywords:
        # Check if Ollama is required and available
        if "ollama" in str(item.fspath).lower():
            try:
                import requests
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code != 200:
                    pytest.skip("Ollama not available for integration test")
            except Exception:
                pytest.skip("Ollama not available for integration test")
        
        # Check if ChromaDB is required and available
        if "chromadb" in str(item.fspath).lower():
            try:
                import chromadb
                client = chromadb.Client()
            except Exception:
                pytest.skip("ChromaDB not available for integration test")


# ============================================================================
# TEST DATA CLEANUP
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_artifacts(request, tmp_path):
    """Automatically cleanup test artifacts after each test"""
    yield
    # Cleanup happens after test
    # Note: tmp_path is automatically cleaned up by pytest


# ============================================================================
# COVERAGE CONFIGURATION
# ============================================================================

def pytest_sessionfinish(session, exitstatus):
    """Hook called after whole test run finished"""
    # Note: Logging may be closed at this point, so we skip final logging
    # All important logging is done during test execution
    pass


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def assert_mock_llm_called(mock_llm, expected_calls=None):
    """
    Assert that mock LLM was called.
    
    Args:
        mock_llm: MockLLMClient instance
        expected_calls: Expected number of calls (None = any calls)
    """
    calls = mock_llm.get_call_log()
    if expected_calls is not None:
        assert len(calls) == expected_calls, \
            f"Expected {expected_calls} LLM calls, got {len(calls)}"
    else:
        assert len(calls) > 0, "Expected LLM to be called at least once"


def assert_mock_chromadb_called(mock_db, expected_queries=None):
    """
    Assert that mock ChromaDB was queried.
    
    Args:
        mock_db: MockChromaDBIngestor instance
        expected_queries: Expected number of queries (None = any queries)
    """
    queries = mock_db.get_query_log()
    if expected_queries is not None:
        assert len(queries) == expected_queries, \
            f"Expected {expected_queries} ChromaDB queries, got {len(queries)}"
    else:
        assert len(queries) > 0, "Expected ChromaDB to be queried at least once"


# Make helper functions available as fixtures
@pytest.fixture
def assert_llm_called():
    """Fixture providing assert_mock_llm_called function"""
    return assert_mock_llm_called


@pytest.fixture
def assert_chromadb_called():
    """Fixture providing assert_mock_chromadb_called function"""
    return assert_mock_chromadb_called
