# Comprehensive Local Testing Plan

## Overview
This document provides a step-by-step testing plan for validating the entire system integration on your local machine, including the broadcast engine, ChromaDB, weather system, story system, and mobile UI.

---

## Prerequisites

### Required Software
- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] Ollama installed and running
- [ ] ChromaDB dependencies installed
- [ ] Android phone with Chrome browser (for mobile testing)
- [ ] Same WiFi network for phone and development machine

### Environment Setup
```bash
# Install Python dependencies
cd /path/to/Esp32-Projects/tools/script-generator
pip install -r requirements.txt

# Install web UI dependencies (if any)
cd ../script-review-app/backend
pip install fastapi uvicorn python-multipart

# Verify Ollama is running
ollama list
# Should show available models like llama2, mistral, etc.
```

---

## Phase 1: Backend Systems Testing

### 1.1 Weather System Validation ✅

**Objective**: Verify weather simulation, calendars, and continuity work correctly.

#### Test Steps:
- [ ] **Weather Calendar Generation**
  ```bash
  cd tools/script-generator
  python -m pytest tests/test_weather_simulator.py -v
  ```
  **Success Criteria**: All 18 tests pass

- [ ] **Regional Climate Verification**
  ```bash
  python -c "from regional_climate import CLIMATES; print(CLIMATES.keys())"
  ```
  **Success Criteria**: Shows Appalachia, Mojave, Commonwealth

- [ ] **Manual Weather Override**
  ```bash
  python tools/script-generator/set_weather.py --region Appalachia --type rad_storm --duration 2 --temp 68
  ```
  **Success Criteria**: Weather override confirmed, no errors

- [ ] **Weather History Query**
  ```bash
  python tools/script-generator/query_weather_history.py --region Appalachia --stats
  ```
  **Success Criteria**: Shows weather statistics

### 1.2 Story System Validation ✅

**Objective**: Verify story extraction, scheduling, and timeline management.

#### Test Steps:
- [ ] **Story System Unit Tests**
  ```bash
  cd tools/script-generator
  python -m pytest tests/test_story_*.py -v
  ```
  **Success Criteria**: All 122 story system tests pass

- [ ] **DJ Profiles Loading**
  ```bash
  python -c "from story_system.data.dj_personalities import load_dj_profiles; print(len(load_dj_profiles()))"
  ```
  **Success Criteria**: Shows 4 DJs loaded

- [ ] **Lore Validation Check**
  ```bash
  python -c "from story_system.lore_validator import LoreValidator; v = LoreValidator(); print(v.validate_faction_reference('Brotherhood of Steel', 2102))"
  ```
  **Success Criteria**: Returns validation result

### 1.3 Broadcast Engine Integration ✅

**Objective**: Verify broadcast engine integrates weather and story systems correctly.

#### Test Steps:
- [ ] **Core Broadcast Engine Tests**
  ```bash
  cd tools/script-generator
  python -m pytest tests/ -k "not chromadb" -v
  ```
  **Success Criteria**: All non-ChromaDB tests pass (85+ tests)

- [ ] **Broadcast Engine Initialization**
  ```bash
  python -c "from broadcast_engine import BroadcastEngine; engine = BroadcastEngine('Julie', 2102); print(f'Weather: {engine.weather_simulator is not None}, Stories: {engine.story_scheduler is not None}')"
  ```
  **Success Criteria**: Shows both systems initialized (True, True)

- [ ] **Generate Test Broadcast**
  ```bash
  python broadcast_engine.py --dj Julie --segments 3 --test-mode
  ```
  **Success Criteria**: Generates 3 segments without errors

---

## Phase 2: ChromaDB Integration Testing

### 2.1 ChromaDB Setup ✅

**Objective**: Verify ChromaDB is properly configured and accessible.

#### Test Steps:
- [ ] **ChromaDB Connection Test**
  ```bash
  python -c "import chromadb; client = chromadb.Client(); print('ChromaDB connected')"
  ```
  **Success Criteria**: Prints "ChromaDB connected" without errors

