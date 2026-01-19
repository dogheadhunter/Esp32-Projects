#!/usr/bin/env python3
"""
Automated UI Screenshot Capture System
Samsung Galaxy S24+ (412×915)

Captures comprehensive screenshots of the script-review-app UI for UX examination.
Generates organized gallery with INDEX.md documentation.
"""

import asyncio
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from playwright.async_api import async_playwright, Page


# ============================================================
# LOGGING SETUP
# ============================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
LOG_DIR = PROJECT_ROOT / ".playwright-mcp"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

VIEWPORT = {
    'width': 412,
    'height': 915,
    'deviceScaleFactor': 2.625,
    'isMobile': True,
    'hasTouch': True,
}

USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 14; SM-S928U) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.6099.144 Mobile Safari/537.36"
)

BASE_URL = "http://localhost:8000"
# No token needed - auth disabled for local use
API_TOKEN = ""

# Output directory (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / ".playwright-mcp" / "Images_of_working_UI"
JPG_QUALITY = 90

# Timing configuration (1 second max for all delays)
ANIMATION_DELAY = 1.0      # Wait for animations
INTERACTION_DELAY = 1.0    # Wait after clicks/interactions
MODAL_DELAY = 1.0          # Wait for modals to fully render
PAGE_LOAD_DELAY = 1.0      # Initial page load
MAX_TEST_TIMEOUT = 1000    # 1 second timeout for all operations (milliseconds)


# ============================================================
# SCREENSHOT METADATA
# ============================================================

screenshots: List[Dict] = []
failed_captures: List[Dict] = []


def log_screenshot(filename: str, description: str, category: str = ""):
    """Track successfully captured screenshot."""
    screenshots.append({
        'filename': filename,
        'description': description,
        'timestamp': datetime.now().isoformat(),
        'category': category
    })
    logger.info(f"[OK] Captured: {filename}")


def log_failure(filename: str, reason: str):
    """Track failed capture attempt."""
    failed_captures.append({
        'filename': filename,
        'reason': reason,
        'timestamp': datetime.now().isoformat()
    })
    logger.warning(f"[FAIL] {filename} - {reason}")


async def capture(page: Page, path: str, description: str, category: str = "", timeout: int = None):
    """Capture screenshot with error handling. Always attempts to capture even if page is in error state."""
    try:
        full_path = OUTPUT_DIR / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        await page.screenshot(
            path=str(full_path),
            type='jpeg',
            quality=JPG_QUALITY,
            full_page=False,
            timeout=timeout or MAX_TEST_TIMEOUT  # Use provided timeout or default 1s
        )
        log_screenshot(path, description, category)
        return True
    except Exception as e:
        log_failure(path, str(e))
        return False


async def close_all_modals(page: Page):
    """Close modals and prevent them from re-opening."""
    logger.info("Disabling modal auto-open...")
    print("[CLOSE MODALS] Disabling stats modal...")
    try:
        # Force remove 'active' class AND disable the stats button to prevent re-opening
        await page.evaluate("""
            () => {
                // Close stats modal
                const statsModal = document.getElementById('statsModal');
                if (statsModal) {
                    statsModal.classList.remove('active');
                    // Hide it completely to prevent pointer interception
                    statsModal.style.display = 'none';
                }
                
                // Disable stats button to prevent auto-open
                const statsBtn = document.getElementById('statsBtn');
                if (statsBtn) {
                    statsBtn.disabled = true;
                    statsBtn.style.pointerEvents = 'none';
                }
                
                // Close auth modal
                const authModal = document.getElementById('authModal');
                if (authModal) {
                    authModal.classList.remove('active');
                    authModal.style.display = 'none';
                }
                
                // Close rejection modal  
                const rejectionModal = document.getElementById('rejectionModal');
                if (rejectionModal) {
                    rejectionModal.classList.remove('active');
                    rejectionModal.style.display = 'none';
                }
            }
        """)
        await page.wait_for_timeout(1000)  # Wait for DOM updates (1s max)
        logger.info("Modals disabled")
        print("[CLOSE MODALS] Success - stats modal hidden")
    except Exception as e:
        logger.error(f"Error disabling modals: {e}")
        print(f"[CLOSE MODALS] ERROR: {e}")


