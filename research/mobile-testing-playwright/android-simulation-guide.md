# Research: Android Phone Simulation for Playwright MCP Server

**Date**: 2026-01-18  
**Researcher**: Researcher Agent  
**Context**: User needs to test web applications on simulated Android phones using Playwright MCP server with Copilot, as desktop browser testing is not providing accurate mobile results.

---

## Executive Summary

There are **two primary approaches** for mobile testing with Playwright MCP server:

1. **Device Emulation (Recommended for most cases)**: Playwright's built-in device emulation simulates mobile browsers without needing a real Android emulator. This is fast, lightweight, and works with MCP server using the `--device` flag.

2. **Real Android Emulator**: Use Android Studio's AVD (Android Virtual Device) with Playwright's Android API for testing real Chrome browser on Android. This requires ADB setup and is more complex.

**Key Recommendation**: Start with device emulation using `--device "Pixel 5"` or similar. Only use a real Android emulator if you need to test native Android browser behavior or device-specific features.

---

## Key Findings

### Device Emulation is Built into Playwright MCP
- ✅ Playwright MCP server supports the `--device` parameter
- ✅ No Android emulator installation needed
- ✅ Fast execution and low resource usage
- ✅ Simulates viewport, user agent, touch events, and mobile browser behavior
- ✅ Works with all browsers (Chromium, Firefox, WebKit)

### Real Android Emulator Support Exists But Is Complex
- ⚠️ Requires Android Studio installation (~3-4 GB)
- ⚠️ Needs ADB (Android Debug Bridge) running
- ⚠️ Only works with Chrome browser on Android
- ⚠️ Playwright's Android support is **experimental**
- ⚠️ Not directly integrated with MCP server's device emulation

### MCP Server Already Supports Mobile Device Emulation
- The `--device` flag in Playwright MCP lets you specify devices like "iPhone 15", "Pixel 5", "Galaxy S9+"
- Configuration is simple: just add `"--device", "Pixel 5"` to the MCP args array

---

## Solution 1: Device Emulation (Recommended)

### What It Does
Playwright simulates a mobile device by:
- Setting mobile viewport size and pixel ratio
- Spoofing user agent string
- Enabling touch events
- Simulating mobile browser behavior
- Respecting mobile meta viewport tags

### How to Configure for MCP Server

#### VS Code / Copilot Configuration

Edit your MCP server configuration (usually in `.vscode/mcp-settings.json` or similar):

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--device",
        "Pixel 5"
      ]
    }
  }
}
```

#### Available Device Presets

Playwright includes 80+ device profiles. Popular Android devices:

- `"Pixel 5"` - 393x851, Android Chrome
- `"Pixel 4"` - 353x745, Android Chrome
- `"Galaxy S9+"` - 320x658, Android Chrome
- `"Galaxy Note 3"` - 360x640, Android Chrome
- `"Nexus 6"` - 412x732, Android Chrome

See full list: https://github.com/microsoft/playwright/blob/main/packages/playwright-core/src/server/deviceDescriptorsSource.json

#### Example Test Workflow with Copilot

Once configured, you can ask GitHub Copilot to:

1. "Open example.com on mobile"
2. "Click the hamburger menu"
3. "Take a screenshot"

The MCP server will automatically use the Pixel 5 emulation.

### Pros
✅ No additional software installation  
✅ Fast and lightweight  
✅ Works immediately  
✅ Cross-browser testing (Chromium, Firefox, WebKit)  
✅ Easy to switch between devices  
✅ Low resource usage  
✅ CI/CD friendly  

### Cons
❌ Not a real Android device  
❌ Doesn't catch Android browser-specific bugs  
❌ No real touch gestures (pinch, zoom physics)  
❌ Can't test native browser rendering differences  
❌ Limited to what Chromium/Firefox/WebKit can emulate  

---

## Solution 2: Real Android Emulator (Advanced)

### Prerequisites

1. **Android Studio** (3-4 GB download)
   - Download from: https://developer.android.com/studio
   - Install AVD Manager during setup
   
2. **ADB (Android Debug Bridge)**
   - Included with Android Studio
   - Must be running on port 5037 (default)

3. **Playwright's Android Support**
   - Experimental feature
   - Requires special setup

### Setup Steps for Windows

#### Step 1: Install Android Studio

1. Download Android Studio from https://developer.android.com/studio
2. Run installer with default settings
3. Open Android Studio
4. Go to **Tools → AVD Manager**
5. Click **"Create Virtual Device"**
6. Select a device (e.g., Pixel 5)
7. Download a system image (e.g., Android 13, API 33)
8. Finish setup and **start the emulator**

#### Step 2: Verify ADB Connection

Open Command Prompt or PowerShell:

```bash
# Check if ADB is in your PATH
adb version