- [ ] **Collection Verification**
  ```bash
  python -c "
  import chromadb
  client = chromadb.Client()
  collections = client.list_collections()
  print(f'Collections: {[c.name for c in collections]}')
  "
  ```
  **Success Criteria**: Shows list of collections

- [ ] **Add Test Content**
  ```bash
  python -c "
  import chromadb
  client = chromadb.Client()
  collection = client.get_or_create_collection('test_fallout')
  collection.add(
      documents=['The Brotherhood of Steel is a techno-religious organization'],
      metadatas=[{'faction': 'Brotherhood of Steel', 'year': 2102}],
      ids=['test_1']
  )
  print('Test content added')
  "
  ```
  **Success Criteria**: Content added successfully

### 2.2 Story Extraction from ChromaDB ✅

**Objective**: Verify story extraction works with real ChromaDB data.

#### Test Steps:
- [ ] **Extract Stories from ChromaDB**
  ```bash
  python -c "
  from story_system.story_extractor import StoryExtractor
  import chromadb
  
  client = chromadb.Client()
  extractor = StoryExtractor(client, 'test_fallout')
  stories = extractor.extract_stories(max_stories=5)
  print(f'Extracted {len(stories)} stories')
  for s in stories:
      print(f'  - {s.title}: {len(s.acts)} acts')
  "
  ```
  **Success Criteria**: Extracts stories with acts

- [ ] **Validate Extracted Story Structure**
  ```bash
  python -c "
  from story_system.story_extractor import StoryExtractor
  import chromadb
  
  client = chromadb.Client()
  extractor = StoryExtractor(client, 'test_fallout')
  stories = extractor.extract_stories(max_stories=1)
  if stories:
      story = stories[0]
      print(f'Story: {story.title}')
      print(f'Acts: {[act.type for act in story.acts]}')
      print(f'Timeline: {story.timeline}')
  "
  ```
  **Success Criteria**: Shows story with proper act structure

---

## Phase 3: Web UI Backend Testing

### 3.1 FastAPI Backend Startup ✅

**Objective**: Verify the web UI backend starts and endpoints respond correctly.

#### Test Steps:
- [ ] **Start Backend Server**
  ```bash
  cd tools/script-review-app/backend
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
  ```
  **Success Criteria**: Server starts without errors, shows "Application startup complete"

- [ ] **Test Health Endpoint** (in new terminal)
  ```bash
  curl http://localhost:8000/
  ```
  **Success Criteria**: Returns welcome message

- [ ] **Test DJ Endpoint**
  ```bash
  curl http://localhost:8000/api/djs
  ```
  **Success Criteria**: Returns JSON array of DJs

- [ ] **Test Scripts Endpoint**
  ```bash
  curl "http://localhost:8000/api/scripts?status=pending"
  ```
  **Success Criteria**: Returns JSON array of scripts

- [ ] **Test Category Filtering**
  ```bash
  curl "http://localhost:8000/api/scripts?category=Weather"
  ```
  **Success Criteria**: Returns only weather scripts

- [ ] **Test Statistics Endpoint**
  ```bash
  curl http://localhost:8000/api/stats/detailed
  ```
  **Success Criteria**: Returns statistics JSON with overview, categories, djs

### 3.2 Generate Test Scripts ✅

**Objective**: Create sample scripts for testing the UI.

#### Test Steps:
- [ ] **Generate Weather Scripts**
  ```bash
  cd tools/script-generator
  python -c "
  from broadcast_engine import BroadcastEngine
  engine = BroadcastEngine('Julie', 2102)
  # Generate 5 weather segments
  for i in range(5):
      segment = engine.generate_next_segment()
      print(f'Generated: {segment.content_type}')
  "
  ```
  **Success Criteria**: Generates 5 weather segments

- [ ] **Generate Story Scripts**
  ```bash
  python -c "
  from broadcast_engine import BroadcastEngine
  engine = BroadcastEngine('Julie', 2102, enable_story_system=True)
  # Generate 5 story segments
  for i in range(10):
      segment = engine.generate_next_segment()
      if segment.content_type == 'story':
          print(f'Generated story: {segment.metadata}')
  "
  ```
  **Success Criteria**: Generates story segments

