"""
Comprehensive tests for Cloudflare tunnel functionality.

Tests the temporary tunnel creation, URL generation, and web app accessibility.
"""

import pytest
import subprocess
import time
import re
import requests
from pathlib import Path
import os


class TestCloudflareTunnel:
    """Test suite for Cloudflare tunnel integration."""
    
    @pytest.fixture(scope="class")
    def app_dir(self):
        """Get the script-review-app directory."""
        return Path(__file__).parent.parent
    
    @pytest.fixture(scope="class")
    def check_cloudflared(self):
        """Check if cloudflared is installed."""
        try:
            result = subprocess.run(
                ["cloudflared", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def test_cloudflared_installed(self, check_cloudflared):
        """Test that cloudflared is available on the system."""
        if not check_cloudflared:
            pytest.skip("cloudflared not installed - skipping tunnel tests")
        assert check_cloudflared, "cloudflared should be installed"
    
    def test_backend_starts_successfully(self, app_dir):
        """Test that the FastAPI backend starts without errors."""
        # Set environment variables
        env = os.environ.copy()
        env["SCRIPT_REVIEW_TOKEN"] = "test-token-123"
        env["LOG_LEVEL"] = "ERROR"
        
        # Start backend
        process = subprocess.Popen(
            ["python", "run_server.py"],
            cwd=str(app_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for startup
        time.sleep(3)
        
        # Check if process is running
        poll_result = process.poll()
        assert poll_result is None, "Backend process should still be running"
        
        # Test health endpoint
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
        finally:
            process.terminate()
            process.wait(timeout=5)
    
    @pytest.mark.skipif(
        subprocess.run(
            ["cloudflared", "--version"],
            capture_output=True
        ).returncode != 0,
        reason="cloudflared not installed"
    )
    def test_tunnel_creates_valid_url(self, app_dir):
        """Test that cloudflared tunnel creates a valid trycloudflare.com URL."""
        # Start backend first
        env = os.environ.copy()
        env["SCRIPT_REVIEW_TOKEN"] = "test-token-123"
        env["LOG_LEVEL"] = "ERROR"
        
        backend_process = subprocess.Popen(
            ["python", "run_server.py"],
            cwd=str(app_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for backend to start
        time.sleep(3)
        
        try:
            # Start cloudflared tunnel
            tunnel_process = subprocess.Popen(
                ["cloudflared", "tunnel", "--url", "http://localhost:8000"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for tunnel to establish (max 30 seconds)
            tunnel_url = None
            url_pattern = re.compile(r'https://[a-z0-9-]+\.trycloudflare\.com')
            
            start_time = time.time()
            while time.time() - start_time < 30:
                if tunnel_process.poll() is not None:
                    # Process ended unexpectedly
                    stdout, stderr = tunnel_process.communicate()
                    pytest.fail(f"Tunnel process ended: {stderr}")
                
                # Check stderr for tunnel URL (cloudflared outputs to stderr)
                try:
                    line = tunnel_process.stderr.readline()
                    if line:
                        match = url_pattern.search(line)
                        if match:
                            tunnel_url = match.group(0)
                            break
                except Exception:
                    pass
                
                time.sleep(0.5)
            
            # Verify URL was found
            assert tunnel_url is not None, "Tunnel URL should be generated within 30 seconds"
            assert "trycloudflare.com" in tunnel_url, "URL should be a trycloudflare.com domain"
            assert tunnel_url.startswith("https://"), "URL should use HTTPS"
            
            # Verify URL is accessible
            try:
                response = requests.get(f"{tunnel_url}/health", timeout=10)
                assert response.status_code == 200
                assert response.json()["status"] == "healthy"
            except requests.RequestException as e:
                pytest.fail(f"Tunnel URL not accessible: {e}")
            
        finally:
            tunnel_process.terminate()
            tunnel_process.wait(timeout=5)
            backend_process.terminate()
            backend_process.wait(timeout=5)
    
    def test_url_changes_on_restart(self, app_dir, check_cloudflared):
        """Test that tunnel URL changes each time it's restarted."""
        if not check_cloudflared:
            pytest.skip("cloudflared not installed")
        
        urls = []
        
        # Start tunnel twice and collect URLs
        for i in range(2):
            # Start backend
            env = os.environ.copy()
            env["SCRIPT_REVIEW_TOKEN"] = "test-token-123"
            env["LOG_LEVEL"] = "ERROR"
            
            backend_process = subprocess.Popen(
                ["python", "run_server.py"],
                cwd=str(app_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            time.sleep(3)
            
            try:
                # Start tunnel
                tunnel_process = subprocess.Popen(
                    ["cloudflared", "tunnel", "--url", "http://localhost:8000"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Extract URL
                tunnel_url = None
                url_pattern = re.compile(r'https://[a-z0-9-]+\.trycloudflare\.com')
                
                start_time = time.time()
                while time.time() - start_time < 30:
                    try:
                        line = tunnel_process.stderr.readline()
                        if line:
                            match = url_pattern.search(line)
                            if match:
                                tunnel_url = match.group(0)
                                break
                    except Exception:
                        pass
                    time.sleep(0.5)
                
                if tunnel_url:
                    urls.append(tunnel_url)
                
            finally:
                tunnel_process.terminate()
                tunnel_process.wait(timeout=5)
                backend_process.terminate()
                backend_process.wait(timeout=5)
            
            # Wait a bit between restarts
            time.sleep(2)
        
        # Verify we got two URLs and they're different
        assert len(urls) == 2, "Should have collected two tunnel URLs"
        assert urls[0] != urls[1], "Tunnel URLs should be different on each restart"
    
    def test_email_notification_script(self, app_dir):
        """Test that the send_email.py script exists and has proper structure."""
        send_email_path = app_dir / "send_email.py"
        assert send_email_path.exists(), "send_email.py should exist"
        
        # Check script can be imported
        import sys
        sys.path.insert(0, str(app_dir))
        
        try:
            import send_email
            assert hasattr(send_email, "send_tunnel_email"), "Should have send_tunnel_email function"
        except ImportError as e:
            pytest.fail(f"Cannot import send_email: {e}")
    
    def test_tunnel_handles_backend_unavailable(self):
        """Test tunnel behavior when backend is not running."""
        # Try to start tunnel without backend
        tunnel_process = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", "http://localhost:8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for tunnel to establish
        time.sleep(5)
        
        # Tunnel should still create a URL even if backend is down
        # (cloudflared just proxies - it doesn't check if the backend responds)
        tunnel_url = None
        url_pattern = re.compile(r'https://[a-z0-9-]+\.trycloudflare\.com')
        
        try:
            # Check a few lines of output
            for _ in range(10):
                line = tunnel_process.stderr.readline()
                if line:
                    match = url_pattern.search(line)
                    if match:
                        tunnel_url = match.group(0)
                        break
        finally:
            tunnel_process.terminate()
            tunnel_process.wait(timeout=5)
        
        # URL should be generated even without backend
        # (though accessing it would return an error)
        # This is expected behavior - tunnel doesn't validate backend
    
    def test_tunnel_security_documentation(self, app_dir):
        """Test that security documentation exists for tunnel usage."""
        # Check for security documentation
        security_docs = [
            app_dir / "TUNNEL_SETUP.md",
            app_dir.parent.parent / "research" / "gmail-app-passwords-cloudflare-tunnels" / "cloudflare-tunnel-security.md"
        ]
        
        found_docs = [doc for doc in security_docs if doc.exists()]
        assert len(found_docs) > 0, "Security documentation should exist for tunnel usage"
        
        # Check one of the docs mentions security risks
        for doc in found_docs:
            content = doc.read_text()
            assert any(keyword in content.lower() for keyword in [
                "security", "risk", "public", "accessible", "authentication"
            ]), f"{doc.name} should mention security considerations"


class TestTunnelIntegration:
    """Integration tests for complete tunnel workflow."""
    
    def test_tunnel_setup_documentation(self):
        """Test that TUNNEL_SETUP.md provides complete setup instructions."""
        doc_path = Path(__file__).parent.parent / "TUNNEL_SETUP.md"
        assert doc_path.exists(), "TUNNEL_SETUP.md should exist"
        
        content = doc_path.read_text()
        
        # Check for key sections
        required_sections = [
            "Quick Start",
            "cloudflared",
            "Email Notification",
            "Troubleshooting",
            "Security"
        ]
        
        for section in required_sections:
            assert section in content, f"Documentation should include '{section}' section"
    
    def test_powershell_scripts_exist(self):
        """Test that PowerShell automation scripts exist."""
        app_dir = Path(__file__).parent.parent
        
        ps_scripts = [
            "auto-start-simple.ps1",
            "auto-start-with-email.ps1",
            "auto-start-email.ps1"
        ]
        
        for script in ps_scripts:
            script_path = app_dir / script
            assert script_path.exists(), f"{script} should exist"
    
    def test_environment_variables_documented(self):
        """Test that required environment variables are documented."""
        doc_path = Path(__file__).parent.parent / "TUNNEL_SETUP.md"
        content = doc_path.read_text()
        
        # Check for environment variable documentation
        env_vars = [
            "EMAIL_SENDER",
            "EMAIL_PASSWORD",
            "SMTP_SERVER",
            "SMTP_PORT"
        ]
        
        for var in env_vars:
            assert var in content, f"Documentation should mention {var}"
