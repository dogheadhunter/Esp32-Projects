# Known Issues - Mobile Script Review App

**Status as of**: 2026-01-18

## High Priority
- [ ] **Tailwind CDN in Production**: Currently using cdn.tailwindcss.com which generates console warning and adds external dependency.
  - *Impact*: Large CDN file, privacy concerns, console warning
  - *Fix*: Build local Tailwind CSS with PurgeCSS
  - *Discovered*: Performance validation 2026-01-18

## Medium Priority
- [ ] **Slow Script Loading**: `/api/scripts` endpoint takes 2+ seconds to load 37 scripts.
  - *Impact*: Poor UX when many pending scripts exist
  - *Fix*: Implement pagination (10-20 scripts per page)
  - *Discovered*: Performance validation 2026-01-18

- [ ] **Swipe Gestures Disabled**: Swipe left/right to approve/reject was removed due to conflict with page scrolling.
  - *Impact*: Users must use buttons instead of swipe gestures
  - *Workaround*: Use Approve/Reject buttons (which work well)
  - *Discovered*: Manual mobile testing 2026-01-18

## Low Priority
- [ ] **Password Visibility Toggle**: No show/hide option for API token input field.
  - *Impact*: Difficult to verify token entry on mobile keyboards
  - *Requested*: Manual mobile testing 2026-01-17
- [ ] **Toast overlap**: On very small screens (iPhone SE), toast notifications might briefly cover the Approve/Reject buttons.
  - *Workaround*: Wait for toast to disappear or swipe card instead.
- [ ] **Tailwind CDN**: Currently using CDN for development.
  - *Mitigation*: For production, set up a build step to generate minimal CSS file (Phase 3 task).
- [ ] **Console Warnings**: "cdn.tailwindcss.com should not be used in production" warning visible in console.
  - *Fix*: Implement local Tailwind build.

## Fixed Issues
- [x] **Event Listeners Missing**: Action buttons unresponsive after login. (Fixed 2026-01-17)
