#!/usr/bin/env python3
"""
Phase 5 E2E Test: 7-Day Extended Broadcast Generation

Production simulation and final validation.
Long-term performance and stability test.
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
    """Run 7-day broadcast test using broadcast.py"""
    print("=" * 60)
    print("7-DAY EXTENDED BROADCAST TEST - Phase 5 E2E")
    print("=" * 60)
    print("\nWARNING: This test will take 1-3 hours to complete!")
    print("Press Ctrl+C within 10 seconds to cancel...")
    
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
        return False
    
    # Setup
    output_dir = Path(PROJECT_ROOT / "output" / "e2e_tests" / "7day_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n[SETUP] Running 7-day broadcast...")
    print("  Command: broadcast.py --dj 'Three Dog' --days 7 --enable-stories")
    
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
                "broadcast.py",
                "--dj", "threedog",
                "--days", "7",
                "--enable-stories",
                "--no-validation",
                "--quiet"
            ],
            cwd=str(PROJECT_ROOT),  # Run from project root
            capture_output=True,
            text=True,
            encoding='utf-8',  # Handle Unicode characters
            errors='replace',  # Replace unencodable characters
            env=env,  # Pass UTF-8 environment
            timeout=10800  # 3 hour timeout
        )
        
        total_time = time.time() - start_time
        
        # Analyze results
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        
        print(f"\nExit code: {result.returncode}")
        print(f"Total time: {total_time/3600:.2f} hours")
        
        # Parse output
        output_lines = result.stdout.split('\n')
        
        # Count days
        day_count = len([line for line in output_lines if 'Day' in line])
        print(f"Days processed: {day_count}/7")
        
        # Check for errors
        if result.returncode != 0:
            print("\n❌ BROADCAST FAILED")
            print("\nStderr preview:")
            print(result.stderr[:1000])
            return False
        
        # Display output summary
        print("\nOutput preview (last 50 lines):")
        for line in output_lines[-50:]:
            if line.strip():
                print(f"  {line}")
        
        # Save results
        with open(output_dir / "output.txt", 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        with open(output_dir / "stderr.txt", 'w', encoding='utf-8') as f:
            f.write(result.stderr)
        
        with open(output_dir / "final_report.txt", 'w', encoding='utf-8') as f:
            f.write("7-DAY BROADCAST TEST - FINAL REPORT\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.now()}\n\n")
            f.write(f"Exit code: {result.returncode}\n")
            f.write(f"Total time: {total_time/3600:.2f} hours\n")
            f.write(f"Days processed: {day_count}\n")
            f.write(f"\nStatus: {'SUCCESS' if result.returncode == 0 else 'FAILED'}\n")
        
        # Success check
        print("\n" + "=" * 60)
        success = (
            result.returncode == 0 and 
            day_count >= 7 and
            total_time < 10800  # Less than 3 hours
        )
        
        if success:
            print("✅ 7-DAY TEST PASSED - PRODUCTION READY")
            print("\nThe broadcast engine refactoring is validated and ready for deployment.")
        else:
            print("⚠️  7-DAY TEST NEEDS REVIEW")
            if day_count < 7:
                print(f"   - Only {day_count}/7 days processed")
            if total_time >= 10800:
                print("   - Generation took too long")
        print("=" * 60)
        
        return success
        
    except subprocess.TimeoutExpired:
        print("\n❌ TEST TIMED OUT (>3 hours)")
        return False
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
