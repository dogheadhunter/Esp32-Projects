# Automated UI Screenshot System - Implementation Plan

**Target Device:** Samsung Galaxy S24+  
**Viewport:** 412×915 (2.625x device scale)  
**Format:** JPG (Quality: 90)  
**Approach:** Fully automated with manual fallback  
**Type:** Living document (auto-updates on UI changes)

---

## Overview

Create a fully automated Playwright-based screenshot capture system that documents every UI state, component, and interaction in the script-review web app for UX examination and optimization on Samsung Galaxy S24+ screen size.

---

## System Architecture

### 1. Screenshot Capture Script (`capture_screenshots.py`)

**Technology:** Python + Playwright Async API  
**Location:** `tools/script-review-app/tests/ui/capture_screenshots.py`

**Key Features:**
- Samsung Galaxy S24+ viewport emulation (412×915)
- Mobile user agent and touch event support
- Automated navigation through all UI states
- JPG compression (90% quality for good size/quality balance)
- Accuracy-first timing (delays for animations/interactions)
- Metadata tracking (descriptions, timestamps, categories)
- Automatic INDEX.md generation
- Failed capture tracking for manual review

**Configuration:**
```python
VIEWPORT = {
    'width': 412,
    'height': 915,
    'deviceScaleFactor': 2.625,
    'isMobile': True,
    'hasTouch': True,
}

BASE_URL = "http://localhost:8000"
API_TOKEN = "your-secret-token-here"
OUTPUT_DIR = ".playwright-mcp/Images_of_working_UI"
JPG_QUALITY = 90

# Timing (accuracy over speed)
ANIMATION_DELAY = 1.0      # Wait for animations
INTERACTION_DELAY = 0.5    # Wait after clicks/interactions
MODAL_DELAY = 0.8          # Wait for modals to fully render
PAGE_LOAD_DELAY = 2.0      # Initial page load
```

---

## Screenshot Coverage Plan

### Phase 1: Main Interface (3 screenshots)
**Subfolder:** `01_main_views/`

1. **01_main_default.jpg**
   - Description: Main review interface - default state with pending scripts
   - Shows: Full page, header, stats, filters, script card, action buttons
   
2. **02_header_stats.jpg**
   - Description: Header showing app title and pending/approved/rejected counters
   - Shows: Stats bar with current counts
   
3. **03_script_card_full.jpg**
   - Description: Script review card with DJ name, category, content, and action buttons
   - Shows: Complete card structure with all elements

### Phase 2: Category-Specific Cards (6 screenshots)
**Subfolder:** `02_category_cards/`

1. **card_weather.jpg** - Weather script with temperature and conditions metadata
2. **card_story.jpg** - Story script with timeline and act information
3. **card_news.jpg** - News category card
4. **card_gossip.jpg** - Gossip category card
5. **card_music.jpg** - Music category card
6. **card_general.jpg** - General category card

**Process:** Filter by category → Wait for load → Capture → Reset to "All"

### Phase 3: Modal Dialogs (6+ screenshots)
**Subfolder:** `03_modals/`

1. **01_stats_modal_full.jpg**
   - Shows: Overview stats, category breakdown, DJ statistics, scrollable content
   
2. **02_rejection_modal_empty.jpg**
   - Shows: Initial state with dropdown, no selection
   
3. **03_rejection_modal_reason_selected.jpg**
   - Shows: Standard reason selected from dropdown
   
4. **04_rejection_modal_other_custom.jpg**
   - Shows: "Other" selected with custom comment field visible
   
5. **01_auth_modal_initial.jpg** (root level)
   - Shows: Authentication modal on first load
   
6. **Timeline modal** (if story scripts exist)
   - Shows: Active story timelines by period

### Phase 4: Filter States (8+ screenshots)
**Subfolder:** `04_filters/`

**Category Filters:**
1. **01_filter_category_weather_active.jpg**
2. **02_filter_category_story_active.jpg**
3. **03_filter_category_news_active.jpg**
4. **04_filter_category_gossip_active.jpg**
5. **05_filter_category_music_active.jpg**

**DJ Filters:**
6. **06_filter_dj_dropdown_open.jpg** - Dropdown expanded showing all DJs
7. **07_filter_dj_julie_selected.jpg** - Julie selected, filtered results

