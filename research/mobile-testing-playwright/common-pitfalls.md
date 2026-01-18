# Common Pitfalls: Mobile Testing with Playwright

**Category**: Mobile Device Simulation  
**Last Updated**: 2026-01-18

This document catalogs common mistakes when setting up Android phone simulation for Playwright testing, particularly with MCP server integration.

---

## Configuration Pitfalls

### 1. Forgetting the `--device` Flag in MCP Config

**Problem**: Tests run in desktop mode even when you want mobile testing.

**Symptoms**:
- Screenshots show desktop layout
- Mobile navigation doesn't appear
- Viewport is 1280x720 instead of mobile dimensions

**Root Cause**: The MCP server defaults to desktop browser if no device is specified.

**Solution**:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--device",    // ← ADD THIS
        "Pixel 5"      // ← AND THIS
      ]
    }
  }
}
```

**Prevention**: Always include device specification in your MCP config from the start.

---

### 2. Typos in Device Names

**Problem**: Error: "Device 'Pixle 5' not found"

**Root Cause**: Device names are case-sensitive and must match exactly.

**Common Mistakes**:
- `"Pixle 5"` → should be `"Pixel 5"`
- `"iphone 13"` → should be `"iPhone 13"`
- `"galaxy s9+"` → should be `"Galaxy S9+"`
- `"pixel5"` → should be `"Pixel 5"` (needs space)

**Solution**: Always use exact names from [Playwright's device registry](https://github.com/microsoft/playwright/blob/main/packages/playwright-core/src/server/deviceDescriptorsSource.json).

**Prevention**: Copy-paste device names from official documentation.

---

### 3. Mixing Emulation Approaches

**Problem**: Trying to use `--device` flag with Android Studio AVD simultaneously.

**Symptoms**:
- Confusion about which "emulation" is being used
- Unexpected behavior in tests
- Complex setup that doesn't work

**Root Cause**: There are TWO different approaches:
1. **Device Emulation**: Playwright simulates a device (no emulator needed)
2. **Real Android Emulator**: Playwright connects to Android Studio's AVD via ADB

**Solution**: Choose ONE approach:
- **For most cases**: Use device emulation with `--device "Pixel 5"`
- **For Android-specific bugs**: Use Playwright's Android API with AVD

**Prevention**: Understand that device emulation ≠ running an Android emulator.

---

### 4. Overriding Viewport When Using Device Preset

**Problem**: Mobile emulation doesn't work correctly despite using `--device`.

**Symptoms**:
- Viewport is wrong size
- Touch events don't work
- Mobile detection fails

**Root Cause**: The `--viewport-size` flag overrides the device preset's viewport.

**Bad Configuration**:
```json
{
  "args": [
    "@playwright/mcp@latest",
    "--device", "Pixel 5",
    "--viewport-size", "1920x1080"  // ← CONFLICTS with device
  ]
}
```

**Solution**: Remove `--viewport-size` when using `--device`. The device preset includes the correct viewport.

**Prevention**: Use `--device` OR custom viewport, not both.

---

## Browser & Platform Pitfalls

### 5. Expecting iOS Testing on Windows

**Problem**: Trying to test iPhone Safari on Windows PC.

**Symptoms**:
- Can't install Safari browser
- iPhone emulator not available
- Looking for iOS simulator on Windows

**Root Cause**: iOS Safari testing requires macOS or cloud services.

**Reality Check**:
- ❌ Safari doesn't run natively on Windows
- ❌ iOS simulator only exists on macOS
- ✅ Playwright can emulate iPhone **in WebKit browser** (approximation)
- ✅ True iOS Safari testing needs macOS, cloud services, or real devices

**Solution**:
- Use `--device "iPhone 13"` with WebKit for **approximation**
- For true iOS testing: Use BrowserStack, Sauce Labs, or macOS + Safari

**Prevention**: Understand platform limitations before planning tests.

---

### 6. Assuming Emulation = Real Device

**Problem**: Finding bugs on real devices that don't appear in emulated tests.

**Symptoms**:
- Tests pass in emulation, fail on real Android
- Touch interactions work differently
- Performance issues not caught

**Root Cause**: Device emulation simulates mobile behavior but can't replicate:
- Native browser rendering quirks
- Hardware-specific bugs
- Real touch gesture physics
- Actual network conditions

**Solution**:
- Use emulation for 90% of testing (fast, cheap, CI-friendly)
- Validate critical flows on real devices monthly
- Use cloud device farms for comprehensive testing

**Prevention**: Treat emulation as "good enough" approximation, not perfect replica.

---

## ADB & Android Emulator Pitfalls

### 7. ADB Port Conflicts

**Problem**: `adb devices` doesn't show the emulator, or connection fails.

**Symptoms**:
- "cannot bind to 0.0.0.0:5037" error
- Emulator running but not detected
- ADB server won't start

**Root Cause**: Another process is using port 5037 (ADB's default port).

**Diagnosis**:
```bash
# Windows
netstat -ano | findstr :5037

