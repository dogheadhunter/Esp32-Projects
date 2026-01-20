#!/bin/bash
# Script Review App - Tailscale Startup (Linux/macOS)
# This script starts the FastAPI server and configures Tailscale for remote access

echo "========================================"
echo "Script Review App - Tailscale Mode"
echo "========================================"
echo ""

# Check if Tailscale is installed
if ! command -v tailscale &> /dev/null; then
    echo "[ERROR] Tailscale is not installed!"
    echo ""
    echo "Please install Tailscale from:"
    echo "https://tailscale.com/download"
    echo ""
    echo "Or use: curl -fsSL https://tailscale.com/install.sh | sh"
    echo ""
    exit 1
fi

# Check if Tailscale is running
if ! tailscale status &> /dev/null; then
    echo "[WARNING] Tailscale is not running!"
    echo "Please start Tailscale and connect to your network."
    echo ""
    exit 1
fi

echo "[OK] Tailscale is running"
echo ""

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Start the FastAPI server in background
echo "[INFO] Starting FastAPI server..."
python3 -m backend.main &
SERVER_PID=$!

# Wait for server to start
echo "[INFO] Waiting for server to start..."
sleep 5

# Check if server is running
if curl -s -f -o /dev/null "http://localhost:8000/health"; then
    echo "[OK] Server is running"
    echo ""
else
    echo "[WARNING] Server may not have started properly"
    echo "Check the logs for errors"
    echo ""
fi

# Configure Tailscale serve for HTTPS
echo "[INFO] Configuring Tailscale HTTPS..."
tailscale serve https / http://localhost:8000

# Get Tailscale URL
echo ""
echo "========================================"
echo "Script Review App is READY!"
echo "========================================"
echo ""

# Extract Tailscale hostname
TAILSCALE_URL=$(tailscale status | grep "$(hostname)" | awk '{print $2}' | head -n 1)

if [ -n "$TAILSCALE_URL" ]; then
    echo "Access your app from any device with Tailscale:"
    echo ""
    echo "  https://$TAILSCALE_URL"
    echo ""
    echo "Copy this URL to your phone's browser!"
else
    echo "Run 'tailscale status' to find your URL"
    echo "It will look like: https://YOUR-MACHINE.TAILNET.ts.net"
fi

echo ""
echo "[INFO] Mobile Access:"
echo "  1. Install Tailscale on your phone"
echo "  2. Sign in with the same account"
echo "  3. Connect to your Tailscale network"
echo "  4. Open the URL above"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Cleanup on exit
cleanup() {
    echo ""
    echo "[INFO] Stopping server..."
    kill $SERVER_PID 2>/dev/null
    
    echo "[INFO] Resetting Tailscale serve..."
    tailscale serve reset
    
    echo "[OK] Cleanup complete"
    exit 0
}

# Register cleanup handlers
trap cleanup INT TERM

# Wait for interrupt
wait
