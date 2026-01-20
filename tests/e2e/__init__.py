"""
End-to-End Tests

These tests can use real external services (Ollama, ChromaDB) when available.
They are skipped by default in CI/CD but can be run manually for full integration testing.

To run these tests:
    pytest tests/e2e/ -v --run-e2e

To run with specific services:
    pytest tests/e2e/ -v --run-ollama
    pytest tests/e2e/ -v --run-chromadb
"""
