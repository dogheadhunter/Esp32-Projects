"""
E2E Test Configuration and Fixtures

Provides fixtures for real external services:
- Ollama (LLM server)
- ChromaDB (vector database)

Tests are SKIPPED BY DEFAULT unless explicitly enabled with:
- --run-e2e: Run all E2E tests
- --run-ollama: Run only Ollama E2E tests
- --run-chromadb: Run only ChromaDB E2E tests
"""

import pytest
import sys
import time
from pathlib import Path
from typing import Generator
import chromadb
from chromadb.config import Settings

# Add tools to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "script-generator"))
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "wiki_to_chromadb"))
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "shared"))

from tools.shared.logging_config import capture_output


# ============================================================================
# Command Line Options
# ============================================================================

def pytest_addoption(parser):
    """Add command line options for E2E tests"""
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run all E2E tests (requires Ollama and ChromaDB)"
    )
    parser.addoption(
        "--run-ollama",
        action="store_true",
        default=False,
        help="Run Ollama E2E tests (requires Ollama server)"
    )
    parser.addoption(
        "--run-chromadb",
        action="store_true",
        default=False,
        help="Run ChromaDB E2E tests (requires ChromaDB)"
    )


def pytest_configure(config):
    """Configure E2E test markers"""
    config.addinivalue_line(
        "markers", "e2e: end-to-end tests with real external services"
    )
    config.addinivalue_line(
        "markers", "requires_ollama: requires real Ollama server running"
    )
    config.addinivalue_line(
        "markers", "requires_chromadb: requires real ChromaDB"
    )


def pytest_collection_modifyitems(config, items):
    """Skip E2E tests unless explicitly enabled"""
    run_e2e = config.getoption("--run-e2e")
    run_ollama = config.getoption("--run-ollama")
    run_chromadb = config.getoption("--run-chromadb")
    
    # If --run-e2e is set, enable all E2E tests
    if run_e2e:
        run_ollama = True
        run_chromadb = True
    
    skip_e2e = pytest.mark.skip(reason="E2E tests skipped (use --run-e2e to enable)")
    skip_ollama = pytest.mark.skip(reason="Ollama tests skipped (use --run-ollama to enable)")
    skip_chromadb = pytest.mark.skip(reason="ChromaDB tests skipped (use --run-chromadb to enable)")
    
    for item in items:
        # Skip E2E tests unless enabled
        if "e2e" in item.keywords and not run_e2e:
            item.add_marker(skip_e2e)
        
        # Skip Ollama tests unless enabled
        if "requires_ollama" in item.keywords and not run_ollama and not run_e2e:
            item.add_marker(skip_ollama)
        
        # Skip ChromaDB tests unless enabled
        if "requires_chromadb" in item.keywords and not run_chromadb and not run_e2e:
            item.add_marker(skip_chromadb)


# ============================================================================
# Ollama Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def ollama_base_url() -> str:
    """Base URL for Ollama server"""
    return "http://localhost:11434"


@pytest.fixture(scope="session")
def ollama_client(ollama_base_url):
    """
    Real Ollama client with connection check.
    
    Verifies Ollama server is running before tests.
    """
    try:
        import requests
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
        response.raise_for_status()
        
        # Import Ollama client
        try:
            from ollama import Client
            client = Client(host=ollama_base_url)
            return client
        except ImportError:
            pytest.skip("ollama package not installed (pip install ollama)")
    
    except requests.exceptions.ConnectionError:
        pytest.skip(f"Ollama server not running at {ollama_base_url}")
    except Exception as e:
        pytest.skip(f"Failed to connect to Ollama: {e}")


@pytest.fixture(scope="session")
def ollama_model_name() -> str:
    """Default model name for Ollama tests"""
    return "llama3.1:8b"


@pytest.fixture
def verify_ollama_model(ollama_client, ollama_model_name):
    """Verify required model is available"""
    try:
        models = ollama_client.list()
        model_names = [m["name"] for m in models.get("models", [])]
        
        if ollama_model_name not in model_names:
            pytest.skip(f"Model {ollama_model_name} not available. Run: ollama pull {ollama_model_name}")
    
    except Exception as e:
        pytest.skip(f"Failed to list Ollama models: {e}")


# ============================================================================
# ChromaDB Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def chromadb_test_dir(tmp_path_factory) -> Path:
    """Temporary directory for ChromaDB test databases"""
    return tmp_path_factory.mktemp("chromadb_e2e")


@pytest.fixture
def chromadb_client(chromadb_test_dir) -> Generator[chromadb.Client, None, None]:
    """
    Real ChromaDB client with cleanup.
    
    Creates a persistent client with unique test directory.
    Automatically cleans up after tests.
    """
    try:
        # Create persistent client with test directory
        client = chromadb.PersistentClient(
            path=str(chromadb_test_dir),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        yield client
        
        # Cleanup: delete all collections
        try:
            client.reset()
        except Exception:
            pass  # Ignore cleanup errors
    
    except Exception as e:
        pytest.skip(f"Failed to initialize ChromaDB: {e}")


@pytest.fixture
def chromadb_collection(chromadb_client):
    """
    Create a test collection with cleanup.
    
    Returns a fresh ChromaDB collection for each test.
    """
    collection_name = f"test_collection_{int(time.time() * 1000)}"
    
    collection = chromadb_client.create_collection(
        name=collection_name,
        metadata={"test": True}
    )
    
    yield collection
    
    # Cleanup: delete collection
    try:
        chromadb_client.delete_collection(collection_name)
    except Exception:
        pass  # Ignore cleanup errors


# ============================================================================
# Logging Fixtures
# ============================================================================

@pytest.fixture
def e2e_capture_output(request):
    """
    Capture all output during E2E tests to 3 log formats.
    
    Logs are saved with test name for easy debugging.
    """
    test_name = request.node.name
    context = f"E2E Test: {test_name}"
    
    with capture_output(f"e2e_{test_name}", context) as session:
        yield session


# ============================================================================
# Shared Test Data
# ============================================================================

@pytest.fixture
def sample_documents():
    """Sample documents for ChromaDB tests"""
    return [
        {
            "id": "doc1",
            "text": "The Vault Dweller emerged from Vault 13 into the wasteland.",
            "metadata": {"type": "lore", "region": "California", "year": "2161"}
        },
        {
            "id": "doc2",
            "text": "The Brotherhood of Steel is a techno-religious organization.",
            "metadata": {"type": "faction", "region": "West Coast", "year": "2077"}
        },
        {
            "id": "doc3",
            "text": "Nuka-Cola is the most popular pre-war soft drink.",
            "metadata": {"type": "item", "region": "Everywhere", "year": "Pre-War"}
        }
    ]


@pytest.fixture
def sample_prompts():
    """Sample prompts for Ollama tests"""
    return [
        "What is 2+2?",
        "Write a haiku about coding.",
        "List three colors."
    ]
