# Playwright Tests for Script Review App
# Uses Playwright MCP Server for testing
# Screenshots are saved as JPG to reduce file size

This directory contains Playwright-based browser tests for the Script Review App running on Tailscale.

## Overview

These tests verify the app works correctly when accessed via Tailscale, including:
- Mobile viewport interactions
- Swipe gestures
- API authentication
- Script review workflow
- Offline PWA functionality

## Screenshot Format

**Important**: All screenshots are saved as **JPG (JPEG)** format with 80% quality to avoid file size issues.

**Why JPG instead of PNG:**
- **Smaller file size**: JPG is 5-10x smaller than PNG for screenshots
- **Avoids size errors**: Prevents issues with large PNG files
- **Good enough quality**: 80% quality is perfect for test verification
- **Faster uploads**: Smaller files upload faster in CI/CD

## Running Tests

### Prerequisites

1. **Tailscale must be running** and connected
2. **Script Review App must be running** via `start_tailscale.bat` or `start_tailscale.sh`
3. **Python dependencies installed**: `pip install pytest playwright`
4. **Playwright browsers installed**: `playwright install`

### Run All Tests

```bash
cd tools/script-review-app
pytest tests/test_tailscale_mobile.py -v
```

### Run Specific Test

```bash
pytest tests/test_tailscale_mobile.py::test_mobile_swipe_gestures -v
```

### Run with Headed Browser (see what's happening)

```bash
pytest tests/test_tailscale_mobile.py -v --headed
```

### Run with Slow Motion (debug)

```bash
pytest tests/test_tailscale_mobile.py -v --headed --slowmo 1000
```

## Test Files

- `test_tailscale_mobile.py` - Main test suite for mobile interactions
- `test_tailscale_auth.py` - Authentication flow tests
- `test_tailscale_pwa.py` - Progressive Web App functionality
- `test_tailscale_performance.py` - Performance and load time tests

## Screenshot Storage

Screenshots are saved to:
```
tests/screenshots/
├── mobile_home_page.jpg
├── script_card.jpg
├── swipe_approve.jpg
├── swipe_reject.jpg
└── stats_dashboard.jpg
```

All screenshots use JPG format with 80% quality for optimal size/quality ratio.

## Configuration

### Test Configuration (conftest.py)

```python
# Screenshot configuration
SCREENSHOT_FORMAT = "jpeg"  # Use JPEG instead of PNG
SCREENSHOT_QUALITY = 80     # 80% quality for good balance
```

### Playwright Configuration

```python
# Mobile viewport (iPhone 12 Pro)
viewport = {"width": 390, "height": 844}

# User agent for mobile
user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7 like Mac OS X)"
```

## Common Issues

### "Cannot connect to server"
- Ensure Tailscale is running: `tailscale status`
- Ensure app server is running: check `start_tailscale.bat` window
- Check your Tailscale URL is correct in test config

### "Screenshots are too large"
- Verify tests are using `type="jpeg"` not `type="png"`
- Check quality setting is 80 or lower
- Review screenshot dimensions (should be 390x844 for mobile)

### "Tests timeout"
- Check network connection to Tailscale
- Increase timeout in test configuration
- Run with `--headed` to see what's happening

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Setup Tailscale
  uses: tailscale/github-action@v2
  with:
    oauth-client-id: ${{ secrets.TS_OAUTH_CLIENT_ID }}
    oauth-secret: ${{ secrets.TS_OAUTH_SECRET }}
    tags: tag:ci

- name: Start Review App
  run: |
    cd tools/script-review-app
    python -m backend.main &
    sleep 5

- name: Run Playwright Tests
  run: |
    cd tools/script-review-app
    pytest tests/ -v --screenshot=only-on-failure
```

## Best Practices

1. **Always use JPG for screenshots** - Set `type="jpeg"` in all screenshot calls
2. **Limit screenshot dimensions** - Use mobile viewport to keep files small
3. **Take screenshots only when needed** - Not on every step
4. **Use descriptive filenames** - Easy to identify in test reports
5. **Clean up old screenshots** - Don't let test artifacts accumulate

## Example Test

```python
import pytest
from playwright.sync_api import Page, expect

def test_mobile_home_page(page: Page, tailscale_url: str):
    """Test that home page loads on mobile."""
    # Navigate to app
    page.goto(tailscale_url)
    
    # Wait for content
    expect(page.locator("h1")).to_have_text("Script Review")
    
    # Take JPG screenshot
    page.screenshot(
        path="tests/screenshots/home_page.jpg",
        type="jpeg",
        quality=80,
        full_page=True
    )
    
    # Verify mobile viewport
    assert page.viewport_size == {"width": 390, "height": 844}
```

## Troubleshooting

### Screenshots are PNG instead of JPG
Check your screenshot calls:
```python
# ✗ Wrong - defaults to PNG
page.screenshot(path="screenshot.png")

# ✓ Correct - explicit JPG
page.screenshot(path="screenshot.jpg", type="jpeg", quality=80)
```

### File size still too large
1. Reduce quality: Try 60-70% instead of 80%
2. Reduce dimensions: Use smaller viewport
3. Crop: Screenshot only the relevant element
4. Check format: Ensure it's actually JPG not PNG

### Can't view JPG screenshots
JPG is a standard format supported everywhere. If you can't view:
1. Check file extension is `.jpg` or `.jpeg`
2. Open in any image viewer or browser
3. Verify file is not corrupt: `file screenshot.jpg`

## Next Steps

1. Run baseline tests to verify Tailscale setup
2. Add tests for your specific workflows
3. Integrate into CI/CD pipeline
4. Monitor screenshot file sizes
5. Adjust quality/dimensions as needed