# Mac/Linux
lsof -i :5037
```

**Solution**:
```bash
# Kill ADB server and restart
adb kill-server
adb start-server
adb devices
```

**Prevention**: Only run one ADB instance at a time. Close other Android tools.

---

### 8. Forgetting to Enable Chrome Flags

**Problem**: Playwright can't connect to Chrome on Android emulator.

**Symptoms**:
- Timeout errors when launching browser
- Chrome opens but Playwright can't control it

**Root Cause**: Chrome on Android requires command-line flag enabled.

**Solution**:
1. Open Chrome on the emulator
2. Navigate to `chrome://flags`
3. Search for "Enable command line on non-rooted devices"
4. Set to **Enabled**
5. Restart Chrome

**Prevention**: Add this step to your emulator setup checklist.

---

### 9. Insufficient Emulator Resources

**Problem**: Android emulator is slow, freezes, or crashes.

**Symptoms**:
- Emulator takes 5+ minutes to start
- UI is laggy
- Tests timeout
- System becomes unresponsive

**Root Cause**: AVD allocated insufficient RAM or CPU.

**Solution**:
1. Open AVD Manager in Android Studio
2. Edit your virtual device
3. Click "Show Advanced Settings"
4. Increase RAM to at least 4 GB
5. Set CPU cores to 4 (if you have ≥8 cores)
6. Enable hardware acceleration

**Minimum Requirements**:
- RAM: 4 GB for AVD + 4 GB for host system
- CPU: 4+ cores
- Disk: 10 GB free space
- Virtualization: Enabled in BIOS (Intel VT-x / AMD-V)

**Prevention**: Check system resources before installing Android Studio.

---

## Testing & Debugging Pitfalls

### 10. Running Headless Mode Too Early

**Problem**: Tests fail in headless mode, but you can't see why.

**Symptoms**:
- Cryptic error messages
- Can't debug visually
- Don't know what the page looks like

**Root Cause**: Jumping straight to headless without visual verification.

**Solution**:
```json
{
  "args": [
    "@playwright/mcp@latest",
    "--device", "Pixel 5"
    // Omit --headless during development
  ]
}
```

Add `--headless` only after tests work in headed mode.

**Prevention**: Always develop tests in headed mode first, then add headless for CI.

---

### 11. Not Validating Touch Events

**Problem**: Click events work but touch-specific interactions fail.

**Symptoms**:
- Swipe gestures don't work
- Long-press doesn't trigger
- Touch targets are off

**Root Cause**: Forgetting that mobile uses touch events, not mouse events.

**Solution**: Device presets automatically enable touch. For custom configs:
```javascript
{
  viewport: { width: 360, height: 740 },
  hasTouch: true,     // ← Enable touch
  isMobile: true      // ← Enable mobile mode
}
```

**Prevention**: Always use device presets instead of manual viewport configs.

---

### 12. Ignoring Network Conditions

**Problem**: Tests work on fast WiFi but fail on real mobile networks.

**Symptoms**:
- Timeouts on slow connections
- Images don't load on 3G
- API calls fail intermittently

**Root Cause**: Not simulating realistic mobile network speeds.

**Solution**: Add network throttling to MCP config:
```javascript
// Custom config file
{
  contextOptions: {
    offline: false,
    // Simulate 3G network
    // Note: This requires custom config file, not CLI args
  }
}
```

Or test manually with Chrome DevTools network throttling.

