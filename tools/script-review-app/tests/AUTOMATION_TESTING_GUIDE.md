# Tailscale Automation Testing Suite

Comprehensive automation testing for the Script Review App with Tailscale integration.

## Overview

This test suite provides:
- **3-Format Logging Verification** - Ensures TXT, JSON, and LLM.md logs are generated correctly
- **Mobile UI Testing** - Complete mobile viewport testing with JPG screenshots
- **CI/CD Integration** - Headless testing and parallel execution support
- **End-to-End Workflows** - Complete user journeys on mobile devices
- **Performance Testing** - Load time and screenshot generation performance
- **Cross-Platform Support** - Works on Windows, macOS, and Linux

## Test Files

### 1. `test_tailscale_automation.py`
Comprehensive automation test suite with the following test classes:

- **TestLoggingSystem** - Verifies 3-format logging (TXT, JSON, LLM.md)
- **TestMobileUI** - Mobile viewport and touch gesture testing
- **TestScreenshotQuality** - JPG format and quality verification
- **TestCICDIntegration** - Headless and parallel execution tests
- **TestEndToEndWorkflows** - Complete user workflows
- **TestPerformance** - Performance benchmarking

### 2. `start_tailscale_logged.py`
Python wrapper for Tailscale startup with full 3-format logging integration.

## Running Tests

### All Tests
```bash
cd tools/script-review-app
pytest tests/test_tailscale_automation.py -v
```

### By Category
```bash
# Logging verification only
pytest tests/test_tailscale_automation.py -m "logging" -v

# Mobile UI tests only
pytest tests/test_tailscale_automation.py -m "mobile" -v

# Screenshot tests only
pytest tests/test_tailscale_automation.py -m "screenshots" -v

# Performance tests only
pytest tests/test_tailscale_automation.py -m "performance" -v

# CI/CD integration tests
pytest tests/test_tailscale_automation.py -m "cicd" -v

# End-to-end workflows
pytest tests/test_tailscale_automation.py -m "e2e" -v
```

### With Coverage
```bash
pytest tests/test_tailscale_automation.py --cov=backend --cov-report=html -v
```

### In Headless Mode (for CI/CD)
```bash
pytest tests/test_tailscale_automation.py --headed=false -v
```

## Test Markers

The test suite uses pytest markers for organization:

- `@pytest.mark.automation` - All automation tests
- `@pytest.mark.tailscale` - Tailscale-specific tests
- `@pytest.mark.logging` - Logging system verification
- `@pytest.mark.mobile` - Mobile viewport tests
- `@pytest.mark.ui` - UI interaction tests
- `@pytest.mark.screenshots` - Screenshot quality tests
- `@pytest.mark.cicd` - CI/CD integration tests
- `@pytest.mark.e2e` - End-to-end workflow tests
- `@pytest.mark.performance` - Performance benchmarks

## Logging Verification

The test suite verifies all 3 logging formats:

### TXT Log (.log)
- Complete terminal output
- Human-readable format
- Detailed timestamps
- Full exception tracebacks

### JSON Metadata (.json)
- Structured event data
- Programmatic access
- CI/CD integration
- Metrics and analytics

### LLM Markdown (.llm.md)
- Token-efficient format
- 50-60% smaller than TXT
- AI-optimized content
- Quick debugging reference

Example verification test:
```python
def test_logger_creates_all_three_formats(session_logger):
    """Verify logger creates TXT, JSON, and LLM.md files."""
    assert session_logger.log_file.exists()       # .log
    assert session_logger.metadata_file.exists()  # .json
    assert session_logger.llm_file.exists()       # .llm.md
```

## Screenshot Configuration

All screenshots use JPG format to avoid size errors:

```python
SCREENSHOT_FORMAT = "jpeg"
SCREENSHOT_QUALITY = 80  # Good balance of quality/size

def take_screenshot(page, name, full_page=False):
    screenshot_path = SCREENSHOT_DIR / f"{name}.jpg"
    page.screenshot(
        path=str(screenshot_path),
        type="jpeg",      # JPG, not PNG
        quality=80,       # Configurable quality
        full_page=full_page
    )
    return screenshot_path
```

### Benefits of JPG over PNG:
- **5-10x smaller file size**
- **No CI/CD upload errors**
- **Faster test execution**
- **Still excellent quality at 80%**

## Mobile Viewport Configuration

Tests use iPhone 12 Pro viewport:

