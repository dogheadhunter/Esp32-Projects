"""Pytest configuration for Playwright tests."""

import pytest
from playwright.sync_api import sync_playwright
import subprocess
import time
import os


@pytest.fixture(scope="session")
def server():
    """Start the FastAPI server for testing."""
    # Set test environment variables
    os.environ["SCRIPT_REVIEW_TOKEN"] = "test-token-123"
    os.environ["LOG_LEVEL"] = "ERROR"  # Reduce log noise during tests
    
    # Start server
    process = subprocess.Popen(
        ["python", "-m", "backend.main"],
        cwd="/home/runner/work/Esp32-Projects/Esp32-Projects/tools/script-review-app",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(3)
    
    yield process
    
    # Cleanup
    process.terminate()
    process.wait()


@pytest.fixture(scope="function")
def browser_context(server):
    """Create a new browser context for each test."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 375, "height": 667},  # Mobile viewport by default
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"
        )
        yield context
        context.close()
        browser.close()


@pytest.fixture(scope="function")
def page(browser_context):
    """Create a new page for each test."""
    page = browser_context.new_page()
    yield page
    page.close()