# If not found, add to PATH:
# Usually located at: C:\Users\<YourName>\AppData\Local\Android\Sdk\platform-tools

# List connected devices
adb devices
```

You should see your AVD listed:
```
List of devices attached
emulator-5554   device
```

#### Step 3: Install Chrome on the Emulator

Open the emulator and:
1. Open Play Store
2. Install **Chrome** (version 87+)
3. Open Chrome
4. Navigate to `chrome://flags`
5. Enable **"Enable command line on non-rooted devices"**

#### Step 4: Use Playwright's Android API

Playwright's Android support is **separate from the device emulation API**. You need to write code:

```javascript
const { _android } = require('playwright');

(async () => {
  // Connect to the running Android device
  const [device] = await _android.devices();
  console.log(`Model: ${device.model()}`);
  console.log(`Serial: ${device.serial()}`);

  // Launch Chrome browser on Android
  await device.shell('am force-stop com.android.chrome');
  const context = await device.launchBrowser();

  // Use the browser context normally
  const page = await context.newPage();
  await page.goto('https://example.com');
  console.log(await page.title());
  await page.screenshot({ path: 'android-screenshot.png' });

  await context.close();
  await device.close();
})();
```

### Pros
✅ Real Android Chrome browser  
✅ Accurate device behavior  
✅ Native touch gestures  
✅ Real-world performance metrics  

### Cons
❌ Complex setup  
❌ Requires 5+ GB disk space  
❌ Slow to start (~30-60 seconds)  
❌ High resource usage (CPU, RAM)  
❌ Only works with Chrome on Android  
❌ **Not directly compatible with MCP server's device flag**  
❌ Experimental Playwright feature  

---

## Alternative Android Emulators (Not Recommended for Testing)

### Lightweight Alternatives
These are primarily for gaming/app usage, not web testing:

1. **Genymotion** (Developer-focused)
   - Pros: Fast, good for app testing
   - Cons: Paid license, complex setup for Playwright

2. **Nox Player** (Gaming-focused)
   - Pros: Lightweight, free
   - Cons: Not designed for automation testing

3. **BlueStacks** (Gaming-focused)
   - Pros: Popular, easy to use
   - Cons: Not suitable for automated testing, no ADB by default

**Verdict**: Stick with Android Studio's AVD if you need a real emulator. The alternatives are not optimized for automation testing.

---

## Comparison Matrix

| Criteria | Device Emulation | Real Android Emulator |
|----------|------------------|----------------------|
| **Setup Time** | < 1 minute | 30-60 minutes |
| **Disk Space** | ~0 MB (built-in) | 5-10 GB |
| **Execution Speed** | Fast (~seconds) | Slow (~30s startup) |
| **Resource Usage** | Low | High (CPU, RAM) |
| **Accuracy** | Good (90%) | Excellent (100%) |
| **MCP Integration** | ✅ Native (`--device`) | ❌ Requires custom code |
| **Browser Support** | Chromium, Firefox, WebKit | Chrome only |
| **Touch Gestures** | Simulated | Real |
| **CI/CD Friendly** | ✅ Yes | ⚠️ Difficult |
| **Windows Support** | ✅ Yes | ✅ Yes |
| **Maintenance** | Zero | High |

---

## Common Mistakes to Avoid

