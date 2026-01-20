# ESP32 AI Radio - Quick Start with Wizard

## 🎯 Interactive Wizard (Easiest Way!)

The quickest way to get started is using the interactive wizard:

```bash
python wizard.py
```

The wizard provides a user-friendly menu interface for:
- ✅ Initial setup and dependency installation
- ✅ Running tests (quick, unit, integration, coverage)
- ✅ Database management (ingest, backup, restore)
- ✅ Generating broadcast content
- ✅ Development tools (formatting, linting, type checking)
- ✅ System information and status checks

### Quick Actions

```bash
# Run setup wizard
python wizard.py --setup

# Quick test run (bypass menu)
python wizard.py --quick-test

# Disable colors (for older terminals)
python wizard.py --no-color
```

## 📋 Menu Structure

### 1. Initial Setup & Installation
- Check Python version (requires 3.10+)
- Verify dependencies (pytest, chromadb, ollama, etc.)
- Install missing packages
- Check database status

### 2. Run Tests
- Quick Tests (fast, mock-only)
- Unit Tests (all unit tests)
- Integration Tests (requires Ollama/ChromaDB)
- Full Test Suite
- Coverage Report
- Specific Test File

### 3. Database Management
- Ingest Fallout Wiki (2-3 hours, requires internet)
- Fresh Ingest (delete existing, then ingest)
- Backup Database (compressed)
- Restore Database
- Quick Backup (fast, no compression)
- Check Database Status

### 4. Generate Broadcast Content
- Guided Generation (step-by-step)
- Quick Generate (Julie, 1 hour)
- Multi-Day Broadcast (7 days)
- View Available DJs
- Advanced Options

### 5. Development Tools
- Format Code (Black)
- Sort Imports (isort)
- Lint Code (Ruff)
- Type Check (MyPy)
- Run All Quality Checks
- View Test Logs

### 6. View Documentation
- Quick links to all project documentation

### 7. System Information
- Python version and platform
- Dependency status
- Project paths

## 🎨 Features

- **Color-coded output** for better readability (auto-disables on older terminals)
- **Error handling** with helpful messages
- **Confirmation prompts** for destructive operations
- **Status indicators** (✓ success, ✗ error, ⚠ warning, ℹ info)
- **Navigation** with 'b' for back, 'q' for quit
- **Quick actions** via command-line flags

## 🚀 Common Workflows

### First Time Setup
```bash
python wizard.py --setup
```
Follow the wizard to install dependencies and check your setup.

### Daily Development
```bash
python wizard.py
# Select: 2 (Run Tests) → 1 (Quick Tests)
```

### Generating Content
```bash
python wizard.py
# Select: 4 (Generate Broadcast) → 2 (Quick Generate)
```

### Before Committing Code
```bash
python wizard.py
# Select: 5 (Development Tools) → 5 (Run All Quality Checks)
```

## 📝 Notes

- The wizard works on Windows, Linux, and macOS
- Colors automatically disable on Windows (unless using Windows Terminal)
- All operations can still be run manually via command line
- The wizard is a convenience layer - it doesn't replace direct script access

## 🔗 Alternative: Direct Commands

If you prefer command-line interface:

```bash
# Testing
python run_tests.py                    # All tests
python run_tests.py quick              # Quick tests
python run_tests.py coverage           # With coverage

# Database (Windows)
scripts\ingest_wiki.bat                # Ingest wiki
scripts\backup_database.bat            # Backup

# Content Generation
python broadcast.py --dj Julie --hours 24

# Development
black tools/ tests/                    # Format code
pytest tools/ -v                       # Run tests
```

See [README.md](README.md) for full documentation.
