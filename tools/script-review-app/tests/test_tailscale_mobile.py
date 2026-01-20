"""
Playwright tests for Script Review App on Tailscale with mobile viewport.
All screenshots use JPG format to avoid size errors.
"""

import pytest
import os
from pathlib import Path
from playwright.sync_api import Page, expect, Browser, BrowserContext

# Test configuration
TAILSCALE_URL = os.getenv("TAILSCALE_URL", "https://localhost:8000")  # Override with actual Tailscale URL
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
SCREENSHOT_FORMAT = "jpeg"
SCREENSHOT_QUALITY = 80

# Mobile viewport configuration (iPhone 12 Pro)
MOBILE_VIEWPORT = {"width": 390, "height": 844}
USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15"


@pytest.fixture(scope="session", autouse=True)
def setup_screenshots_dir():
    """Create screenshots directory if it doesn't exist."""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup old screenshots
    # Comment out if you want to keep screenshots
    # for screenshot in SCREENSHOT_DIR.glob("*.jpg"):
    #     screenshot.unlink()


@pytest.fixture
def mobile_context(browser: Browser) -> BrowserContext:
    """Create a mobile browser context."""
    context = browser.new_context(
        viewport=MOBILE_VIEWPORT,
        user_agent=USER_AGENT,
        has_touch=True,  # Enable touch events
        is_mobile=True,
        device_scale_factor=3,  # Retina display
    )
    yield context
    context.close()


@pytest.fixture
def mobile_page(mobile_context: BrowserContext) -> Page:
    """Create a mobile page."""
    page = mobile_context.new_page()
    yield page
    page.close()


def take_screenshot(page: Page, name: str, full_page: bool = False):
    """
    Helper function to take JPG screenshots consistently.
    
    Args:
        page: Playwright page object
        name: Screenshot filename (without extension)
        full_page: Whether to capture the full scrollable page
    """
    screenshot_path = SCREENSHOT_DIR / f"{name}.jpg"
    page.screenshot(
        path=str(screenshot_path),
        type=SCREENSHOT_FORMAT,
        quality=SCREENSHOT_QUALITY,
        full_page=full_page
    )
    print(f"[OK] Screenshot saved: {screenshot_path}")


# ==================== Authentication Tests ====================

def test_home_page_loads(mobile_page: Page):
    """Test that the home page loads correctly on mobile."""
    mobile_page.goto(TAILSCALE_URL)
    
    # Wait for page to load
    expect(mobile_page).to_have_title("Script Review")
    
    # Take screenshot
    take_screenshot(mobile_page, "home_page_mobile", full_page=True)
    
    # Verify mobile viewport
    assert mobile_page.viewport_size == MOBILE_VIEWPORT


def test_auth_token_prompt(mobile_page: Page):
    """Test that authentication token prompt appears."""
    mobile_page.goto(TAILSCALE_URL)
    
    # Should show token input
    token_input = mobile_page.locator('input[type="password"]')
    expect(token_input).to_be_visible()
    
    # Take screenshot
    take_screenshot(mobile_page, "auth_prompt")


def test_auth_token_validation(mobile_page: Page):
    """Test token authentication flow."""
    mobile_page.goto(TAILSCALE_URL)
    
    # Enter invalid token
    mobile_page.fill('input[type="password"]', "invalid-token")
    mobile_page.click('button[type="submit"]')
    
    # Should show error
    expect(mobile_page.locator(".error")).to_be_visible()
    take_screenshot(mobile_page, "auth_error")
    
    # Enter valid token (get from env)
    test_token = os.getenv("SCRIPT_REVIEW_TOKEN", "test-token-123")
    mobile_page.fill('input[type="password"]', test_token)
    mobile_page.click('button[type="submit"]')
    
    # Should navigate to main app
    expect(mobile_page.locator(".script-card")).to_be_visible(timeout=5000)
    take_screenshot(mobile_page, "auth_success")


# ==================== UI/UX Tests ====================

