#!/usr/bin/env python3
"""
Phase 3 E2E Test: 4-Hour Broadcast Generation

Progressive scale test before full day.
Tests scheduling, cache behavior, and multi-segment generation.
"""

import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Add parent directories to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    """Run 4-hour broadcast test using broadcast.py"""
    print("=" * 60)
    print("4-HOUR BROADCAST TEST - Phase 3 E2E")
    print("=" * 60)
    
    # Setup
    output_dir = Path(PROJECT_ROOT / "output" / "e2e_tests" / "4hour_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n[SETUP] Running 4-hour broadcast...")
    print("  Command: broadcast.py --dj julie --hours 4 --enable-stories --no-validation")
    
    # Run broadcast.py
    start_time = time.time()
    
    try:
        # Change to project root directory for proper imports
        original_dir = Path.cwd()
        
        # Set UTF-8 environment for Python subprocess
        import os
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            [
                "python",
                "broadcast.py",
                "--dj", "julie",
                "--hours", "4",
                "--enable-stories",
                "--no-validation",
                "--quiet"
            ],
            cwd=str(PROJECT_ROOT),  # Run from project root
            capture_output=True,
            text=True,            encoding='utf-8',  # Handle Unicode characters
            errors='replace',  # Replace unencodable characters
            env=env,  # Pass UTF-8 environment
            timeout=600  # 10 minute timeout
        )
        
        total_time = time.time() - start_time
        
        # Analyze results
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        
        print(f"\nExit code: {result.returncode}")
        print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
        
        # Parse output
        output_lines = result.stdout.split('\n')
        
        # Count segments from output
        segment_count = len([line for line in output_lines if 'Hour' in line or 'Segment' in line])
        print(f"Segments mentioned in output: {segment_count}")
        
        # Check for errors
        if result.returncode != 0:
            print("\n❌ BROADCAST FAILED")
            print("\nStdout (last 1000 chars):")
            print(result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout)
            print("\nStderr:")
            print(result.stderr[:1000] if result.stderr else "(no stderr)")
            return False
        
        # Display output summary
        print("\nOutput preview (last 20 lines):")
        for line in output_lines[-20:]:
            if line.strip():
                print(f"  {line}")
        
        # Save results
        with open(output_dir / "output.txt", 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        with open(output_dir / "summary.txt", 'w', encoding='utf-8') as f:
            f.write(f"4-Hour Broadcast Test Summary\n")
            f.write(f"Generated: {datetime.now()}\n\n")
            f.write(f"Exit code: {result.returncode}\n")
            f.write(f"Total time: {total_time:.1f}s\n")
            f.write(f"Segments: {segment_count}\n")
        
        # Success check
        print("\n" + "=" * 60)
        success = (result.returncode == 0 and total_time < 480)  # 8 minutes max
        
        if success:
            print("✅ 4-HOUR TEST PASSED - Ready for 24-hour test")
        else:
            print("⚠️  4-HOUR TEST NEEDS REVIEW")
            if total_time >= 480:
                print("   - Generation took too long")
        print("=" * 60)
        
        return success
        
    except subprocess.TimeoutExpired:
        print("\n❌ TEST TIMED OUT (>10 minutes)")
        return False
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