**Advanced Filters:**
8. **08_filter_advanced_panel_expanded.jpg** - Full advanced filters panel

### Phase 5: Interactive States (4+ screenshots)
**Subfolder:** `05_interactions/`

1. **01_gesture_swipe_right_indicator.jpg**
   - Shows: Swipe right in progress, green ✓ indicator visible
   
2. **02_gesture_swipe_left_indicator.jpg**
   - Shows: Swipe left in progress, red ✗ indicator visible
   
3. **03_button_approve_hover.jpg**
   - Shows: Approve button hover state
   
4. **04_button_reject_hover.jpg**
   - Shows: Reject button hover state

### Phase 6: Special States (2+ screenshots)
**Subfolder:** `06_special_states/`

1. **01_toast_success_approved.jpg**
   - Shows: Success toast notification after approval
   
2. **02_state_empty_no_scripts.jpg**
   - Shows: Empty state when all scripts reviewed (if achievable)
   
3. **Additional:** Loading states, error toasts (if triggered)

### Phase 7: Touch Target Compliance (1 screenshot)
**Subfolder:** `07_touch_targets/`

1. **01_touch_targets_highlighted.jpg**
   - Shows: All interactive elements outlined (44px minimum compliance)
   - Injected CSS overlays for visualization

---

## Automation Workflow

### Step 1: Setup & Authentication
```python
1. Launch browser with S24+ viewport
2. Navigate to localhost:8000
3. Wait 2 seconds for page load
4. Capture auth modal
5. Fill API token
6. Click Login
7. Wait 2 seconds for main interface
```

### Step 2: Capture Main Views
```python
1. Capture default main view
2. Capture header/stats section
3. Capture full script card
```

### Step 3: Cycle Through Categories
```python
For each category (Weather, Story, News, Gossip, Music, General):
    1. Click category filter button
    2. Wait 1 second for scripts to load
    3. Capture card with category-specific metadata
    4. Click "All" to reset
    5. Wait 0.5 seconds
```

### Step 4: Capture Modals
```python
Stats Modal:
    1. Click "📊 Stats" button
    2. Wait 0.8 seconds for modal render
    3. Capture full modal
    4. Click close button (×)
    5. Wait 0.5 seconds

Rejection Modal:
    1. Click "✗ Reject" button
    2. Wait 0.8 seconds
    3. Capture empty state
    4. Select standard reason from dropdown
    5. Capture with reason selected
    6. Select "Other" from dropdown
    7. Capture with custom field visible
    8. Click "Cancel"
```

### Step 5: Capture Filters
```python
Category Filters (5 iterations):
    For each: Click → Wait → Capture → Reset

DJ Dropdown:
    1. Focus dropdown
    2. Capture open state
    3. Select DJ
    4. Wait 1 second for filter
    5. Capture filtered view
    6. Reset to "All DJs"

Advanced Filters:
    1. Click toggle
    2. Wait 0.5 seconds
    3. Capture expanded panel
    4. Click toggle to collapse
```

### Step 6: Capture Interactions
```python
Swipe Gestures:
    1. Get card bounding box
    2. Simulate mouse drag right (partial)
    3. Wait 0.3 seconds mid-drag
    4. Capture with indicator
    5. Release mouse
    6. Repeat for left swipe

Button Hovers:
    1. Hover approve button
    2. Wait 0.2 seconds
    3. Capture
    4. Repeat for reject button
```

### Step 7: Capture Special States
```python
Toast Notification:
    1. Click approve button
    2. Wait 0.5 seconds (catch toast)
    3. Capture toast visible
    4. Wait 1 second for animation

Empty State (if possible):
    1. Check if "Pending: 0" in stats
    2. If yes, capture empty state
```

### Step 8: Touch Targets
```python
1. Inject CSS to highlight all interactive elements
2. Wait 0.5 seconds for render
3. Capture compliance visualization
4. Remove CSS overlays
```

### Step 9: Generate INDEX.md
```python
1. Compile all screenshot metadata
2. Generate markdown with embedded images
3. Organize by section with priorities
4. Include timestamps
5. List failed captures
6. Write to INDEX.md
```

---

## Metadata Structure