- [ ] **Verify Scripts in Storage**
  ```bash
  curl http://localhost:8000/api/scripts | python -m json.tool | grep -c "id"
  ```
  **Success Criteria**: Shows count > 0

---

## Phase 4: Web UI Frontend Testing (Desktop)

### 4.1 Basic UI Functionality ✅

**Objective**: Verify the UI loads and basic features work in desktop Chrome.

#### Test Steps:
- [ ] **Open UI in Browser**
  - Navigate to `http://localhost:8000`
  - **Success Criteria**: Page loads, no console errors

- [ ] **Verify UI Elements Present**
  - [ ] DJ selector dropdown visible
  - [ ] Category filter pills visible (All, Weather, Story, News, Gossip, Music)
  - [ ] Script card visible with content
  - [ ] Action buttons visible (Timeline, Filters, Stats)
  - **Success Criteria**: All elements render correctly

- [ ] **Test DJ Selection**
  - Select different DJs from dropdown
  - **Success Criteria**: Scripts reload, filtered by DJ

- [ ] **Test Category Filtering**
  - Click "Weather" category pill
  - **Success Criteria**: Only weather scripts shown, pill becomes active

- [ ] **Test Keyboard Navigation**
  - Press Left Arrow key
  - Press Right Arrow key
  - **Success Criteria**: Scripts navigate (reject/approve)

### 4.2 Advanced Features Testing ✅

#### Test Steps:
- [ ] **Test Advanced Filters Panel**
  - Click "🔍 Filters" button
  - Panel should expand
  - **Success Criteria**: Filter panel visible with status, date, weather type filters

- [ ] **Test Status Filter**
  - Select "Approved" from status dropdown
  - Click "Apply Filters"
  - **Success Criteria**: Only approved scripts shown

- [ ] **Test Date Range Filter**
  - Set date_from to 1 week ago
  - Set date_to to today
  - Click "Apply Filters"
  - **Success Criteria**: Scripts filtered by date range

- [ ] **Test Weather Type Filter**
  - Select "Weather" category
  - In advanced filters, select "Sunny"
  - Click "Apply Filters"
  - **Success Criteria**: Only sunny weather scripts shown

- [ ] **Test Statistics Dashboard**
  - Click "📊 Stats" button
  - **Success Criteria**: Modal opens showing overview, category breakdown, DJ breakdown

- [ ] **Test Story Timeline View**
  - Click "📚 Story Timelines" button (if visible)
  - **Success Criteria**: Modal opens showing grouped story timelines

---

## Phase 5: Mobile UI Testing (Android Chrome)

### 5.1 Setup Mobile Testing Environment ✅

**Objective**: Connect Android phone to local backend for testing.

#### Test Steps:
- [ ] **Find Local Machine IP Address**
  ```bash
  # On Linux/Mac
  ifconfig | grep "inet " | grep -v 127.0.0.1
  
  # On Windows
  ipconfig | findstr IPv4
  ```
  **Note**: Use this IP for mobile testing (e.g., 192.168.1.100)

- [ ] **Ensure Backend Accessible from Network**
  - Backend should be started with `--host 0.0.0.0`
  - Verify firewall allows port 8000

- [ ] **Test Connection from Phone**
  - Open Chrome on Android
  - Navigate to `http://<YOUR_IP>:8000`
  - **Success Criteria**: UI loads on mobile

### 5.2 Touch Interaction Testing ✅

**Objective**: Verify swipe gestures and touch interactions work correctly.

#### Test Steps:
- [ ] **Test Vertical Scrolling**
  - Open a long script
  - Scroll down with finger
  - **Success Criteria**: Content scrolls smoothly without triggering swipe

- [ ] **Test Swipe Right (Approve)**
  - Swipe script card to the right
  - **Success Criteria**: Green checkmark appears, script approved, next script loads

- [ ] **Test Swipe Left (Reject)**
  - Swipe script card to the left
  - **Success Criteria**: Red X appears, script rejected, next script loads

- [ ] **Test Category Filter Scrolling**
  - Swipe left/right on category pill bar
  - **Success Criteria**: Pills scroll horizontally

