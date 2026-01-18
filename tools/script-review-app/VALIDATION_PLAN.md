# Mobile Script Review App - Validation Plan

**Date**: 2026-01-17  
**Purpose**: Validate implementation using real broadcast scripts with comprehensive testing and performance optimization for self-hosted remote access  
**Target**: Production-ready for personal use with Lighthouse score >90

---

## Phase 1: Setup Dependencies and Real Test Data

### Checklist

- [ ] Create `requirements.txt` with FastAPI dependencies
  - [ ] fastapi
  - [ ] uvicorn[standard]
  - [ ] pydantic
  - [ ] pydantic-settings
  - [ ] python-multipart
- [ ] Create `tests/requirements.txt` with test dependencies
  - [ ] pytest
  - [ ] pytest-playwright
  - [ ] playwright
- [ ] Install Playwright browsers: `playwright install chromium`
- [ ] Copy real broadcast scripts from broadcast engine output
  - [ ] Find latest Julie scripts
  - [ ] Find latest Mr. New Vegas scripts
  - [ ] Find latest Travis Miles scripts
  - [ ] Copy to `output/scripts/pending_review/[DJ_NAME]/`
  - [ ] Verify filename format: `YYYY-MM-DD_HHMMSS_DJName_ContentType.txt`
- [ ] Fix hardcoded paths in `tests/conftest.py`
  - [ ] Replace `/home/runner/work/...` with relative path
  - [ ] Test fixture imports correctly
- [ ] Create PWA icons
  - [ ] Generate 192x192 PNG from icon.svg
  - [ ] Generate 512x512 PNG from icon.svg
  - [ ] Save to `frontend/static/icons/`
  - [ ] Update manifest.json references if needed

### Success Criteria

✅ **Dependencies Installed**
- `pip install -r requirements.txt` completes without errors
- `pip install -r tests/requirements.txt` completes without errors
- `playwright --version` shows installed version

✅ **Test Data Ready**
- At least 5 scripts per DJ in pending_review folders
- All scripts follow naming convention
- Scripts contain actual broadcast engine content (not Lorem Ipsum)
- Total script count: minimum 15 scripts

✅ **Icons Created**
- `frontend/static/icons/icon-192.png` exists (192x192 pixels)
- `frontend/static/icons/icon-512.png` exists (512x512 pixels)
- Icons are valid PNG format

✅ **Paths Fixed**
- `tests/conftest.py` uses relative paths or environment variables
- No hardcoded `/home/runner/` paths remain

---

## Phase 2: Run Playwright End-to-End Test Suite

### Checklist

- [ ] Start FastAPI server: `uvicorn backend.main:app --reload`
- [ ] Verify server health: `curl http://localhost:8000/health`
- [ ] Set test environment variable: `SCRIPT_REVIEW_TOKEN=test-token-123`
- [ ] Run Playwright tests: `pytest tests/test_playwright.py -v`
- [ ] Review test output for failures
- [ ] Capture screenshots of any failures
- [ ] Fix critical bugs blocking workflows
  - [ ] Authentication modal issues
  - [ ] Script loading errors
  - [ ] Approve workflow bugs
  - [ ] Reject workflow bugs
  - [ ] DJ filter issues
  - [ ] Statistics display errors
- [ ] Re-run tests after fixes until all pass
- [ ] Verify real script content displays correctly in browser

### Success Criteria

✅ **Server Healthy**
- Health endpoint returns `{"status": "ok", "version": "1.0.0"}`
- Frontend loads at `http://localhost:8000`
- No server errors in console

✅ **All Tests Pass**
- 20/20 Playwright tests pass
- Zero test failures
- Zero test errors
- Test duration: <60 seconds

✅ **Real Data Integration**
- Tests work with actual broadcast scripts (not mock data)
- DJ names parsed correctly from filenames
- Content types displayed correctly
- Timestamps formatted properly

✅ **Screenshots Clean**
- No visual regressions in `tests/screenshots/`
- Cards display real script text
- Buttons and UI elements render correctly

---

## Phase 3: Performance Validation and Optimization

### Checklist

- [ ] Run Lighthouse audit: Chrome DevTools > Lighthouse > Analyze page load
- [ ] Record baseline metrics:
  - [ ] Performance score: ____/100
  - [ ] First Contentful Paint: ____ ms
  - [ ] Time to Interactive: ____ ms
  - [ ] Total Bundle Size: ____ KB