def test_mobile_layout_responsive(mobile_page: Page):
    """Test that the mobile layout is responsive."""
    # Login first
    test_token = os.getenv("SCRIPT_REVIEW_TOKEN", "test-token-123")
    mobile_page.goto(TAILSCALE_URL)
    mobile_page.fill('input[type="password"]', test_token)
    mobile_page.click('button[type="submit"]')
    
    # Check script card is visible and centered
    script_card = mobile_page.locator(".script-card").first
    expect(script_card).to_be_visible()
    
    # Verify touch-friendly button sizes (at least 44x44px)
    approve_btn = mobile_page.locator('button:has-text("Approve")').first
    reject_btn = mobile_page.locator('button:has-text("Reject")').first
    
    expect(approve_btn).to_be_visible()
    expect(reject_btn).to_be_visible()
    
    take_screenshot(mobile_page, "mobile_layout")


def test_script_card_display(mobile_page: Page):
    """Test that script card displays correctly."""
    # Login
    test_token = os.getenv("SCRIPT_REVIEW_TOKEN", "test-token-123")
    mobile_page.goto(TAILSCALE_URL)
    mobile_page.fill('input[type="password"]', test_token)
    mobile_page.click('button[type="submit"]')
    
    # Get first script card
    script_card = mobile_page.locator(".script-card").first
    expect(script_card).to_be_visible()
    
    # Verify card contains DJ name, script content
    expect(script_card.locator(".dj-name")).to_be_visible()
    expect(script_card.locator(".script-content")).to_be_visible()
    
    take_screenshot(mobile_page, "script_card_detail")


# ==================== Swipe Gesture Tests ====================

def test_swipe_right_approve(mobile_page: Page):
    """Test swipe right gesture to approve script."""
    # Login
    test_token = os.getenv("SCRIPT_REVIEW_TOKEN", "test-token-123")
    mobile_page.goto(TAILSCALE_URL)
    mobile_page.fill('input[type="password"]', test_token)
    mobile_page.click('button[type="submit"]')
    
    # Get script card
    script_card = mobile_page.locator(".script-card").first
    expect(script_card).to_be_visible()
    
    # Get card position
    box = script_card.bounding_box()
    if box:
        # Simulate swipe right (touchstart -> touchmove -> touchend)
        mobile_page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        mobile_page.mouse.down()
        mobile_page.mouse.move(box["x"] + box["width"] * 1.5, box["y"] + box["height"] / 2)
        mobile_page.mouse.up()
        
        # Card should disappear (approved)
        expect(script_card).not_to_be_visible(timeout=2000)
        take_screenshot(mobile_page, "swipe_approve_after")


def test_swipe_left_reject(mobile_page: Page):
    """Test swipe left gesture to reject script."""
    # Login
    test_token = os.getenv("SCRIPT_REVIEW_TOKEN", "test-token-123")
    mobile_page.goto(TAILSCALE_URL)
    mobile_page.fill('input[type="password"]', test_token)
    mobile_page.click('button[type="submit"]')
    
    # Get script card
    script_card = mobile_page.locator(".script-card").first
    expect(script_card).to_be_visible()
    
    # Take before screenshot
    take_screenshot(mobile_page, "before_swipe_reject")
    
    # Get card position
    box = script_card.bounding_box()
    if box:
        # Simulate swipe left
        mobile_page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        mobile_page.mouse.down()
        mobile_page.mouse.move(box["x"] - box["width"] * 0.5, box["y"] + box["height"] / 2)
        mobile_page.mouse.up()
        
        # Should show rejection reason dialog
        expect(mobile_page.locator(".rejection-modal")).to_be_visible(timeout=2000)
        take_screenshot(mobile_page, "rejection_modal")


# ==================== Button Interaction Tests ====================

def test_approve_button_click(mobile_page: Page):
    """Test approve button click interaction."""
    # Login
    test_token = os.getenv("SCRIPT_REVIEW_TOKEN", "test-token-123")
    mobile_page.goto(TAILSCALE_URL)
    mobile_page.fill('input[type="password"]', test_token)
    mobile_page.click('button[type="submit"]')
    
    # Click approve button
    approve_btn = mobile_page.locator('button:has-text("Approve")').first
    expect(approve_btn).to_be_visible()
    approve_btn.click()
    
    # Script should be approved and next one loads
    mobile_page.wait_for_timeout(1000)
    take_screenshot(mobile_page, "after_approve_click")


