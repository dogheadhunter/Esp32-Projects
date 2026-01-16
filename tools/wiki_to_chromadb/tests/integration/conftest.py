"""
Pytest configuration and shared fixtures for integration tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir():
    """Return path to test data directory"""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def temp_chromadb():
    """Create temporary ChromaDB directory"""
    temp_dir = tempfile.mkdtemp(prefix="chromadb_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def sample_wiki_pages():
    """Sample wiki pages for testing"""
    return {
        'vault_101': {
            'title': 'Vault 101',
            'text': '''{{Infobox location|name=Vault 101|type=vault}}
Vault 101 is a vault in the Capital Wasteland, constructed in 2063.''',
            'timestamp': '2077-10-23T00:00:00Z'
        },
        'ncr': {
            'title': 'New California Republic',
            'text': '''{{Infobox faction|name=NCR|type=faction}}
The NCR was founded in 2189 in California.''',
            'timestamp': '2189-01-01T00:00:00Z'
        }
    }