Each screenshot stores:
```python
{
    'filename': 'path/to/image.jpg',
    'description': 'Human-readable description',
    'timestamp': '2026-01-18T18:30:45.123456',
    'category': 'subfolder_name'
}
```

---

## INDEX.md Structure

```markdown
# Script Review App - UI Documentation
**Samsung Galaxy S24+ (412×915)**
**Last Updated:** 2026-01-18 18:30:45
**Total Screenshots:** 87

## 📊 Summary
- Device: Samsung Galaxy S24+
- Resolution: 412×915 (2.625x scale)
- Format: JPG (Quality: 90)
- Sections: 7
- Screenshots: 87

## 🖥️ Main Interface Views
**Priority:** 🔴 High
**Count:** 3 screenshots

### 1. Main review interface - default state
![Description](01_main_views/01_main_default.jpg)
*Captured: 2026-01-18T18:30:12.456789*

---

[... continues for all sections ...]

## ⚠️ Failed Captures
- **05_interactions/gesture_x.jpg**: Timeout waiting for element

---

## 🔄 Updating This Document
```bash
cd tools/script-review-app/tests/ui
python capture_screenshots.py
```
```

---

## File Organization

```
esp32-project/
├── .playwright-mcp/
│   └── Images_of_working_UI/              # Output directory
│       ├── INDEX.md                        # Auto-generated gallery
│       ├── .gitignore                      # Exclude JPGs from git
│       ├── 01_auth_modal_initial.jpg       # Root screenshots
│       ├── 01_main_views/
│       │   ├── 01_main_default.jpg
│       │   ├── 02_header_stats.jpg
│       │   └── 03_script_card_full.jpg
│       ├── 02_category_cards/
│       │   ├── card_weather.jpg
│       │   ├── card_story.jpg
│       │   └── ...
│       ├── 03_modals/
│       ├── 04_filters/
│       ├── 05_interactions/
│       ├── 06_special_states/
│       └── 07_touch_targets/
│
└── tools/script-review-app/tests/ui/
    ├── capture_screenshots.py              # Main automation script
    ├── README.md                           # Usage instructions
    └── SCREENSHOT_SYSTEM_PLAN.md           # This file
```

---

## Git Strategy

**Recommendation:** Exclude screenshot binaries from git, track structure

**.gitignore in Images_of_working_UI/:**
```gitignore
# Ignore all screenshot files (large binaries)
*.jpg
*.jpeg
*.png

# Keep the INDEX.md and folder structure
!INDEX.md
!.gitignore
!*/
```

**Benefits:**
- Keeps repository size manageable
- INDEX.md tracks changes (text diff-able)
- Screenshots regenerate locally
- Can store screenshots separately if needed

**Alternative:** Use Git LFS for binary tracking (if visual diffs needed)

---

## Manual Fallback Process

If automation fails for specific states:

### 1. Identify Failed Captures
Check console output or INDEX.md "Failed Captures" section

### 2. Use Playwright MCP Manually
```javascript
// Navigate to state
await page.click('specific-selector');
await page.waitForTimeout(800);

// Capture
await page.screenshot({
    path: 'Images_of_working_UI/subfolder/filename.jpg',
    type: 'jpeg',
    quality: 90
});
```

### 3. Update Metadata
Add entry to INDEX.md manually following the format

---

## Data Requirements

### Real Scripts Needed
- **Weather:** At least 1 pending script with weather metadata
- **Story:** At least 1 pending script with story timeline info
- **News:** At least 1 pending script
- **Gossip:** At least 1 pending script
- **Music:** At least 1 pending script
- **General:** At least 1 pending script

### Mock Script Creation
If category missing, create mock:

```bash
# Location: output/scripts/pending_review/[DJ Name]/
# Format: YYYY-MM-DD_HHMMSS_[DJ Name]_[Category].txt
```

Example mock weather script:
```json
{
    "content": "Good morning wasteland! Temperature is 85 degrees...",
    "metadata": {
        "dj": "Mr. New Vegas",
        "category": "weather",
        "timestamp": "2026-01-18T08:00:00",
        "word_count": 75,
        "weather_state": {
            "current_weather": "sunny",
            "temperature": 85,
            "is_emergency": false
        }
    }
}
```

---

## Timing Configuration Rationale