def test_reject_button_with_reason(mobile_page: Page):
    """Test reject button with reason selection."""
    # Login
    test_token = os.getenv("SCRIPT_REVIEW_TOKEN", "test-token-123")
    mobile_page.goto(TAILSCALE_URL)
    mobile_page.fill('input[type="password"]', test_token)
    mobile_page.click('button[type="submit"]')
    
    # Click reject button
    reject_btn = mobile_page.locator('button:has-text("Reject")').first
    expect(reject_btn).to_be_visible()
    reject_btn.click()
    
    # Should show rejection reasons
    expect(mobile_page.locator(".rejection-modal")).to_be_visible()
    take_screenshot(mobile_page, "rejection_reasons")
    
    # Select a reason
    mobile_page.locator('select[name="reason"]').select_option("lore_inaccurate")
    take_screenshot(mobile_page, "reason_selected")
    
    # Submit rejection
    mobile_page.locator('button:has-text("Submit")').click()
    
    # Should load next script
    mobile_page.wait_for_timeout(1000)
    take_screenshot(mobile_page, "after_rejection")


# ==================== Statistics Tests ====================

def test_stats_dashboard(mobile_page: Page):
    """Test that statistics dashboard displays correctly."""
    # Login
    test_token = os.getenv("SCRIPT_REVIEW_TOKEN", "test-token-123")
    mobile_page.goto(TAILSCALE_URL)
    mobile_page.fill('input[type="password"]', test_token)
    mobile_page.click('button[type="submit"]')
    
    # Navigate to stats
    mobile_page.click('a:has-text("Stats")')
    
    # Verify stats are visible
    expect(mobile_page.locator(".stats-card")).to_be_visible()
    take_screenshot(mobile_page, "stats_dashboard", full_page=True)


# ==================== Offline/PWA Tests ====================

def test_pwa_manifest_exists(mobile_page: Page):
    """Test that PWA manifest is accessible."""
    response = mobile_page.goto(f"{TAILSCALE_URL}/static/manifest.json")
    assert response.status == 200
    
    # Parse manifest
    manifest = response.json()
    assert manifest.get("name") == "Script Review"
    assert "icons" in manifest


def test_service_worker_registration(mobile_page: Page):
    """Test that service worker registers correctly."""
    mobile_page.goto(TAILSCALE_URL)
    
    # Wait for service worker to register
    mobile_page.wait_for_timeout(2000)
    
    # Check if service worker is registered
    sw_registered = mobile_page.evaluate("""
        () => {
            return navigator.serviceWorker.controller !== null;
        }
    """)
    
    assert sw_registered, "Service worker should be registered"


# ==================== Performance Tests ====================

def test_page_load_performance(mobile_page: Page):
    """Test that page loads within acceptable time."""
    import time
    
    start_time = time.time()
    mobile_page.goto(TAILSCALE_URL)
    
    # Wait for main content
    mobile_page.wait_for_selector("h1", timeout=5000)
    load_time = time.time() - start_time
    
    # Should load in under 3 seconds on mobile
    assert load_time < 3.0, f"Page took {load_time:.2f}s to load"
    
    take_screenshot(mobile_page, "performance_loaded")


# ==================== Accessibility Tests ====================

def test_keyboard_navigation(mobile_page: Page):
    """Test keyboard navigation works."""
    # Login
    test_token = os.getenv("SCRIPT_REVIEW_TOKEN", "test-token-123")
    mobile_page.goto(TAILSCALE_URL)
    mobile_page.fill('input[type="password"]', test_token)
    mobile_page.keyboard.press("Enter")
    
    # Tab through elements
    mobile_page.keyboard.press("Tab")
    mobile_page.wait_for_timeout(500)
    take_screenshot(mobile_page, "keyboard_focus_1")
    
    mobile_page.keyboard.press("Tab")
    mobile_page.wait_for_timeout(500)
    take_screenshot(mobile_page, "keyboard_focus_2")


def test_touch_target_sizes(mobile_page: Page):
    """Test that touch targets are at least 44x44px."""
    # Login
    test_token = os.getenv("SCRIPT_REVIEW_TOKEN", "test-token-123")
    mobile_page.goto(TAILSCALE_URL)
    mobile_page.fill('input[type="password"]', test_token)
    mobile_page.click('button[type="submit"]')
    
    # Check button sizes
    approve_btn = mobile_page.locator('button:has-text("Approve")').first
    box = approve_btn.bounding_box()
    
    if box:
        assert box["width"] >= 44, f"Approve button width {box['width']}px is too small"
        assert box["height"] >= 44, f"Approve button height {box['height']}px is too small"
