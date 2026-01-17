#!/bin/bash
# Startup script for Script Review App

cd "$(dirname "$0")"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.template .env
    echo "⚠️  Please edit .env and set SCRIPT_REVIEW_TOKEN before running again"
    exit 1
fi

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the server
echo "Starting Script Review App..."
echo "Access the app at: http://localhost:8000"
echo "Press Ctrl+C to stop"
python -m backend.main
