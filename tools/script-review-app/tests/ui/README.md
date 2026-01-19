# UI Screenshot Capture System

Automated Playwright-based screenshot documentation system for the script-review-app. Captures comprehensive UI states optimized for Samsung Galaxy S24+ (412×915) viewport.

## Quick Start

```powershell
# 1. Start the server (in one terminal)
cd tools/script-review-app
$env:SCRIPT_REVIEW_TOKEN="your-secret-token-here"
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 2. Run screenshot capture (in another terminal)
cd tools/script-review-app/tests/ui
python capture_screenshots.py
```

## Prerequisites

### 1. Python Dependencies
```powershell
# Install Playwright
pip install playwright

# Install browser binaries
playwright install chromium
```

### 2. Server Running
The script-review-app must be running on `http://localhost:8000`

### 3. Authentication Token
Set environment variable:
```powershell
$env:SCRIPT_REVIEW_TOKEN="your-actual-token"
```

Or edit `capture_screenshots.py` directly:
```python
API_TOKEN = "your-actual-token"
```

### 4. Test Data
Ensure pending scripts exist in various categories:
- Weather scripts with metadata
- Story scripts with timeline info
- News, Gossip, Music, General scripts

**Location:** `output/scripts/pending_review/[DJ Name]/`

## Output

### Directory Structure
```
.playwright-mcp/Images_of_working_UI/
├── INDEX.md                              # Auto-generated gallery
├── .gitignore                            # Excludes JPGs from git
├── 01_auth_modal_initial.jpg             # Root screenshots
├── 01_main_views/
│   ├── 01_main_default.jpg
│   ├── 02_header_stats.jpg
│   └── 03_script_card_full.jpg
├── 02_category_cards/
│   ├── card_weather.jpg
│   ├── card_story.jpg
│   └── ...
├── 03_modals/
│   ├── 01_stats_modal_full.jpg
│   ├── 02_rejection_modal_empty.jpg
│   └── ...
├── 04_filters/
├── 05_interactions/
├── 06_special_states/
└── 07_touch_targets/
```

### INDEX.md
Automatically generated markdown gallery with:
- Embedded screenshot previews
- Descriptions and timestamps
- Organized by section/priority
- Failed capture report

## Configuration

Edit `capture_screenshots.py` to customize:

### Viewport (Samsung S24+)
```python
VIEWPORT = {
    'width': 412,
    'height': 915,
    'deviceScaleFactor': 2.625,
    'isMobile': True,
    'hasTouch': True,
}
```

### Timing (Accuracy vs Speed)
```python
ANIMATION_DELAY = 1.0      # CSS transitions, card filters
INTERACTION_DELAY = 0.5    # Button clicks, UI updates
MODAL_DELAY = 0.8          # Modal render + content load
PAGE_LOAD_DELAY = 2.0      # Initial page load, auth
```

**Trade-off:** Slower = more accurate captures, fewer failures

### Image Quality
```python
JPG_QUALITY = 90  # Range: 0-100 (90 = good balance)
```

## Execution Time

**Expected Duration:** 15-20 minutes  
**Target Screenshots:** 80-120 images  
**Success Rate:** >95% (fewer than 5 failures)

## Troubleshooting

### Server Not Running
**Error:** `ERR_CONNECTION_REFUSED`  
**Fix:** Start server on port 8000 before running script

### Authentication Failed
**Error:** Modal not closing, stuck on auth  
**Fix:** Verify `SCRIPT_REVIEW_TOKEN` matches server configuration

### No Scripts Found
**Error:** Failed captures for category cards  
**Fix:** Add test scripts to `output/scripts/pending_review/`

### Playwright Not Installed
**Error:** `playwright._impl._errors.Error`  
**Fix:** Run `playwright install chromium`

### Wrong Viewport Size
**Issue:** Screenshots don't match S24+ proportions  
**Fix:** Verify `VIEWPORT` config hasn't been modified

## Creating Mock Test Data

If categories missing, create mock scripts:

```json
// output/scripts/pending_review/Mr. New Vegas/2026-01-18_120000_Mr. New Vegas_weather.json
{
    "content": "Good morning wasteland! Temperature is 85 degrees with clear skies...",
    "metadata": {
        "dj": "Mr. New Vegas",
        "category": "weather",
        "timestamp": "2026-01-18T12:00:00",
        "word_count": 75,
        "weather_state": {
            "current_weather": "sunny",
            "temperature": 85,
            "is_emergency": false
        }
    }
}
```

## Manual Capture (Fallback)

For failed automated captures, use Playwright MCP manually:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        viewport={'width': 412, 'height': 915},
        device_scale_factor=2.625
    )
    page = context.new_page()
    page.goto('http://localhost:8000')
    
    # Navigate to specific state...
    page.click('button:text("Stats")')
    page.wait_for_timeout(800)
    
    # Capture
    page.screenshot(
        path='path/to/screenshot.jpg',
        type='jpeg',
        quality=90
    )
    
    browser.close()
```

## Updating Documentation

After UI changes:

```powershell
# Regenerate all screenshots
cd tools/script-review-app/tests/ui
python capture_screenshots.py

# Review new INDEX.md
start ../../.playwright-mcp/Images_of_working_UI/INDEX.md
```

## Git Strategy

Screenshots are **NOT** committed to git (large binaries).

**Tracked:**
- `INDEX.md` (text, diff-able)
- Directory structure
- This README

**Ignored:**
- All `.jpg` files (via `.gitignore`)

**Regenerate locally** when needed for UX review.

## Features Captured

### ✅ Automated
- Main interface views (3)
- Category-specific cards (6)
- Modal dialogs (4+)
- Filter states (8+)
- Button hover states (2)
- Touch target visualization (1)
- Special states (toasts, empty state)

### ⚠️ Manual Fallback
- Mid-gesture swipe indicators (complex state)
- Error toasts (requires triggering errors)
- Timeline modals (requires story scripts)

## Success Metrics

**Complete when:**
- [x] All 7 section folders populated
- [x] 80-120 screenshots captured
- [x] INDEX.md generated with metadata
- [x] <5 failed captures
- [x] Priority 🔴 High sections complete
- [x] Samsung S24+ viewport accurate
- [x] JPG quality acceptable for UX review

## Support

**Issues?** Check:
1. Server logs for errors
2. Console output for failed captures
3. INDEX.md "Failed Captures" section
4. Viewport configuration accuracy

**Questions?** See [SCREENSHOT_SYSTEM_PLAN.md](SCREENSHOT_SYSTEM_PLAN.md) for detailed implementation plan.

---

*Living documentation - regenerate after UI changes*