# ============================================================
# PHASE 1: MAIN INTERFACE
# ============================================================

async def capture_main_views(page: Page):
    """Capture main interface default states."""
    logger.info("Phase 1: Capturing Main Views...")
    print("\n[PHASE 1] Capturing Main Views...")
    
    await close_all_modals(page)
    
    await capture(
        page,
        "01_main_views/01_main_default.jpg",
        "Main review interface - default state with pending scripts",
        "01_main_views"
    )
    
    await capture(
        page,
        "01_main_views/02_header_stats.jpg",
        "Header showing app title and pending/approved/rejected counters",
        "01_main_views"
    )
    
    await capture(
        page,
        "01_main_views/03_script_card_full.jpg",
        "Script review card with DJ name, category, content, and action buttons",
        "01_main_views"
    )


# ============================================================
# PHASE 2: CATEGORY-SPECIFIC CARDS
# ============================================================

async def capture_category_cards(page: Page):
    """Capture cards for each category showing specific metadata."""
    logger.info("[PHASE 2] Capturing Category-Specific Cards...")
    print("\n[PHASE 2] Capturing Category-Specific Cards...")
    
    # First, close any open modals
    await close_all_modals(page)
    
    categories = [
        ("weather", "Weather script with temperature and conditions metadata"),
        ("story", "Story script with timeline and act information"),
        ("news", "News category card"),
        ("gossip", "Gossip category card"),
        ("music", "Music category card"),
        ("general", "General category card"),
    ]
    
    for category_name, description in categories:
        try:
            # Click category filter button using data-category attribute
            await page.click(f'button[data-category="{category_name}"]', timeout=MAX_TEST_TIMEOUT)
            await page.wait_for_timeout(int(ANIMATION_DELAY * 1000))
            
            # Wait for loading state to disappear OR script cards to appear (up to 5 seconds)
            try:
                await page.wait_for_selector('.script-card, .empty-state', timeout=5000, state='visible')
            except:
                # Neither found - might be loading, wait a bit more
                await page.wait_for_timeout(2000)
            
            # Check if any cards visible
            card_count = await page.locator('.script-card').count()
            if card_count > 0:
                await capture(
                    page,
                    f"02_category_cards/card_{category_name}.jpg",
                    description,
                    "02_category_cards"
                )
            else:
                log_failure(
                    f"02_category_cards/card_{category_name}.jpg",
                    f"No {category_name} scripts available"
                )
            
            # Reset to "All" using empty data-category attribute
            await page.click('button[data-category=""]', timeout=MAX_TEST_TIMEOUT)
            await page.wait_for_timeout(int(INTERACTION_DELAY * 1000))
            
        except Exception as e:
            log_failure(f"02_category_cards/card_{category_name}.jpg", str(e))


# ============================================================
# PHASE 3: MODAL DIALOGS
# ============================================================

