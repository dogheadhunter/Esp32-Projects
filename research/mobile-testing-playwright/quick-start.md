# Quick Start: Mobile Testing with Playwright MCP Server

**Goal**: Test your web app on a simulated Android phone using Playwright MCP server with GitHub Copilot.

**Time to Setup**: < 5 minutes  
**Difficulty**: Easy

---

## The Simple Answer

Add two lines to your MCP configuration:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--device",           // ← ADD THIS LINE
        "Pixel 5"            // ← AND THIS LINE
      ]
    }
  }
}
```

That's it! No Android emulator needed.

---

## Step-by-Step Setup

### Step 1: Find Your MCP Configuration File

Location depends on your editor:

- **VS Code**: `.vscode/mcp-settings.json` or settings UI
- **Cursor**: `.cursor/mcp-settings.json`
- **Windsurf**: `.windsurf/mcp-settings.json`
- **Claude Desktop**: `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

### Step 2: Edit Configuration

Add the `--device` argument:

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

### Step 3: Restart Your Editor

**Important**: MCP server needs to reload.

- Fully close and reopen VS Code / Cursor / Windsurf
- Or reload window: Press `Ctrl+Shift+P` → "Developer: Reload Window"

### Step 4: Test with Copilot

Ask GitHub Copilot:

```
Open https://example.com and take a screenshot
```

**Expected Result**: Screenshot should show mobile layout with ~393x851 viewport.

---

## Popular Device Presets

### Android Devices
```json
"Pixel 5"        // 393x851, modern Android
"Pixel 4"        // 353x745, mid-range Android
"Galaxy S9+"     // 320x658, Samsung device
"Galaxy Note 3"  // 360x640, older Samsung
```

### iPhone Devices (uses WebKit, not real Safari)
```json
"iPhone 13"      // 390x844, modern iPhone
"iPhone 12"      // 390x844, similar to 13
"iPhone SE"      // 375x667, smaller iPhone
```

### Tablets
```json
"iPad Pro"       // 1024x1366, large tablet
"Pixel Slate"    // 1200x1600, Android tablet
```

See full list: https://github.com/microsoft/playwright/blob/main/packages/playwright-core/src/server/deviceDescriptorsSource.json

---

## Troubleshooting

### Still Seeing Desktop View?

1. **Check config syntax**: Make sure JSON is valid (commas, quotes)
2. **Restart editor**: Close and reopen VS Code completely
3. **Check device name**: Must be exact (case-sensitive): `"Pixel 5"` not `"pixel 5"`
4. **Test manually**:
   ```bash
   npx @playwright/mcp@latest --device "Pixel 5"
   ```

### Error: "Device not found"?

- Use exact device name from Playwright registry
- Check for typos: `"Pixel 5"` not `"Pixle 5"`
- Device names are case-sensitive

### Want to Test Multiple Devices?

Create multiple MCP configurations:

```json
{
  "mcpServers": {
    "playwright-mobile": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--device", "Pixel 5"]
    },
    "playwright-tablet": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--device", "iPad Pro"]
    },
    "playwright-desktop": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

Then select which server to use in Copilot.

---

## Advanced Configuration

### With Geolocation Permission

```json
{
  "args": [
    "@playwright/mcp@latest",
    "--device", "Pixel 5",
    "--grant-permissions", "geolocation"
  ]
}
```

### With Specific Timezone

```json
{
  "args": [
    "@playwright/mcp@latest",
    "--device", "Pixel 5",
    "--grant-permissions", "geolocation"
  ]
}
```

Note: Some settings require a config file instead of CLI args. See the [full guide](./android-simulation-guide.md) for details.

---

## What You Get

With device emulation enabled:

✅ Mobile viewport size (e.g., 393x851 for Pixel 5)  
✅ Mobile user agent (browser identifies as mobile)  
✅ Touch events enabled (tap, swipe, etc.)  
✅ Mobile meta viewport handling  
✅ Mobile browser behavior  
✅ Mobile device pixel ratio  

### What You Don't Get

❌ Real Android operating system  
❌ Native Android Chrome quirks  
❌ Real hardware sensors  
❌ Actual network conditions  
❌ Native app testing  

For 90% of web app testing, device emulation is enough!

---

## Next Steps

- ✅ **Test different devices**: Try `"iPhone 13"`, `"Galaxy S9+"`, `"iPad Pro"`
- ✅ **Add to CI/CD**: Device emulation works great in CI pipelines
- 📖 **Read full guide**: See [android-simulation-guide.md](./android-simulation-guide.md) for advanced topics
- 📖 **Common mistakes**: Check [common-pitfalls.md](./common-pitfalls.md) to avoid issues

---

## When Device Emulation Isn't Enough

If you discover bugs that only appear on real Android devices (rare), see the "Real Android Emulator" section in the [full guide](./android-simulation-guide.md#solution-2-real-android-emulator-advanced).

That requires:
- Android Studio installation (~4 GB)
- ADB setup
- Running emulator (slow, resource-intensive)
- Custom Playwright code (not compatible with MCP `--device` flag)

**But start with device emulation first!** It handles 90%+ of mobile testing needs.

---

**Quick Start Version**: 1.0  
**Last Updated**: 2026-01-18