### Why Accuracy Over Speed?

| Delay Type | Duration | Reason |
|------------|----------|--------|
| Page Load | 2.0s | Ensure all JS/CSS loaded, API calls complete |
| Animation | 1.0s | Card transitions, modal open/close animations |
| Modal | 0.8s | Modal render + content population |
| Interaction | 0.5s | Button clicks, filter changes, UI updates |
| Hover | 0.2s | CSS transitions for hover states |

**Trade-off:** Full run takes ~15-20 minutes vs ~5 minutes with fast timing

**Benefit:** Near-zero failed captures, accurate visual states

---

## Expected Outcomes

### Success Metrics
- **Target:** 80-120 screenshots captured
- **Success Rate:** >95% (fewer than 5 failed captures)
- **Accuracy:** All UI states clearly visible, no mid-animation captures
- **Coverage:** Every major UI component documented

### Deliverables
1. **INDEX.md** - Complete visual gallery with descriptions
2. **Organized screenshots** - 7 categorized subfolders
3. **Metadata** - Timestamps and descriptions for each capture
4. **Failed capture report** - Any issues documented for manual review

---

## Future Enhancements

### Phase 2 Additions
- **Error states:** Trigger and capture API errors, validation errors
- **Edge cases:** Single script, last script, filter with zero results
- **Animations:** Capture mid-swipe states, card transitions
- **Accessibility:** Color contrast overlays, screen reader simulation
- **Responsive:** Capture at multiple breakpoints (tablet, desktop)

### Automation Improvements
- **Visual regression testing:** Compare screenshots between versions
- **Automated annotations:** Highlight changed elements
- **Performance metrics:** Capture alongside screenshots
- **CI/CD integration:** Auto-run on PR creation

---

## Running the System

### Prerequisites
```bash
# 1. Server running
cd tools/script-review-app
$env:SCRIPT_REVIEW_TOKEN="your-secret-token-here"
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 2. Playwright installed
pip install playwright
playwright install chromium

# 3. Test data present
# Ensure pending scripts exist in output/scripts/pending_review/
```

### Execution
```bash
cd tools/script-review-app/tests/ui
python capture_screenshots.py
```

### Output
```
============================================================
📸 UI Screenshot Capture System
Samsung Galaxy S24+ (412×915)
============================================================

🗑️  Clearing old screenshots...

📸 Capturing Main Views...
✓ Captured: 01_main_default.jpg
✓ Captured: 02_header_stats.jpg
✓ Captured: 03_script_card_full.jpg

📸 Capturing Category-Specific Cards...
✓ Captured: card_weather.jpg
✓ Captured: card_story.jpg
...

✅ Capture complete: 87 screenshots
⚠️  2 captures failed

📝 Generating INDEX.md...
✓ Generated INDEX.md with 87 screenshots

============================================================
📁 Screenshots saved to:
   C:\esp32-project\.playwright-mcp\Images_of_working_UI
📄 View INDEX.md for organized gallery
============================================================
```

---

## Maintenance Plan

### As UI Changes
1. Delete old screenshots: `shutil.rmtree(OUTPUT_DIR)`
2. Re-run capture script
3. Review new INDEX.md
4. Check for failed captures
5. Manually capture any failures
6. Commit INDEX.md to git (screenshots stay local)

### Regular Updates
- **After each UI PR:** Regenerate screenshots
- **Before UX review:** Ensure latest captures
- **After major refactor:** Full regeneration

### Version History
Track in git via INDEX.md timestamps:
```bash
git log --follow -- .playwright-mcp/Images_of_working_UI/INDEX.md
```

---

## Success Criteria

✅ **Complete** when:
- [ ] All 7 section folders populated
- [ ] 80-120 screenshots captured
- [ ] INDEX.md generated with all metadata
- [ ] <5 failed captures
- [ ] All priority 🔴 High sections complete
- [ ] Samsung S24+ viewport accurate (412×915)
- [ ] JPG quality acceptable for UX review
- [ ] Documentation clear and actionable

---

**Plan Status:** Ready for Implementation  
**Next Step:** Create `capture_screenshots.py` and execute  
**Est. Time:** 15-20 minutes per full capture  
**Maintenance:** Living document, regenerate on UI changes