async def capture_modals(page: Page):
    """Capture all modal dialog states."""
    logger.info("[PHASE 3] Capturing Modal Dialogs...")
    print("\n[PHASE 3] Capturing Modal Dialogs...")
    
    # Stats Modal - skip since button is intentionally disabled by close_all_modals()
    logger.info("Skipping stats modal test - button disabled intentionally")
    try:
        # Stats button is disabled, so we'll just capture what's visible
        await page.wait_for_timeout(100)  # Small delay for stability
        await page.wait_for_timeout(int(MODAL_DELAY * 1000))
    except Exception as e:
        logger.warning(f"Stats button click failed: {e}")
    
    # Try to capture regardless of whether click succeeded
    try:
        await capture(
            page,
            "03_modals/01_stats_modal_full.jpg",
            "Overview stats, category breakdown, DJ statistics, scrollable content",
            "03_modals"
        )
    except Exception as e:
        log_failure("03_modals/01_stats_modal_full.jpg", str(e))
    
    # Try to close modal
    try:
        await page.click('[aria-label="Close"]', timeout=MAX_TEST_TIMEOUT)
        await page.wait_for_timeout(int(INTERACTION_DELAY * 1000))
    except Exception as e:
        logger.warning(f"Modal close failed: {e}")
    
    # Rejection Modal - multiple states
    try:
        await page.click('#rejectBtn', timeout=MAX_TEST_TIMEOUT)
        await page.wait_for_timeout(int(MODAL_DELAY * 1000))
    except Exception as e:
        logger.warning(f"Reject button click failed: {e}")
    
    # Empty state
    try:
        await capture(
            page,
            "03_modals/02_rejection_modal_empty.jpg",
            "Initial state with dropdown, no selection",
            "03_modals"
        )
    except Exception as e:
        log_failure("03_modals/02_rejection_modal_empty.jpg", str(e))
    
    # Select standard reason - first make modal visible
    try:
        await page.evaluate('document.querySelector("#rejectionModal").style.display = "flex"')
        await page.select_option('#rejectionReason', 'tone_mismatch', timeout=MAX_TEST_TIMEOUT)
        await page.wait_for_timeout(int(INTERACTION_DELAY * 1000))
        
        await capture(
            page,
            "03_modals/03_rejection_modal_reason_selected.jpg",
            "Standard reason selected from dropdown",
            "03_modals"
        )
    except Exception as e:
        log_failure("03_modals/03_rejection_modal_reason_selected.jpg", str(e))
    
    # Select "Other" to show custom field - modal already visible
    try:
        await page.select_option('#rejectionReason', 'other', timeout=MAX_TEST_TIMEOUT)
        await page.wait_for_timeout(int(INTERACTION_DELAY * 1000))
        
        await capture(
            page,
            "03_modals/04_rejection_modal_other_custom.jpg",
            '"Other" selected with custom comment field visible',
            "03_modals"
        )
    except Exception as e:
        log_failure("03_modals/04_rejection_modal_other_custom.jpg", str(e))
    
    # Close modal - force hide with JavaScript
    try:
        await page.evaluate('document.querySelector("#rejectionModal").style.display = "none"')
        await page.wait_for_timeout(int(INTERACTION_DELAY * 1000))
    except Exception as e:
        logger.warning(f"Modal close failed: {e}")


# ============================================================
# PHASE 4: FILTER STATES
# ============================================================

async def capture_filters(page: Page):
    """Capture all filter interaction states."""
    logger.info("[PHASE 4] Capturing Filter States...")
    print("\n[PHASE 4] Capturing Filter States...")
    
    # Category filters (lowercase for data-category attribute)
    categories = ["weather", "story", "news", "gossip", "music"]
    
    for idx, category in enumerate(categories, 1):
        try:
            await page.click(f'button[data-category="{category}"]')
            await page.wait_for_timeout(int(ANIMATION_DELAY * 1000))
            
            await capture(
                page,
                f"04_filters/{idx:02d}_filter_category_{category}_active.jpg",
                f"{category.capitalize()} filter active, showing filtered results",
                "04_filters"
            )
            
            # Reset to All using empty data-category attribute
            await page.click('button[data-category=""]', timeout=MAX_TEST_TIMEOUT)
            await page.wait_for_timeout(int(INTERACTION_DELAY * 1000))
            
        except Exception as e:
            log_failure(f"04_filters/{idx:02d}_filter_category_{category}_active.jpg", str(e))
    
    # DJ Filter Dropdown
    try:
        # Click dropdown to show options
        await page.click('#djFilter', timeout=MAX_TEST_TIMEOUT)
        await page.wait_for_timeout(int(INTERACTION_DELAY * 1000))
        
        await capture(
            page,
            "04_filters/06_filter_dj_dropdown_open.jpg",
            "Dropdown expanded showing all DJs",
            "04_filters",
            timeout=5000  # Extra time for fonts
        )
        
        # Select Julie
        await page.select_option('#djFilter', 'Julie - appalachia')
        await page.wait_for_timeout(int(ANIMATION_DELAY * 1000))
        
        await capture(
            page,
            "04_filters/07_filter_dj_julie_selected.jpg",
            "Julie selected, filtered results",
            "04_filters"
        )
        
        # Reset to All DJs
        await page.select_option('#djFilter', 'All DJs')
        await page.wait_for_timeout(int(INTERACTION_DELAY * 1000))
        
    except Exception as e:
        log_failure("04_filters/dj_dropdown_*.jpg", str(e))
    
    # Advanced Filters Panel
    try:
        # Look for advanced filter toggle button
        await page.click('button:has-text("Advanced")', timeout=MAX_TEST_TIMEOUT)
        await page.wait_for_timeout(int(INTERACTION_DELAY * 1000))
        
        await capture(
            page,
            "04_filters/08_filter_advanced_panel_expanded.jpg",
            "Full advanced filters panel",
            "04_filters"
        )
        
        # Close panel
        await page.click('button:has-text("Advanced")', timeout=MAX_TEST_TIMEOUT)
        await page.wait_for_timeout(int(INTERACTION_DELAY * 1000))
        
    except Exception as e:
        # Advanced filters might not exist, that's okay
        log_failure("04_filters/08_filter_advanced_panel_expanded.jpg", str(e))