- [ ] Identify bottlenecks from Lighthouse report
- [ ] If Performance <90, implement optimizations:
  - [ ] Replace Tailwind CDN with local build
    - [ ] Install Tailwind CLI: `npm install -D tailwindcss`
    - [ ] Create `tailwind.config.js`
    - [ ] Run PurgeCSS to remove unused styles
    - [ ] Replace CDN link with local CSS
  - [ ] Minify JavaScript files
    - [ ] Minify `app.js` → `app.min.js`
    - [ ] Minify `swipe.js` → `swipe.min.js`
    - [ ] Minify `api.js` → `api.min.js`
    - [ ] Update `index.html` script tags
  - [ ] Optimize Service Worker caching
    - [ ] Review cache strategy (cache-first vs network-first)
    - [ ] Remove unnecessary cached resources
    - [ ] Implement cache versioning
  - [ ] Compress icons
    - [ ] Use imagemin or similar tool
    - [ ] Compress PNG icons to reduce size
- [ ] Test API response times
  - [ ] `/api/scripts` endpoint: ____ ms
  - [ ] `/api/review` endpoint: ____ ms
  - [ ] `/api/stats` endpoint: ____ ms
- [ ] Re-run Lighthouse after each optimization
- [ ] Document performance improvements

### Success Criteria

✅ **Lighthouse Performance Score >90**
- Overall Performance: ≥90/100
- Accessibility: ≥90/100
- Best Practices: ≥90/100
- SEO: ≥80/100 (not critical for internal app)

✅ **Core Web Vitals Met**
- First Contentful Paint: <1.5s
- Time to Interactive: <3.0s
- Total Blocking Time: <300ms
- Largest Contentful Paint: <2.5s

✅ **API Performance**
- `/api/scripts` response: <200ms (with 50+ scripts)
- `/api/review` response: <200ms
- `/api/stats` response: <100ms

✅ **Bundle Size Optimized**
- Total CSS: <50KB (gzipped)
- Total JS: <100KB (gzipped)
- PWA icons: <50KB each (compressed)

---

## Phase 4: Manual Mobile Testing with Real Device

### Checklist

- [ ] Connect mobile device to same network as dev server
- [ ] Find local IP address: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)
- [ ] Access app on phone: `http://[LOCAL_IP]:8000`
- [ ] Test PWA installation
  - [ ] "Add to Home Screen" prompt appears
  - [ ] Tap to install
  - [ ] App icon appears on home screen
  - [ ] Launch app from home screen
  - [ ] App opens in standalone mode (no browser UI)
- [ ] Test swipe gestures
  - [ ] Swipe right → Approve (green checkmark appears)
  - [ ] Swipe left → Reject (red X appears)
  - [ ] Swipe threshold feels natural (~100-150px)
  - [ ] Card animation smooth (no jank)
  - [ ] Next card reveals after swipe
- [ ] Test touch targets
  - [ ] Approve button easy to tap (≥48x48px)
  - [ ] Reject button easy to tap
  - [ ] DJ filter dropdown works
  - [ ] Rejection reason dropdown works
  - [ ] Comment textarea usable on small keyboard
- [ ] Test responsive layout
  - [ ] Portrait mode (375px width)
  - [ ] Landscape mode (667px width)
  - [ ] Tablet portrait (768px width)
  - [ ] Card text readable without zooming
  - [ ] No horizontal scrolling
- [ ] Test offline mode
  - [ ] Enable airplane mode
  - [ ] App still loads (cached)
  - [ ] View cached scripts
  - [ ] Attempt review (should queue or show offline message)
  - [ ] Disable airplane mode
  - [ ] Verify queued actions sync
- [ ] Test complete workflows
  - [ ] Approve 5 scripts → Check `output/scripts/approved/`
  - [ ] Reject 3 scripts with reasons → Check `output/scripts/rejected/`
  - [ ] Verify statistics update correctly
  - [ ] Verify metadata logged in JSON files

### Success Criteria

✅ **PWA Installation Works**
- App installs to home screen
- Launches in standalone mode (fullscreen, no browser chrome)
- Icon displays correctly on home screen
- Splash screen appears on launch (if configured)

✅ **Gestures Feel Natural**
- Swipe detection threshold: 100-150px
- Visual feedback immediate (<50ms)
- Animations smooth (60fps, no jank)
- Card removal animation: 300ms ease-out
- Next card reveal smooth

✅ **Mobile UX Excellent**
- All touch targets ≥48x48px
- Text readable at arm's length (16px+ font size)
- No need to zoom to read content
- Buttons easy to tap with thumb
- Dropdown menus accessible
- Keyboard doesn't obscure inputs

✅ **Offline Mode Functional**
- App loads without network
- Static assets served from cache
- Scripts cached from previous session visible
- Offline indicator shown (if implemented)
- Actions queue or graceful error shown

