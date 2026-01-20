"""
Tailscale Startup Script with 3-Format Logging Integration

This script starts the FastAPI server with Tailscale and logs all output to:
- .log: Complete terminal output
- .json: Structured metadata
- .llm.md: LLM-optimized markdown

Usage:
    python start_tailscale_logged.py
"""

import sys
import os
import subprocess
import time
import platform
from pathlib import Path

# Add parent directories to path to import logging_config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.shared.logging_config import SessionLogger


def check_tailscale_installed():
    """Check if Tailscale is installed."""
    try:
        subprocess.run(
            ["tailscale", "version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_tailscale_running():
    """Check if Tailscale is running and connected."""
    try:
        result = subprocess.run(
            ["tailscale", "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError:
        return False, ""


def get_tailscale_url(status_output: str) -> str:
    """Extract Tailscale URL from status output."""
    lines = status_output.split('\n')
    for line in lines:
        if platform.node().lower() in line.lower():
            parts = line.split()
            if len(parts) >= 2:
                hostname = parts[1]
                return f"https://{hostname}"
    return None


def start_server(logger: SessionLogger):
    """Start the FastAPI server."""
    logger.log_event("SERVER_START_ATTEMPT", {
        "port": 8000,
        "module": "backend.main"
    })
    
    print("[INFO] Starting FastAPI server...")
    
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=Path(__file__).parent
    )
    
    # Wait for server to start
    print("[INFO] Waiting for server to start...")
    time.sleep(5)
    
    # Check if server is running
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("[OK] Server is running")
            logger.log_event("SERVER_STARTED", {
                "port": 8000,
                "pid": server_process.pid,
                "status": "healthy"
            })
            return server_process
        else:
            raise Exception(f"Server returned status {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Server failed to start: {e}")
        logger.log_event("SERVER_START_FAILED", {
            "error": str(e)
        })
        server_process.kill()
        return None


def configure_tailscale_serve(logger: SessionLogger):
    """Configure Tailscale to serve HTTPS."""
    logger.log_event("TAILSCALE_SERVE_CONFIG", {
        "target": "http://localhost:8000",
        "protocol": "https"
    })
    
    print("[INFO] Configuring Tailscale HTTPS...")
    
    try:
        result = subprocess.run(
            ["tailscale", "serve", "https", "/", "http://localhost:8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True
        )
        
        print("[OK] Tailscale HTTPS configured")
        logger.log_event("TAILSCALE_SERVE_CONFIGURED", {
            "status": "success",
            "output": result.stdout
        })
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to configure Tailscale: {e}")
        logger.log_event("TAILSCALE_SERVE_FAILED", {
            "error": str(e),
            "output": e.output if hasattr(e, 'output') else None
        })
        return False


def main():
    """Main startup routine with logging."""
    # Create logger for this session
    logger = SessionLogger(
        session_name="tailscale_start",
        session_context="Starting Script Review App with Tailscale for mobile access from anywhere",
        log_dir=Path(__file__).parent / "logs"
    )
    
    try:
        print("="*60)
        print("Script Review App - Tailscale Mode")
        print("="*60)
        print()
        
        # Log startup event
        logger.log_event("STARTUP", {
            "mode": "tailscale",
            "platform": platform.system(),
            "python_version": sys.version
        })
        
        # Check Tailscale installation
        print("[INFO] Checking Tailscale installation...")
        if not check_tailscale_installed():
            print("[ERROR] Tailscale is not installed!")
            print()
            print("Please install Tailscale from:")
            print("  Windows: https://tailscale.com/download/windows")
            print("  macOS:   https://tailscale.com/download/mac")
            print("  Linux:   https://tailscale.com/download/linux")
            print()
            print("Or use package manager:")
            if platform.system() == "Windows":
                print("  winget install tailscale.tailscale")
            elif platform.system() == "Darwin":
                print("  brew install tailscale")
            else:
                print("  See https://tailscale.com/download")
            
            logger.log_event("STARTUP_FAILED", {
                "reason": "tailscale_not_installed",
                "platform": platform.system()
            })
            return 1
        
        print("[OK] Tailscale is installed")
        logger.log_event("TAILSCALE_CHECK", {"installed": True})
        
        # Check Tailscale status
        print("[INFO] Checking Tailscale connection...")
        is_running, status_output = check_tailscale_running()
        
        if not is_running:
            print("[WARNING] Tailscale is not running or not connected!")
            print("Please start Tailscale and connect to your network.")
            print()
            logger.log_event("STARTUP_FAILED", {
                "reason": "tailscale_not_connected"
            })
            return 1
        
        print("[OK] Tailscale is running and connected")
        logger.log_event("TAILSCALE_STATUS", {
            "running": True,
            "connected": True
        })
        
        # Get Tailscale URL
        tailscale_url = get_tailscale_url(status_output)
        if tailscale_url:
            logger.log_event("TAILSCALE_URL_DETECTED", {
                "url": tailscale_url
            })
        
        # Start server
        server_process = start_server(logger)
        if not server_process:
            return 1
        
        # Configure Tailscale
        if not configure_tailscale_serve(logger):
            server_process.kill()
            return 1
        
        # Display success information
        print()
        print("="*60)
        print("Script Review App is READY!")
        print("="*60)
        print()
        
        if tailscale_url:
            print("Access your app from any device with Tailscale:")
            print()
            print(f"  {tailscale_url}")
            print()
            print("Copy this URL to your phone's browser!")
        else:
            print("Run 'tailscale status' to find your URL")
            print("It will look like: https://YOUR-PC.TAILNET.ts.net")
        
        print()
        print("[INFO] Mobile Access:")
        print("  1. Install Tailscale on your phone")
        print("  2. Sign in with the same account")
        print("  3. Connect to your Tailscale network")
        print("  4. Open the URL above")
        print()
        print("Press Ctrl+C to stop the server")
        print()
        
        logger.log_event("STARTUP_COMPLETE", {
            "tailscale_url": tailscale_url,
            "server_pid": server_process.pid
        })
        
        # Wait for server (until user presses Ctrl+C)
        try:
            server_process.wait()
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down...")
            logger.log_event("SHUTDOWN_INITIATED", {
                "reason": "user_interrupt"
            })
            server_process.terminate()
            server_process.wait(timeout=5)
        
        logger.log_event("SHUTDOWN_COMPLETE", {
            "status": "clean"
        })
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        logger.log_event("EXCEPTION", {
            "type": type(e).__name__,
            "message": str(e)
        })
        return 1
    
    finally:
        # Close logger (writes to all 3 formats)
        logger.close()
        print()
        print("[INFO] Session logs saved to:")
        print(f"  TXT:  {logger.log_file}")
        print(f"  JSON: {logger.metadata_file}")
        print(f"  LLM:  {logger.llm_file}")


if __name__ == "__main__":
    sys.exit(main())
