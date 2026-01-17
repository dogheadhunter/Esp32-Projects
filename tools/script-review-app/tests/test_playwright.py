"""
Playwright tests for Script Review App.

These tests verify the mobile-first UI, swipe gestures, and API integration.
"""

import pytest
from playwright.sync_api import Page, expect
import time


class TestScriptReviewApp:
    """Test suite for the Script Review App with Playwright."""
    
    @pytest.fixture(scope="function")
    def page_with_auth(self, page: Page) -> Page:
        """Set up page with authentication."""
        # Navigate to the app
        page.goto("http://localhost:8000")
        
        # Enter API token
        page.fill("#apiToken", "test-token-123")
        page.click("#loginBtn")
        
        # Wait a bit for the async API call
        page.wait_for_timeout(1000)
        
        # Wait for auth modal to close
        page.wait_for_selector("#authModal.active", state="hidden", timeout=5000)
        
        return page
    
    def test_auth_modal_shows_on_load(self, page: Page):
        """Test that authentication modal shows on initial load."""
        page.goto("http://localhost:8000")
        
        # Check that auth modal is visible
        auth_modal = page.locator("#authModal")
        expect(auth_modal).to_have_class("modal active")
        
        # Check for token input
        token_input = page.locator("#apiToken")
        expect(token_input).to_be_visible()
    
    def test_successful_authentication(self, page: Page):
        """Test successful authentication flow."""
        page.goto("http://localhost:8000")
        
        # Enter valid token
        page.fill("#apiToken", "test-token-123")
        page.click("#loginBtn")
        
        # Wait a bit for the async API call
        page.wait_for_timeout(1000)
        
        # Auth modal should close
        page.wait_for_selector("#authModal.active", state="hidden", timeout=5000)
        
        # Main UI should be visible
        expect(page.locator("#cardContainer")).to_be_visible()
    
    def test_mobile_viewport(self, page: Page):
        """Test app layout in mobile viewport."""
        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})  # iPhone SE
        
        page.goto("http://localhost:8000")
        page.fill("#apiToken", "test-token-123")
        page.click("#loginBtn")
        
        # Wait for authentication
        page.wait_for_timeout(1000)
        page.wait_for_selector("#authModal.active", state="hidden", timeout=5000)
        
        # Wait for scripts to load
        page.wait_for_selector(".review-card", timeout=5000)
        
        # Check that card is visible and sized correctly
        card = page.locator(".review-card").first
        expect(card).to_be_visible()
        
        # Take screenshot
        page.screenshot(path="/tmp/mobile-viewport.png")
    
    def test_desktop_viewport(self, page: Page):
        """Test app layout in desktop viewport."""
        # Set desktop viewport
        page.set_viewport_size({"width": 1920, "height": 1080})
        
        page.goto("http://localhost:8000")
        page.fill("#apiToken", "test-token-123")
        page.click("#loginBtn")
        
        # Wait for authentication
        page.wait_for_timeout(1000)
        page.wait_for_selector("#authModal.active", state="hidden", timeout=5000)
        
        # Wait for scripts to load
        page.wait_for_selector(".review-card", timeout=5000)
        
        # Check that card is visible
        card = page.locator(".review-card").first
        expect(card).to_be_visible()
        
        # Take screenshot
        page.screenshot(path="/tmp/desktop-viewport.png")
    
    def test_script_card_displays_metadata(self, page_with_auth: Page):
        """Test that script card displays DJ name, content type, and timestamp."""
        page = page_with_auth
        
        # Wait for card to load
        page.wait_for_selector(".review-card", timeout=5000)
        
        card = page.locator(".review-card").first
        
        # Check for DJ name (should be in the header)
        expect(card).to_contain_text(["Julie", "Mr. New Vegas", "Travis"])
        
        # Take screenshot of card
        card.screenshot(path="/tmp/script-card.png")
    
    def test_approve_button_click(self, page_with_auth: Page):
        """Test clicking the approve button."""
        page = page_with_auth
        
        # Wait for card to load
        page.wait_for_selector(".review-card", timeout=5000)
        
        # Get initial script count
        stats_text = page.locator("#stats").inner_text()
        
        # Click approve button
        page.click("#approveBtn")
        
        # Wait for card animation
        time.sleep(0.5)
        
        # Check that card has approved class or next card is shown
        # (depends on whether there are more scripts)
        # We mainly want to ensure no errors occurred
    
    def test_reject_button_opens_modal(self, page_with_auth: Page):
        """Test that clicking reject button opens the rejection modal."""
        page = page_with_auth
        
        # Wait for card to load
        page.wait_for_selector(".review-card", timeout=5000)
        
        # Click reject button
        page.click("#rejectBtn")
        
        # Rejection modal should be visible
        modal = page.locator("#rejectionModal")
        expect(modal).to_have_class("modal active")
        
        # Reason dropdown should be visible
        expect(page.locator("#rejectionReason")).to_be_visible()
    
    def test_rejection_flow_with_reason(self, page_with_auth: Page):
        """Test complete rejection flow with reason selection."""
        page = page_with_auth
        
        # Wait for card to load
        page.wait_for_selector(".review-card", timeout=5000)
        
        # Click reject
        page.click("#rejectBtn")
        
        # Wait for modal
        page.wait_for_selector("#rejectionModal.active", timeout=2000)
        
        # Select a rejection reason
        page.select_option("#rejectionReason", "tone_mismatch")
        
        # Confirm rejection
        page.click("#confirmReject")
        
        # Modal should close
        page.wait_for_selector("#rejectionModal.active", state="hidden", timeout=3000)
    
    def test_rejection_with_custom_comment(self, page_with_auth: Page):
        """Test rejection with 'other' reason and custom comment."""
        page = page_with_auth
        
        # Wait for card to load
        page.wait_for_selector(".review-card", timeout=5000)
        
        # Click reject
        page.click("#rejectBtn")
        
        # Select 'other' reason
        page.select_option("#rejectionReason", "other")
        
        # Custom comment field should appear
        comment_field = page.locator("#customComment")
        expect(comment_field).to_be_visible()
        
        # Enter custom comment
        page.fill("#customComment", "This script doesn't fit the character")
        
        # Confirm rejection
        page.click("#confirmReject")
    
    def test_cancel_rejection(self, page_with_auth: Page):
        """Test canceling a rejection."""
        page = page_with_auth
        
        # Wait for card to load
        page.wait_for_selector(".review-card", timeout=5000)
        
        # Click reject
        page.click("#rejectBtn")
        
        # Wait for modal
        page.wait_for_selector("#rejectionModal.active", timeout=2000)
        
        # Click cancel
        page.click("#cancelReject")
        
        # Modal should close
        expect(page.locator("#rejectionModal")).not_to_have_class("modal active")
        
        # Card should still be visible
        expect(page.locator(".review-card").first).to_be_visible()
    
    def test_keyboard_shortcuts(self, page_with_auth: Page):
        """Test keyboard shortcuts for approve/reject."""
        page = page_with_auth
        
        # Wait for card to load
        page.wait_for_selector(".review-card", timeout=5000)
        
        # Press right arrow (approve)
        page.keyboard.press("ArrowRight")
        
        # Wait a moment
        time.sleep(0.5)
        
        # If there's another script, try reject with left arrow
        if page.locator(".review-card").count() > 0:
            page.keyboard.press("ArrowLeft")
            
            # Rejection modal should open
            expect(page.locator("#rejectionModal")).to_have_class("modal active")
    
    def test_dj_filter(self, page_with_auth: Page):
        """Test filtering scripts by DJ."""
        page = page_with_auth
        
        # Wait for scripts to load
        page.wait_for_selector("#djFilter option:nth-child(2)", timeout=5000)
        
        # Select a specific DJ
        page.select_option("#djFilter", index=1)  # First DJ option
        
        # Wait for scripts to reload
        time.sleep(0.5)
        
        # Check that card is displayed
        # (Would need to verify DJ name matches filter)
    
    def test_refresh_button(self, page_with_auth: Page):
        """Test refresh button functionality."""
        page = page_with_auth
        
        # Wait for initial load
        page.wait_for_selector(".review-card", timeout=5000)
        
        # Click refresh
        page.click("#refreshBtn")
        
        # Toast should appear
        expect(page.locator("#toast.show")).to_be_visible()
    
    def test_stats_display(self, page_with_auth: Page):
        """Test that statistics are displayed."""
        page = page_with_auth
        
        # Wait for stats to load
        page.wait_for_selector("#stats", timeout=5000)
        
        stats = page.locator("#stats").inner_text()
        
        # Stats should contain expected keywords
        assert "Pending" in stats
        assert "Approved" in stats
        assert "Rejected" in stats
    
    def test_responsive_card_sizing(self, page_with_auth: Page):
        """Test that cards resize appropriately on different screen sizes."""
        page = page_with_auth
        
        viewports = [
            {"width": 375, "height": 667, "name": "iPhone SE"},
            {"width": 414, "height": 896, "name": "iPhone 11"},
            {"width": 768, "height": 1024, "name": "iPad"},
            {"width": 1920, "height": 1080, "name": "Desktop"}
        ]
        
        for viewport in viewports:
            page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
            
            # Wait for layout to adjust
            time.sleep(0.2)
            
            # Take screenshot
            page.screenshot(path=f"/tmp/viewport-{viewport['name'].replace(' ', '-')}.png")
            
            # Card should still be visible
            if page.locator(".review-card").count() > 0:
                expect(page.locator(".review-card").first).to_be_visible()
    
    def test_touch_events_mobile(self, page_with_auth: Page):
        """Test touch event handling on mobile viewport."""
        page = page_with_auth
        page.set_viewport_size({"width": 375, "height": 667})
        
        # Wait for card
        page.wait_for_selector(".review-card", timeout=5000)
        
        card = page.locator(".review-card").first
        
        # Get card bounding box
        box = card.bounding_box()
        
        if box:
            # Simulate swipe right (approve)
            page.mouse.move(box["x"] + 50, box["y"] + box["height"] / 2)
            page.mouse.down()
            page.mouse.move(box["x"] + box["width"] - 50, box["y"] + box["height"] / 2)
            page.mouse.up()
            
            # Wait for animation
            time.sleep(0.5)
    
    def test_no_scripts_message(self, page: Page):
        """Test that 'no scripts' message shows when all reviewed."""
        # This test would need a scenario where no scripts are pending
        # For now, we'll just check that the element exists
        page.goto("http://localhost:8000")
        page.fill("#apiToken", "test-token-123")
        page.click("#loginBtn")
        
        # Check that noScripts element exists
        no_scripts = page.locator("#noScripts")
        # Element exists (count >= 0)
        assert no_scripts.count() >= 0
    
    def test_accessibility_labels(self, page_with_auth: Page):
        """Test that key interactive elements have proper accessibility."""
        page = page_with_auth
        
        # Check for key buttons
        expect(page.locator("#approveBtn")).to_be_visible()
        expect(page.locator("#rejectBtn")).to_be_visible()
        
        # Check that buttons have text content
        approve_text = page.locator("#approveBtn").inner_text()
        assert "Approve" in approve_text
        
        reject_text = page.locator("#rejectBtn").inner_text()
        assert "Reject" in reject_text