✅ **Real Workflows Complete**
- Scripts move from pending → approved/rejected folders
- Metadata logged correctly in JSON files
- Statistics update in real-time
- No duplicate actions (idempotency)
- File operations atomic (no partial writes)

---

## Phase 5: Self-Hosting Deployment Setup

### Checklist

- [ ] Generate secure API token
  - [ ] Run: `openssl rand -hex 32`
  - [ ] Save to `.env` file: `SCRIPT_REVIEW_TOKEN=<generated_token>`
  - [ ] Remove test token from code
- [ ] Configure production settings
  - [ ] Update `ALLOWED_ORIGINS` in `config.py` for production domain
  - [ ] Set `LOG_LEVEL=WARNING` for production
  - [ ] Review CORS settings
- [ ] Setup dynamic DNS (free option)
  - [ ] Choose provider: DuckDNS, No-IP, or Dynu
  - [ ] Create account and domain (e.g., `myscriptreview.duckdns.org`)
  - [ ] Install DDNS updater on host machine
  - [ ] Verify domain resolves to home IP
- [ ] Configure router port forwarding
  - [ ] Forward external port 443 → internal port 8000 (or nginx port)
  - [ ] Reserve static local IP for host machine (DHCP reservation)
  - [ ] Test port forwarding: `https://www.yougetsignal.com/tools/open-ports/`
- [ ] Setup HTTPS with Let's Encrypt
  - [ ] Install certbot: `sudo apt-get install certbot python3-certbot-nginx` (Linux)
  - [ ] Or use standalone mode for Windows
  - [ ] Generate certificate: `certbot certonly --standalone -d myscriptreview.duckdns.org`
  - [ ] Verify certificate installed: `ls /etc/letsencrypt/live/`
  - [ ] Setup auto-renewal: `certbot renew --dry-run`
- [ ] Configure nginx reverse proxy (optional but recommended)
  - [ ] Install nginx: `sudo apt-get install nginx`
  - [ ] Create nginx config file for app
  - [ ] Configure SSL, headers (HSTS, CSP), and proxy_pass
  - [ ] Test config: `nginx -t`
  - [ ] Reload nginx: `systemctl reload nginx`
- [ ] Create systemd service for auto-start (Linux)
  - [ ] Create service file: `/etc/systemd/system/script-review.service`
  - [ ] Configure WorkingDirectory, ExecStart, User
  - [ ] Enable service: `systemctl enable script-review`
  - [ ] Start service: `systemctl start script-review`
  - [ ] Check status: `systemctl status script-review`
- [ ] Test remote access
  - [ ] Access app from cellular data (not home WiFi)
  - [ ] URL: `https://myscriptreview.duckdns.org`
  - [ ] Verify HTTPS (green lock icon)
  - [ ] Test authentication with production token
  - [ ] Test approve/reject workflows
  - [ ] Verify file operations work remotely

### Success Criteria

✅ **Secure Token Generated**
- Token is 64 characters (32 bytes hex)
- Stored in `.env` file only (not in code)
- Not committed to git (`.env` in `.gitignore`)

✅ **Dynamic DNS Working**
- Domain resolves to home public IP
- DDNS updater runs on startup
- Domain updates within 5 minutes of IP change

✅ **HTTPS Configured**
- SSL certificate valid and trusted
- `https://` URL loads without browser warnings
- Certificate auto-renewal scheduled (every 90 days)
- HTTP redirects to HTTPS (if nginx configured)

✅ **Port Forwarding Active**
- External port 443 accessible from internet
- Port forwarding test shows "open"
- Local firewall allows traffic on port 8000/443

✅ **Auto-Start Configured**
- Service starts on system boot
- Service restarts on crash
- Logs accessible via `journalctl -u script-review`

✅ **Remote Access Verified**
- App accessible from cellular data (4G/5G)
- App accessible from public WiFi
- Authentication works with production token
- All workflows function remotely (approve/reject)
- Performance acceptable over cellular (<5s load time)

---

## Phase 6: Document Validation Results

### Checklist

- [ ] Create `tests/MASTER_TEST_LOG.md`
  - [ ] Document all test results (20 Playwright tests)
  - [ ] Include pass/fail status for each test
  - [ ] Note any bugs found and fixed
  - [ ] Screenshot references for failures
- [ ] Create `tests/KNOWN_ISSUES.md`
  - [ ] List non-critical issues discovered
  - [ ] Include reproduction steps
  - [ ] Note workarounds if available
  - [ ] Prioritize issues (low/medium/high)
