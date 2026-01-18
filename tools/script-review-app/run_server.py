"""Start the FastAPI server for testing"""
import sys
from pathlib import Path
import os

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables
os.environ["SCRIPT_REVIEW_TOKEN"] = "test-token-123"
os.environ["LOG_LEVEL"] = "INFO"

# Import and run
from backend.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