```python
MOBILE_VIEWPORT = {"width": 390, "height": 844}
USER_AGENT_MOBILE = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)"

@pytest.fixture
def mobile_context(browser):
    return browser.new_context(
        viewport=MOBILE_VIEWPORT,
        user_agent=USER_AGENT_MOBILE,
        has_touch=True,
        is_mobile=True,
        device_scale_factor=3  # Retina display
    )
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tailscale Automation Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      
      - name: Run automation tests
        run: |
          cd tools/script-review-app
          pytest tests/test_tailscale_automation.py -v --headed=false
      
      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-screenshots
          path: tools/script-review-app/tests/screenshots/
      
      - name: Upload logs
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-logs
          path: tools/script-review-app/logs/
```

### GitLab CI Example
```yaml
test:tailscale:
  stage: test
  image: mcr.microsoft.com/playwright/python:v1.40.0-focal
  script:
    - pip install -r requirements.txt
    - cd tools/script-review-app
    - pytest tests/test_tailscale_automation.py -v
  artifacts:
    when: always
    paths:
      - tools/script-review-app/tests/screenshots/
      - tools/script-review-app/logs/
    expire_in: 1 week
```

## Test Output

### Successful Run
```
tests/test_tailscale_automation.py::TestLoggingSystem::test_logger_creates_all_three_formats PASSED
tests/test_tailscale_automation.py::TestLoggingSystem::test_txt_log_contains_output PASSED
tests/test_tailscale_automation.py::TestLoggingSystem::test_json_metadata_structure PASSED
tests/test_tailscale_automation.py::TestLoggingSystem::test_llm_markdown_format PASSED
tests/test_tailscale_automation.py::TestMobileUI::test_homepage_loads_on_mobile PASSED
tests/test_tailscale_automation.py::TestMobileUI::test_mobile_viewport_responsive PASSED
tests/test_tailscale_automation.py::TestScreenshotQuality::test_screenshots_are_jpg_format PASSED
tests/test_tailscale_automation.py::TestScreenshotQuality::test_screenshot_size_acceptable PASSED
tests/test_tailscale_automation.py::TestCICDIntegration::test_headless_mode_works PASSED
tests/test_tailscale_automation.py::TestPerformance::test_page_load_time_acceptable PASSED

========== 10 passed in 15.23s ==========
```

### Log Files Generated
After running tests, you'll find:
```
tools/script-review-app/logs/
├── session_20260120_230000_tailscale_automation.log      # TXT - Complete output
├── session_20260120_230000_tailscale_automation.json     # JSON - Structured data
└── session_20260120_230000_tailscale_automation.llm.md   # LLM - AI-optimized
```

## Troubleshooting

### Tests Fail with "Connection Refused"
**Problem:** Server not running  
**Solution:** Start server first or use `start_tailscale_logged.py`

### Screenshots Too Large
**Problem:** PNG format being used  
**Solution:** Verify `SCREENSHOT_FORMAT = "jpeg"` in test file

### Logging Files Not Created
**Problem:** Logger not properly initialized  
**Solution:** Check `session_logger` fixture is used

### Touch Events Not Working
**Problem:** Mobile context not configured  
**Solution:** Use `mobile_context` and `mobile_page` fixtures

## Performance Benchmarks

Typical test execution times:
- **Logging tests**: ~0.5s per test
- **Mobile UI tests**: ~2-3s per test
- **Screenshot tests**: ~1-2s per test
- **E2E workflows**: ~5-10s per test
- **Full suite**: ~15-30s (depends on parallelization)

## Best Practices

1. **Always use JPG for screenshots** - Avoid PNG size errors
2. **Use session logger fixture** - Ensures proper logging
3. **Take screenshots on failure** - Helps debugging
4. **Use mobile viewport** - Matches real device testing
5. **Verify all 3 log formats** - Ensures complete logging
6. **Run in headless mode for CI/CD** - Faster execution
7. **Use pytest markers** - Organize test execution

## Example: Verifying Logging in Tests

```python
def test_my_feature_with_logging(mobile_page, session_logger):
    """Test feature with full logging."""
    # Log test start
    session_logger.log_event("TEST_START", {
        "test": "my_feature",
        "viewport": "mobile"
    })
    
    try:
        # Perform test actions
        mobile_page.goto(TAILSCALE_URL)
        screenshot = take_screenshot(mobile_page, "my_feature")
        
        # Log success
        session_logger.log_event("TEST_COMPLETE", {
            "test": "my_feature",
            "status": "passed",
            "screenshot": str(screenshot)
        })
        
    except Exception as e:
        # Log failure
        session_logger.log_event("TEST_FAILED", {
            "test": "my_feature",
            "error": str(e)
        })
        raise
```

## Additional Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Tailscale Documentation](https://tailscale.com/kb/)
- [Session Logger API](../../shared/logging_config.py)

## Support

For issues or questions:
1. Check test logs in `tools/script-review-app/logs/`
2. Review screenshots in `tools/script-review-app/tests/screenshots/automation/`
3. Run with `-v` flag for verbose output
4. Use `--pdb` flag to drop into debugger on failure