- [ ] Create `tests/screenshots/` directory structure
  - [ ] `tests/screenshots/success/` for passing tests
  - [ ] `tests/screenshots/failures/` for failed tests
  - [ ] `tests/screenshots/performance/` for Lighthouse reports
  - [ ] Archive all screenshots with timestamps
- [ ] Document performance metrics
  - [ ] Baseline Lighthouse scores (before optimization)
  - [ ] Final Lighthouse scores (after optimization)
  - [ ] Performance improvement delta
  - [ ] API response times
- [ ] Update `README.md` with deployment guide
  - [ ] Self-hosting instructions (HTTPS, DDNS, port forwarding)
  - [ ] nginx configuration example
  - [ ] systemd service example
  - [ ] Security best practices
  - [ ] Troubleshooting section
- [ ] Create deployment checklist in `README.md`
  - [ ] Pre-deployment tasks
  - [ ] Deployment steps
  - [ ] Post-deployment verification
  - [ ] Maintenance tasks (log rotation, backups)

### Success Criteria

✅ **Test Documentation Complete**
- `MASTER_TEST_LOG.md` contains all 20 test results
- Each test has status: ✅ PASS / ❌ FAIL / 🔧 FIXED
- Bugs documented with issue description and fix details
- Screenshot paths referenced for visual evidence

✅ **Performance Documentation Complete**
- Baseline metrics recorded (before optimization)
- Final metrics recorded (after optimization)
- Improvement delta calculated and documented
- Lighthouse report screenshots saved
- API response times documented

✅ **Known Issues Documented**
- All non-critical issues listed
- Reproduction steps included
- Priority assigned (low/medium/high)
- Workarounds documented where available

✅ **Deployment Guide Complete**
- Step-by-step self-hosting instructions
- All configuration files provided as examples
- Security best practices documented
- Troubleshooting section with common issues
- Maintenance tasks outlined

✅ **Screenshots Organized**
- All screenshots saved to `tests/screenshots/`
- Organized by category (success/failures/performance)
- Named with timestamps and test names
- Lighthouse reports saved as PNG

---

## Overall Success Criteria

### ✅ Application Validated

- [ ] All dependencies installed without errors
- [ ] 15+ real broadcast scripts loaded as test data
- [ ] All 20 Playwright tests pass
- [ ] Zero critical bugs blocking workflows
- [ ] Real script content displays correctly

### ✅ Performance Optimized

- [ ] Lighthouse Performance Score: ≥90/100
- [ ] First Contentful Paint: <1.5s
- [ ] Time to Interactive: <3.0s
- [ ] API response times: <200ms
- [ ] Bundle size optimized (<150KB total)

### ✅ Mobile Experience Excellent

- [ ] PWA installs to home screen successfully
- [ ] Swipe gestures feel natural on real device
- [ ] All touch targets ≥48x48px
- [ ] Text readable without zooming
- [ ] Offline mode functional
- [ ] Complete workflows tested on mobile

### ✅ Self-Hosting Configured

- [ ] Secure token generated (64 characters)
- [ ] HTTPS certificate valid and trusted
- [ ] Dynamic DNS resolving correctly
- [ ] Port forwarding active and tested
- [ ] Auto-start service configured
- [ ] Remote access verified from cellular/WiFi

### ✅ Documentation Complete

- [ ] Test results documented in `MASTER_TEST_LOG.md`
- [ ] Performance metrics documented
- [ ] Known issues documented
- [ ] Deployment guide written in `README.md`
- [ ] Screenshots organized and archived

---

## Final Validation Checklist

Before considering validation complete:

- [ ] Run full Playwright test suite one final time
- [ ] Test remote access from 3 different networks (cellular, public WiFi, friend's WiFi)
- [ ] Test PWA installation on both iOS and Android (if available)
- [ ] Approve 10 real scripts and verify they move to approved folder
- [ ] Reject 10 real scripts with different reasons and verify metadata
- [ ] Check all documentation is up-to-date
- [ ] Verify no secrets committed to git
- [ ] Run Lighthouse audit one final time
- [ ] Confirm auto-start service works after reboot
- [ ] Review logs for any unexpected errors

---

## Next Steps After Validation

1. **Begin using app for real script review workflow**
2. **Monitor logs for issues over first week**
3. **Add backend unit tests if issues arise**
4. **Consider rate limiting if abuse detected**
5. **Setup automated backups for metadata JSON files**
6. **Review security logs monthly**
7. **Update SSL certificates (auto-renewal should handle this)**

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-17  
**Status**: Ready for validation execution