### 1. **Assuming Emulation = Real Device**
   - **Problem**: Device emulation simulates mobile behavior but doesn't replicate hardware-level differences or browser quirks specific to Android.
   - **Why it happens**: Developers trust emulation too much.
   - **Solution**: Use emulation for 90% of testing, but validate critical flows on real devices or emulators for Android-specific issues.

### 2. **Not Setting the `--device` Flag in MCP Config**
   - **Problem**: Tests run in desktop mode even though you want mobile.
   - **Why it happens**: Forgetting to add `--device` to MCP args.
   - **Solution**: Always include `"--device", "Pixel 5"` in your MCP configuration when testing mobile.

### 3. **Using the Wrong Device Name**
   - **Problem**: Playwright throws an error: "Device not found"
   - **Why it happens**: Typo in device name or using a non-existent preset.
   - **Solution**: Use exact names from Playwright's device registry (case-sensitive). Examples: `"Pixel 5"`, `"iPhone 13"`, `"Galaxy S9+"`.

### 4. **Mixing Emulation with Real Emulator Approaches**
   - **Problem**: Trying to use `--device` flag with Android Studio AVD.
   - **Why it happens**: Confusion between Playwright's device emulation and Android API.
   - **Solution**: Choose one approach. Device emulation uses `--device`. Real emulator uses Playwright's `_android.devices()` API.

### 5. **Expecting iOS Testing on Windows**
   - **Problem**: Trying to test Safari on iPhone using Windows.
   - **Why it happens**: Misunderstanding cross-platform limitations.
   - **Solution**: iOS Safari testing requires macOS or cloud services (BrowserStack, Sauce Labs). Use WebKit emulation for basic iOS testing.

### 6. **Forgetting to Enable Touch Events**
   - **Problem**: Mobile interactions don't work as expected.
   - **Why it happens**: Device emulation automatically enables touch, but custom viewport configs might not.
   - **Solution**: When using device presets, touch is automatic. For custom configs, set `hasTouch: true` and `isMobile: true`.

### 7. **Not Testing in Headed Mode First**
   - **Problem**: Headless tests fail, but you can't see why.
   - **Why it happens**: Running headless immediately without visual debugging.
   - **Solution**: Add `--headless` flag only after tests work in headed mode. For MCP, omit `--headless` to see the browser.

### 8. **Ignoring Viewport Configuration Conflicts**
   - **Problem**: Device emulation doesn't work because viewport is overridden elsewhere.
   - **Why it happens**: Multiple configuration sources (config file, CLI args, test code).
   - **Solution**: Device presets define viewport. Don't override `--viewport-size` when using `--device`.

### 9. **Not Accounting for ADB Port Conflicts (Real Emulator)**
   - **Problem**: ADB fails to connect to emulator.
   - **Why it happens**: Another process using port 5037.
   - **Solution**: Check with `netstat -ano | findstr :5037` and kill conflicting processes.

### 10. **Expecting Full Android Ecosystem**
   - **Problem**: Trying to test Android apps (APKs) instead of web apps.
   - **Why it happens**: Confusion about what Playwright tests.
   - **Solution**: Playwright tests **web browsers**, not native Android apps. For native app testing, use Appium or Maestro.

---

## Recommendations

### For Your Use Case (MCP Server + Copilot)

**Use Device Emulation** with these steps:

1. **Update your MCP configuration** to include the `--device` flag:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--device",
        "Pixel 5"
      ]
    }
  }
}
```

2. **Restart VS Code / Copilot** to apply the new configuration.

3. **Test with Copilot** by asking it to:
   - "Open https://example.com"
   - "Take a screenshot"
   - "Click the menu button"

4. **Verify mobile viewport** by checking the screenshot or asking Copilot to "get the window dimensions".

### When to Use Real Android Emulator

Only use a real Android emulator if:
- You're testing Android-specific browser bugs (e.g., Chrome on Android layout issues)
- You need to test WebView-based apps
- You're debugging performance on real hardware
- You must validate touch gesture physics

### Progressive Testing Strategy

1. **Start with device emulation** (Pixel 5, iPhone 13)
2. **Run automated tests** in CI/CD with emulation
3. **Spot-check critical flows** on real devices or emulators monthly
4. **Use cloud services** (BrowserStack, Sauce Labs) for comprehensive device matrix

---

## Configuration Examples

### Basic Mobile Testing

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--device",
        "Pixel 5"
      ]
    }
  }
}
```