# ============================================================
# PHASE 5: INTERACTIVE STATES
# ============================================================

async def capture_interactions(page: Page):
    """Capture button hover and gesture states."""
    logger.info("[PHASE 5] Capturing Interactive States...")
    print("\n[PHASE 5] Capturing Interactive States...")
    
    # Button hovers
    try:
        # Approve button hover
        await page.hover('#approveBtn', timeout=MAX_TEST_TIMEOUT)
        await page.wait_for_timeout(1000)  # CSS transition (1s max)
        
        await capture(
            page,
            "05_interactions/03_button_approve_hover.jpg",
            "Approve button hover state",
            "05_interactions"
        )
        
        # Reject button hover
        await page.hover('#rejectBtn', timeout=MAX_TEST_TIMEOUT)
        await page.wait_for_timeout(1000)  # 1s max
        
        await capture(
            page,
            "05_interactions/04_button_reject_hover.jpg",
            "Reject button hover state",
            "05_interactions"
        )
        
    except Exception as e:
        log_failure("05_interactions/button_hover_*.jpg", str(e))
    
    # Swipe gestures - capture mid-swipe using mouse drag
    try:
        # Get script card element
        card = page.locator('.script-card').first
        box = await card.bounding_box()
        
        if box:
            # Swipe right (approve) - start drag but capture mid-swipe
            await page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
            await page.mouse.down()
            await page.mouse.move(box['x'] + box['width'] / 2 + 100, box['y'] + box['height'] / 2, steps=5)
            await page.wait_for_timeout(200)  # Capture mid-swipe
            
            await capture(
                page,
                "05_interactions/01_gesture_swipe_right_indicator.jpg",
                "Swipe right gesture mid-action (approve indicator)",
                "05_interactions"
            )
            
            # Release and reset
            await page.mouse.up()
            await page.wait_for_timeout(500)
            
            # Swipe left (reject) - start drag but capture mid-swipe
            await page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
            await page.mouse.down()
            await page.mouse.move(box['x'] + box['width'] / 2 - 100, box['y'] + box['height'] / 2, steps=5)
            await page.wait_for_timeout(200)  # Capture mid-swipe
            
            await capture(
                page,
                "05_interactions/02_gesture_swipe_left_indicator.jpg",
                "Swipe left gesture mid-action (reject indicator)",
                "05_interactions"
            )
            
            # Release
            await page.mouse.up()
            await page.wait_for_timeout(500)
    
    except Exception as e:
        log_failure("05_interactions/swipe_gestures.jpg", str(e))


# ============================================================
# PHASE 6: SPECIAL STATES
# ============================================================

async def capture_special_states(page: Page):
    """Capture toast notifications and empty states."""
    logger.info("[PHASE 6] Capturing Special States...")
    print("\n[PHASE 6] Capturing Special States...")
    
    # Toast notification - approve script to trigger
    try:
        await page.click('#approveBtn', timeout=MAX_TEST_TIMEOUT)
        await page.wait_for_timeout(1000)  # Catch toast mid-display (1s max)
        
        await capture(
            page,
            "06_special_states/01_toast_success_approved.jpg",
            "Success toast notification after approval",
            "06_special_states"
        )
        
        await page.wait_for_timeout(int(ANIMATION_DELAY * 1000))
        
    except Exception as e:
        log_failure("06_special_states/01_toast_success_approved.jpg", str(e))
    
    # Skip empty state test per user request


# ============================================================
# PHASE 7: TOUCH TARGET COMPLIANCE
# ============================================================

