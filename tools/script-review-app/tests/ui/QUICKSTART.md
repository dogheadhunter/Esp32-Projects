# Quick Start Guide - Screenshot Capture System

## 🚀 Fast Setup (2 minutes)

### Step 1: Ensure Playwright browsers installed
```powershell
# Check if chromium is installed
playwright install chromium
```

### Step 2: Set API token
```powershell
$env:SCRIPT_REVIEW_TOKEN="your-secret-token-here"
```

### Step 3: Start the server (Terminal 1)
```powershell
cd tools/script-review-app
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 4: Run screenshot capture (Terminal 2)
```powershell
cd tools/script-review-app/tests/ui
python capture_screenshots.py
```

## ⏱️ Expected Results

**Execution Time:** 15-20 minutes  
**Screenshots:** 80-120 images  
**Output:** `.playwright-mcp/Images_of_working_UI/INDEX.md`

## 📊 Console Output Example

```
============================================================
📸 UI Screenshot Capture System
Samsung Galaxy S24+ (412×915)
============================================================

🗑️  Clearing old screenshots...

📸 Capturing Main Views...
✓ Captured: 01_main_views/01_main_default.jpg
✓ Captured: 01_main_views/02_header_stats.jpg
✓ Captured: 01_main_views/03_script_card_full.jpg

📸 Capturing Category-Specific Cards...
✓ Captured: 02_category_cards/card_weather.jpg
✓ Captured: 02_category_cards/card_story.jpg
✗ Failed: 02_category_cards/card_music.jpg - No music scripts available

📸 Capturing Modal Dialogs...
✓ Captured: 03_modals/01_stats_modal_full.jpg
...

📝 Generating INDEX.md...
✓ Generated INDEX.md with 87 screenshots

============================================================
✅ Capture complete: 87 screenshots
⚠️  2 captures failed

📁 Screenshots saved to:
   C:\esp32-project\.playwright-mcp\Images_of_working_UI
📄 View INDEX.md for organized gallery
============================================================
```

## 🔧 Troubleshooting

| Issue | Fix |
|-------|-----|
| "Connection refused" | Start server on port 8000 |
| "Auth failed" | Set correct `SCRIPT_REVIEW_TOKEN` |
| "No scripts found" | Add test scripts to `output/scripts/pending_review/` |
| "Browser not found" | Run `playwright install chromium` |

## 📁 View Results

```powershell
# Open the generated gallery
start .playwright-mcp/Images_of_working_UI/INDEX.md
```

## 🔄 Regenerate After UI Changes

Just re-run the script:
```powershell
cd tools/script-review-app/tests/ui
python capture_screenshots.py
```

Old screenshots are automatically cleared, INDEX.md regenerates.

---

**Full documentation:** See [README.md](README.md)