### Mobile Testing with Geolocation

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--device",
        "Pixel 5",
        "--grant-permissions",
        "geolocation"
      ]
    }
  }
}
```

### Custom Viewport (Android-like)

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--viewport-size",
        "360x740"
      ]
    }
  }
}
```

Note: Using `--device` is better than custom viewport because it sets user agent, touch events, and other mobile behaviors automatically.

---

## Troubleshooting

### Issue: Copilot Still Shows Desktop View

**Symptoms**: Tests run but screenshots show desktop layout.

**Solutions**:
1. Verify `--device` flag is in MCP config
2. Restart VS Code completely
3. Check MCP server logs for errors
4. Test manually: `npx @playwright/mcp@latest --device "Pixel 5" --headless=false`

### Issue: Device Not Found Error

**Symptoms**: Error message: "Device 'Pixle 5' not found"

**Solutions**:
1. Check spelling (case-sensitive): `"Pixel 5"` not `"Pixle 5"`
2. Use exact device names from Playwright registry
3. Common devices: `"Pixel 5"`, `"Pixel 4"`, `"Galaxy S9+"`, `"iPhone 13"`

### Issue: ADB Not Found (Real Emulator)

**Symptoms**: `adb: command not found` or `'adb' is not recognized`

**Solutions**:
1. Add Android SDK platform-tools to PATH:
   ```
   C:\Users\<YourName>\AppData\Local\Android\Sdk\platform-tools
   ```
2. Restart Command Prompt/PowerShell
3. Verify: `adb version`

### Issue: Emulator Won't Start (Real Emulator)

**Symptoms**: AVD fails to launch or crashes

**Solutions**:
1. Check virtualization is enabled in BIOS (Intel VT-x or AMD-V)
2. Ensure Hyper-V is disabled (conflicts with AVD)
3. Allocate more RAM to AVD (Settings → Advanced → RAM)
4. Try a lower API level (Android 10 instead of 13)

---

## References

### Official Documentation
- [Playwright Device Emulation](https://playwright.dev/docs/emulation)
- [Playwright Android API](https://playwright.dev/docs/api/class-android)
- [Playwright MCP Server](https://github.com/microsoft/playwright-mcp)
- [Device Descriptors (Full List)](https://github.com/microsoft/playwright/blob/main/packages/playwright-core/src/server/deviceDescriptorsSource.json)

### Guides & Articles
- [Mobile Web Testing: Emulators vs Real Devices](https://medium.com/@testrig/mobile-web-testing-with-playwright-emulators-vs-real-devices-62ab3b081e16)
- [Playwright Mobile Automation Guide](https://www.perfecto.io/blog/playwright-mobile-automation)
- [Playwright MCP for Mobile Testing](https://www.getpanto.ai/blog/playwright-mcp-for-mobile-app-testing)

### Tools
- [Android Studio Download](https://developer.android.com/studio)
- [ADB Documentation](https://developer.android.com/studio/command-line/adb)

### Community
- [r/Playwright - Mobile Testing Discussion](https://www.reddit.com/r/Playwright/comments/1jc9j8k/mobile_testing/)
- [GitHub Playwright Issues](https://github.com/microsoft/playwright/issues)

---

## Next Steps

1. ✅ Update your MCP configuration with `--device "Pixel 5"`
2. ✅ Restart VS Code / Copilot
3. ✅ Test with Copilot: "Open example.com and take a screenshot"
4. ✅ Verify mobile viewport in screenshot
5. ⏭️ Explore different device presets (`"iPhone 13"`, `"Galaxy S9+"`)
6. ⏭️ Add to CI/CD pipeline with device emulation

If device emulation meets your needs (90% likely), you're done! If you discover Android-specific issues that emulation can't catch, revisit the Real Android Emulator section for advanced setup.

---

**Research Complete**: 2026-01-18  
**Status**: Ready for implementation with Device Emulation (Recommended)