- [ ] **Test Filter Panel on Mobile**
  - Tap "🔍 Filters" button
  - **Success Criteria**: Panel expands smoothly

- [ ] **Test Touch Targets**
  - Tap DJ selector dropdown
  - Tap category pills
  - Tap filter buttons
  - **Success Criteria**: All elements respond to touch, no missed taps

### 5.3 Mobile-Specific UI Validation ✅

#### Test Steps:
- [ ] **Test Responsive Layout**
  - Rotate phone to landscape
  - Rotate back to portrait
  - **Success Criteria**: Layout adapts correctly

- [ ] **Test Modal Dialogs**
  - Open Stats modal
  - Scroll within modal
  - Close modal
  - **Success Criteria**: Modal scrolls, closes properly, background not scrollable

- [ ] **Test Pull-to-Refresh Prevention**
  - Scroll to top of page
  - Try to pull down
  - **Success Criteria**: No browser refresh triggered

- [ ] **Test Text Selection**
  - Long-press on script text
  - **Success Criteria**: Text can be selected and copied

---

## Phase 6: Playwright UI Automation Testing

### 6.1 Playwright Setup ✅

**Objective**: Set up Playwright for automated UI testing.

#### Test Steps:
- [ ] **Install Playwright** (if not already available via MCP)
  ```bash
  # The Playwright MCP server should already be available
  # Verify by checking if playwright-browser tools are accessible
  ```

- [ ] **Create Playwright Test Script**
  ```bash
  # Create test directory
  mkdir -p tools/script-review-app/tests/playwright
  ```

### 6.2 Automated UI Tests with Playwright ✅

**Objective**: Use Playwright MCP server to validate UI behavior.

#### Test Scenarios:

- [ ] **Test 1: Page Load and Initial State**
  - Navigate to `http://localhost:8000`
  - Take screenshot
  - Verify DJ selector is visible
  - Verify category pills are visible
  - **Success Criteria**: Elements present in screenshot

- [ ] **Test 2: DJ Selection Flow**
  - Click DJ selector
  - Select "Julie - Appalachia"
  - Wait for scripts to reload
  - Take screenshot
  - **Success Criteria**: Scripts filtered, UI updated

- [ ] **Test 3: Category Filtering**
  - Click "Weather" category pill
  - Wait for filter to apply
  - Take screenshot
  - Verify weather badge on visible card
  - **Success Criteria**: Only weather scripts shown

- [ ] **Test 4: Swipe Gesture Simulation**
  - Get card element
  - Simulate swipe right gesture
  - Wait for next card
  - Take screenshot
  - **Success Criteria**: Card approved, next script loaded

- [ ] **Test 5: Advanced Filters**
  - Click "🔍 Filters" button
  - Fill date_from field
  - Fill date_to field
  - Click "Apply Filters"
  - Take screenshot
  - **Success Criteria**: Filters applied, results updated

- [ ] **Test 6: Statistics Modal**
  - Click "📊 Stats" button
  - Wait for modal to open
  - Take screenshot
  - Verify overview section visible
  - Click close button
  - **Success Criteria**: Modal opens and closes correctly

- [ ] **Test 7: Responsive Design**
  - Resize browser to 375x667 (iPhone size)
  - Take screenshot
  - Resize to 1920x1080 (desktop)
  - Take screenshot
  - **Success Criteria**: Layout adapts correctly

- [ ] **Test 8: Console Errors Check**
  - Navigate to page
  - Interact with filters
  - Check browser console
  - **Success Criteria**: No JavaScript errors

### 6.3 Playwright MCP Commands ✅

**Use these Playwright MCP commands for testing:**

```javascript
// Navigate to app
browser_navigate: { url: "http://localhost:8000" }

// Take snapshot of current state
browser_snapshot: {}

// Click element (use ref from snapshot)
browser_click: { element: "DJ selector", ref: "<element_ref>" }

// Type in input field
browser_type: { element: "date input", ref: "<element_ref>", text: "2024-01-01" }

// Take screenshot
browser_take_screenshot: { filename: "test_homepage.png" }

// Wait for element/text
browser_wait_for: { text: "Scripts loaded" }

// Get console messages
browser_console_messages: {}

// Resize window
browser_resize: { width: 375, height: 667 }
```