**Prevention**: Test critical flows with "Slow 3G" network profile.

---

## Integration Pitfalls

### 13. Not Restarting IDE After Config Changes

**Problem**: MCP config changes don't take effect.

**Symptoms**:
- Added `--device` flag but still seeing desktop view
- Changed device but tests use old device
- Config looks correct but behavior is wrong

**Root Cause**: MCP server is already running and doesn't reload config automatically.

**Solution**:
1. Save config file
2. **Fully close and reopen VS Code** (or Cursor, Windsurf, etc.)
3. Verify MCP server restarted (check logs)

**Prevention**: Always restart IDE after changing MCP configuration.

---

### 14. Expecting MCP to Support Native Android Apps

**Problem**: Trying to test Android APK files with Playwright.

**Symptoms**:
- Looking for app installation features
- Trying to open `.apk` files
- Expecting to test native UI elements

**Root Cause**: Playwright tests **web browsers**, not native apps.

**Reality**:
- ✅ Playwright tests web apps in mobile browsers
- ✅ Playwright can test WebView (web content in apps)
- ❌ Playwright cannot test native Android UI (buttons, activities, etc.)

**Solution**: For native Android app testing, use:
- [Appium](https://appium.io/) - Cross-platform mobile automation
- [Maestro](https://maestro.mobile.dev/) - Modern mobile UI testing
- [Espresso](https://developer.android.com/training/testing/espresso) - Android-native testing

**Prevention**: Understand Playwright is for browser automation, not native app testing.

---

### 15. Hardcoding Desktop Selectors

**Problem**: Selectors work on desktop but fail on mobile.

**Symptoms**:
- "Element not found" errors on mobile
- Different elements appear on mobile vs desktop
- Menu structure changes between devices

**Root Cause**: Mobile sites often use different HTML structure:
- Desktop: `<div class="desktop-nav">`
- Mobile: `<div class="mobile-hamburger">`

**Solution**: Use responsive selectors or conditional logic:
```javascript
// Good: Use test IDs that work on both
await page.click('[data-testid="main-menu"]');

// Bad: Desktop-specific selector
await page.click('.desktop-sidebar-menu');
```

**Prevention**: Design test selectors to be device-agnostic, or use separate test suites.

---

## Performance & Resource Pitfalls

### 16. Not Accounting for CI/CD Resource Limits

**Problem**: Tests work locally but timeout in CI.

**Symptoms**:
- CI builds take 10x longer
- Random timeouts in CI
- Out of memory errors

**Root Cause**: CI environments have limited CPU/RAM compared to local machines.

**Solution**:
- Use device emulation, not real emulators in CI
- Increase timeouts for CI: `--timeout-navigation 90000`
- Run tests in parallel batches, not all at once
- Use headless mode: `--headless`

**Prevention**: Test your CI pipeline early with resource-constrained settings.

---

### 17. Over-Installing Emulator System Images

**Problem**: Android Studio taking 20+ GB of disk space.

**Symptoms**:
- Disk space warnings
- Slow Android Studio performance
- Multiple unused system images

**Root Cause**: Downloading too many Android API levels.

**Solution**:
1. Open Android Studio → SDK Manager
2. Go to "SDK Platforms" tab
3. Uninstall unused API levels (keep only 1-2 recent ones)
4. Keep Android 13 (API 33) for modern testing

**Prevention**: Only install what you need. One API level is enough for web testing.

---

## Summary: Top 5 Mistakes

1. **Forgetting `--device` flag** → Always include in MCP config
2. **Typos in device names** → Copy-paste exact names
3. **Mixing emulation approaches** → Choose device emulation OR real emulator
4. **Not restarting IDE** → Restart after config changes
5. **Expecting iOS Safari on Windows** → Use WebKit emulation or cloud services

---

## Quick Checklist for Success

✅ Add `--device "Pixel 5"` to MCP args  
✅ Restart IDE after config changes  
✅ Use exact device names (case-sensitive)  
✅ Test in headed mode first, headless later  
✅ Don't override viewport when using device preset  
✅ Understand emulation ≠ real device (use for speed, validate on real devices)  
✅ Use device emulation for CI/CD (fast, lightweight)  
✅ Reserve real Android emulator for Android-specific bug investigation  

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-18
