#!/usr/bin/env python3
"""
Phase 4 E2E Test: 24-Hour Broadcast Generation

Full day simulation with story arcs and scheduling.
Tests complete broadcast system under realistic load.
"""

import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Add parent directories to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    """Run 24-hour broadcast test using broadcast.py"""
    print("=" * 60)
    print("24-HOUR BROADCAST TEST - Phase 4 E2E")
    print("=" * 60)
    print("\nThis test will take approximately 15-30 minutes...")
    
    # Setup
    output_dir = Path(PROJECT_ROOT / "output" / "e2e_tests" / "24hour_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n[SETUP] Running 24-hour broadcast...")
    print("  Command: broadcast.py --dj 'Mr. New Vegas' --hours 24 --enable-stories")
    
    # Run broadcast.py
    start_time = time.time()
    
    try:
        # Set UTF-8 environment for Python subprocess
        import os
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            [
                "python",
                "-u",  # Unbuffered output
                "broadcast.py",
                "--dj", "vegas",
                "--hours", "24",
                "--enable-stories",
                "--no-validation",
                "--quiet"
            ],
            cwd=str(PROJECT_ROOT),  # Run from project root
            capture_output=False,  # Don't capture (stream to console)
            text=True,
            env=env,  # Pass UTF-8 environment
            timeout=3600  # 60 minute timeout
        )
        
        total_time = time.time() - start_time
        
        # Analyze results
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        
        print(f"\nExit code: {result.returncode}")
        print(f"Total time: {total_time/60:.1f} minutes")
        
        # Since we're streaming output, just check return code
        if result.returncode != 0:
            print("\n❌ BROADCAST FAILED")
            return False
        
        print("\n✅ BROADCAST COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        return True
        
    except subprocess.TimeoutExpired:
        print("\n❌ TEST TIMED OUT (>60 minutes)")
        return False
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