---

## Phase 7: Integration Testing

### 7.1 End-to-End Workflow ✅

**Objective**: Test complete workflow from broadcast generation to UI review.

#### Test Steps:
- [ ] **Generate Fresh Scripts**
  ```bash
  cd tools/script-generator
  python broadcast_engine.py --dj Julie --segments 20
  ```
  **Success Criteria**: 20 segments generated

- [ ] **Verify in Backend**
  ```bash
  curl "http://localhost:8000/api/scripts?status=pending" | python -m json.tool | grep -c "id"
  ```
  **Success Criteria**: Shows 20+ pending scripts

- [ ] **Review via UI**
  - Open UI on mobile
  - Review 5 scripts (approve 3, reject 2)
  - **Success Criteria**: Scripts processed successfully

- [ ] **Verify Status Changes**
  ```bash
  curl "http://localhost:8000/api/scripts?status=approved" | python -m json.tool | grep -c "id"
  ```
  **Success Criteria**: Shows 3 approved scripts

- [ ] **Check Statistics**
  - Open Stats dashboard
  - **Success Criteria**: Shows 60% approval rate (3/5)

### 7.2 Multi-DJ Testing ✅

#### Test Steps:
- [ ] **Generate Scripts for Each DJ**
  ```bash
  for dj in Julie "Mr. New Vegas" Travis; do
    python broadcast_engine.py --dj "$dj" --segments 5
  done
  ```
  **Success Criteria**: 15 scripts generated (5 per DJ)

- [ ] **Filter by Each DJ in UI**
  - Select "Julie - Appalachia"
  - Verify scripts shown
  - Select "Mr. New Vegas - Mojave"
  - Verify scripts shown
  - **Success Criteria**: Correct scripts for each DJ

### 7.3 Weather System Integration ✅

#### Test Steps:
- [ ] **Set Emergency Weather**
  ```bash
  python set_weather.py --region Appalachia --type rad_storm --duration 3
  ```

- [ ] **Generate Emergency Broadcast**
  ```bash
  python broadcast_engine.py --dj Julie --segments 1
  ```
  **Success Criteria**: Generates emergency weather alert

- [ ] **Verify in UI**
  - Filter by Weather category
  - Find emergency alert script
  - **Success Criteria**: Shows ⚠️ emergency indicator

### 7.4 Story System Integration ✅

#### Test Steps:
- [ ] **Verify Story Scripts Generated**
  ```bash
  curl "http://localhost:8000/api/scripts?category=Story" | python -m json.tool
  ```
  **Success Criteria**: Shows story scripts with timeline metadata

- [ ] **Test Timeline View**
  - Click "📚 Story Timelines" button
  - **Success Criteria**: Shows stories grouped by Daily/Weekly/Monthly/Yearly

- [ ] **Test Story Metadata Display**
  - View story script card
  - **Success Criteria**: Shows timeline badge, act position, engagement score

---

## Phase 8: Performance and Stress Testing

### 8.1 Load Testing ✅

#### Test Steps:
- [ ] **Generate Large Script Set**
  ```bash
  python broadcast_engine.py --dj Julie --segments 100
  ```
  **Success Criteria**: 100 scripts generated without errors

- [ ] **Test UI with Many Scripts**
  - Open UI
  - Load all 100 scripts
  - Measure load time
  - **Success Criteria**: Page loads in < 3 seconds

- [ ] **Test Filtering Performance**
  - Apply multiple filters
  - Measure response time
  - **Success Criteria**: Filters apply in < 500ms

### 8.2 Mobile Performance ✅

#### Test Steps:
- [ ] **Test on Mobile Network**
  - Switch phone to mobile data (4G/5G)
  - Load UI
  - **Success Criteria**: Usable on mobile network

- [ ] **Test Offline Behavior**
  - Load UI
  - Turn off WiFi
  - Try to load scripts
  - **Success Criteria**: Shows appropriate error message

---

## Success Criteria Summary