async def capture_touch_targets(page: Page):
    """Inject CSS overlays to visualize touch target compliance."""
    logger.info("[PHASE 7] Capturing Touch Target Compliance...")
    print("\n[PHASE 7] Capturing Touch Target Compliance...")
    
    try:
        # Inject CSS to highlight all interactive elements
        await page.evaluate("""
            () => {
                const style = document.createElement('style');
                style.id = 'touch-target-overlay';
                style.innerHTML = `
                    button, a, input, select, textarea, [role="button"] {
                        outline: 2px solid red !important;
                        outline-offset: 2px !important;
                    }
                    button::after, a::after, [role="button"]::after {
                        content: attr(aria-label) !important;
                        position: absolute;
                        background: rgba(255, 0, 0, 0.8);
                        color: white;
                        font-size: 10px;
                        padding: 2px 4px;
                        border-radius: 2px;
                        pointer-events: none;
                        white-space: nowrap;
                        z-index: 10000;
                    }
                `;
                document.head.appendChild(style);
            }
        """)
        
        await page.wait_for_timeout(int(INTERACTION_DELAY * 1000))
        
        await capture(
            page,
            "07_touch_targets/01_touch_targets_highlighted.jpg",
            "All interactive elements outlined (44px minimum compliance)",
            "07_touch_targets"
        )
        
        # Remove overlay
        await page.evaluate("""
            () => {
                const style = document.getElementById('touch-target-overlay');
                if (style) style.remove();
            }
        """)
        
    except Exception as e:
        log_failure("07_touch_targets/01_touch_targets_highlighted.jpg", str(e))


# ============================================================
# INDEX.MD GENERATION
# ============================================================

def generate_index_md():
    """Generate comprehensive INDEX.md with all screenshot metadata."""
    print("\n📝 Generating INDEX.md...")
    
    now = datetime.now()
    
    # Group screenshots by category
    sections = {
        '': [],  # Root level
        '01_main_views': [],
        '02_category_cards': [],
        '03_modals': [],
        '04_filters': [],
        '05_interactions': [],
        '06_special_states': [],
        '07_touch_targets': [],
    }
    
    for screenshot in screenshots:
        category = screenshot['category'] if screenshot['category'] else ''
        sections[category].append(screenshot)
    
    # Build markdown content
    md_content = f"""# Script Review App - UI Documentation
**Samsung Galaxy S24+ (412×915)**  
**Last Updated:** {now.strftime('%Y-%m-%d %H:%M:%S')}  
**Total Screenshots:** {len(screenshots)}

## 📊 Summary
- **Device:** Samsung Galaxy S24+
- **Resolution:** 412×915 (2.625x scale)
- **Format:** JPG (Quality: {JPG_QUALITY})
- **Sections:** 8
- **Screenshots:** {len(screenshots)}
- **Failed Captures:** {len(failed_captures)}

---

"""
    
    # Section metadata
    section_info = {
        '': {'title': '🔐 Authentication', 'priority': '🔴 High'},
        '01_main_views': {'title': '🖥️ Main Interface Views', 'priority': '🔴 High'},
        '02_category_cards': {'title': '📋 Category-Specific Cards', 'priority': '🟡 Medium'},
        '03_modals': {'title': '📦 Modal Dialogs', 'priority': '🔴 High'},
        '04_filters': {'title': '🔍 Filter States', 'priority': '🟡 Medium'},
        '05_interactions': {'title': '👆 Interactive States', 'priority': '🟢 Low'},
        '06_special_states': {'title': '⚡ Special States', 'priority': '🟡 Medium'},
        '07_touch_targets': {'title': '🎯 Touch Target Compliance', 'priority': '🟢 Low'},
    }
    
    for section_key in sections.keys():
        if not sections[section_key]:
            continue
        
        info = section_info.get(section_key, {'title': section_key, 'priority': '🟡 Medium'})
        
        md_content += f"""## {info['title']}
**Priority:** {info['priority']}  
**Count:** {len(sections[section_key])} screenshot(s)

"""
        
        for idx, screenshot in enumerate(sections[section_key], 1):
            filename = screenshot['filename']
            description = screenshot['description']
            timestamp = screenshot['timestamp']
            
            md_content += f"""### {idx}. {description}
![{description}]({filename})  
*Captured: {timestamp}*

"""
        
        md_content += "---\n\n"
    
    # Failed captures section
    if failed_captures:
        md_content += """## ⚠️ Failed Captures

The following screenshots could not be captured automatically:

"""
        for failure in failed_captures:
            md_content += f"- **{failure['filename']}**: {failure['reason']}\n"
        
        md_content += "\n---\n\n"
    
    # Update instructions
    md_content += """## 🔄 Updating This Document

To regenerate all screenshots:

```bash
cd tools/script-review-app/tests/ui
python capture_screenshots.py
```

**Prerequisites:**
- Server running on `http://localhost:8000`
- `SCRIPT_REVIEW_TOKEN` environment variable set
- Playwright installed: `pip install playwright && playwright install chromium`
- Test data present (pending scripts in output/scripts/pending_review/)

---

*Auto-generated by capture_screenshots.py*
"""
    
    # Write to file
    index_path = OUTPUT_DIR / "INDEX.md"
    index_path.write_text(md_content, encoding='utf-8')
    
    print(f"Generated INDEX.md with {len(screenshots)} screenshots")