### ✅ Backend Systems
- [ ] All 265 tests passing
- [ ] Weather system generates calendars correctly
- [ ] Story system extracts and schedules stories
- [ ] Broadcast engine integrates both systems

### ✅ ChromaDB Integration
- [ ] ChromaDB connects successfully
- [ ] Story extraction works with real data
- [ ] Content metadata properly formatted

### ✅ Web UI Backend
- [ ] FastAPI server starts without errors
- [ ] All API endpoints respond correctly
- [ ] Filtering works across all dimensions
- [ ] Statistics calculate correctly

### ✅ Desktop UI
- [ ] All UI elements render correctly
- [ ] Keyboard navigation works
- [ ] Filters and modals function properly
- [ ] No console errors

### ✅ Mobile UI
- [ ] UI loads on Android Chrome
- [ ] Swipe gestures work correctly
- [ ] Vertical scrolling doesn't trigger swipe
- [ ] Touch targets are appropriately sized
- [ ] Responsive layout works

### ✅ Playwright Automation
- [ ] Can navigate and interact with UI
- [ ] Screenshots capture correctly
- [ ] Can simulate user workflows
- [ ] No JavaScript errors detected

### ✅ Integration
- [ ] End-to-end workflow completes successfully
- [ ] Multi-DJ filtering works
- [ ] Weather and story metadata displays correctly
- [ ] Performance acceptable with large datasets

---

## Troubleshooting Guide

### Common Issues

**Issue**: Backend won't start
- **Solution**: Check if port 8000 is already in use: `lsof -i :8000` (Linux/Mac) or `netstat -ano | findstr :8000` (Windows)

**Issue**: ChromaDB connection fails
- **Solution**: Ensure ChromaDB is installed: `pip install chromadb`

**Issue**: No scripts showing in UI
- **Solution**: Generate test scripts first using broadcast_engine.py

**Issue**: Can't access from mobile
- **Solution**: Verify firewall allows connections, check IP address is correct

**Issue**: Swipe not working on mobile
- **Solution**: Check browser console for touch event errors, verify touch-action CSS is applied

**Issue**: Playwright tests fail
- **Solution**: Ensure backend is running on localhost:8000, check network access

---

## Debugging with Playwright MCP

### Interactive Debugging Session

1. **Start backend**: `uvicorn main:app --reload`
2. **Open Playwright MCP session**
3. **Navigate**: Use `browser_navigate` to open UI
4. **Inspect**: Use `browser_snapshot` to see current state
5. **Interact**: Use `browser_click`, `browser_type` to simulate user actions
6. **Capture**: Use `browser_take_screenshot` to document issues
7. **Debug**: Use `browser_console_messages` to see JavaScript errors

### Example Debugging Workflow

```
# Start session
browser_navigate: { url: "http://localhost:8000" }
browser_take_screenshot: { filename: "initial_load.png" }

# Test DJ selector
browser_snapshot: {}
# (Get element ref from snapshot)
browser_click: { element: "DJ selector", ref: "element_123" }
browser_wait_for: { time: 1 }
browser_take_screenshot: { filename: "dj_dropdown.png" }

# Check for errors
browser_console_messages: {}
```

---

## Reporting Issues

When reporting issues, include:
1. Test phase and step number
2. Expected vs actual behavior
3. Screenshots (especially for UI issues)
4. Console errors (from browser or Playwright)
5. Backend logs
6. Device/browser information (for mobile issues)

---

## Next Steps After Testing

Once all tests pass:
1. Document any issues found and fixed
2. Update README with setup instructions
3. Create demo video showing mobile UI in action
4. Deploy to production environment
5. Monitor real-world usage

---

## Testing Timeline Estimate

- **Phase 1-2 (Backend)**: 2-3 hours
- **Phase 3 (Web Backend)**: 1 hour
- **Phase 4 (Desktop UI)**: 1-2 hours
- **Phase 5 (Mobile UI)**: 2-3 hours
- **Phase 6 (Playwright)**: 2-3 hours
- **Phase 7-8 (Integration/Performance)**: 2-3 hours

**Total**: 10-17 hours of comprehensive testing

---

**Last Updated**: 2026-01-18
**Version**: 1.0
**Status**: Ready for Testing