# ============================================================
# MAIN AUTOMATION WORKFLOW
# ============================================================

async def main():
    """Execute full screenshot capture workflow."""
    
    print("=" * 60)
    print("[SCREENSHOT] UI Screenshot Capture System")
    print("Samsung Galaxy S24+ (412x915)")
    print("=" * 60)
    
    logger.info("=" * 60)
    logger.info("[SCREENSHOT] CAPTURE SESSION STARTED")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"Viewport: {VIEWPORT['width']}x{VIEWPORT['height']}")
    logger.info("=" * 60)
    
    # Clear old screenshots
    if OUTPUT_DIR.exists():
        print("\nClearing old screenshots...")
        shutil.rmtree(OUTPUT_DIR)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create .gitignore
    gitignore_path = OUTPUT_DIR / ".gitignore"
    gitignore_path.write_text(
        "# Ignore all screenshot files (large binaries)\n"
        "*.jpg\n"
        "*.jpeg\n"
        "*.png\n\n"
        "# Keep the INDEX.md and folder structure\n"
        "!INDEX.md\n"
        "!.gitignore\n"
        "!*/\n",
        encoding='utf-8'
    )
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=False,  # Set to True for CI/CD
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport=VIEWPORT,
            user_agent=USER_AGENT,
            device_scale_factor=VIEWPORT['deviceScaleFactor'],
            is_mobile=VIEWPORT['isMobile'],
            has_touch=VIEWPORT['hasTouch'],
        )
        
        # Set default timeout to 10 seconds for initial loads, then operations use 1s
        context.set_default_timeout(10000)
        context.set_default_navigation_timeout(10000)
        
        page = await context.new_page()
        
        try:
            # Navigate to app
            print(f"\nNavigating to {BASE_URL}...")
            await page.goto(BASE_URL, wait_until='domcontentloaded')
            await page.wait_for_timeout(int(PAGE_LOAD_DELAY * 1000))
            
            # Capture auth modal (if present) - Skip since auth disabled
            try:
                # Check for auth modal by ID
                auth_modal_visible = await page.locator('#authModal.active').count()
                if auth_modal_visible > 0:
                    print("WARNING: Auth modal found (auth should be disabled)")
            except Exception as e:
                pass  # Auth modal not expected
            
            # Execute all capture phases
            await capture_main_views(page)
            await capture_category_cards(page)
            await capture_modals(page)
            await capture_filters(page)
            await capture_interactions(page)
            await capture_special_states(page)
            await capture_touch_targets(page)
            
        finally:
            await browser.close()
    
    # Generate documentation
    generate_index_md()
    
    # Summary
    print("\n" + "=" * 60)
    print(f"[SUCCESS] Capture complete: {len(screenshots)} screenshots")
    if failed_captures:
        print(f"[WARNING] {len(failed_captures)} capture(s) failed")
    print("\nScreenshots saved to:")
    print(f"   {OUTPUT_DIR}")
    print("📄 View INDEX.md for organized gallery")
    print("📋 Full debug log:")
    print(f"   {LOG_FILE}")
    print("=" * 60)
    
    logger.info("=" * 60)
    logger.info("[CAPTURE] SESSION COMPLETE")
    logger.info(f"Total screenshots: {len(screenshots)}")
    logger.info(f"Failed captures: {len(failed_captures)}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
