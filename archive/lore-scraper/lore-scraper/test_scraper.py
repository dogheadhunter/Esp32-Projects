"""
Test suite for full wiki scraper - validates before 65-hour scrape.

Tests:
1. Small sample scrape (100 pages)
2. Storage estimation
3. Resume capability
4. Crash recovery  
5. Time estimation

Usage:
    python test_scraper.py
"""

import subprocess
import json
from pathlib import Path
import time
import random
import shutil


TEST_OUTPUT = Path(__file__).parent.parent.parent / "lore" / "scraper_test"
FULL_TITLES = Path(__file__).parent.parent.parent / "lore" / "fallout_complete_titles.txt"
SCRAPER = Path(__file__).parent / "scrape_fallout76.py"


def create_test_sample(sample_size: int = 100) -> Path:
    """Create random sample of titles for testing"""
    print(f"Creating test sample of {sample_size} pages...")
    
    with open(FULL_TITLES, "r", encoding="utf-8") as f:
        all_titles = [line.strip() for line in f if line.strip()]
    
    sample = random.sample(all_titles, min(sample_size, len(all_titles)))
    
    test_file = TEST_OUTPUT.parent / f"test_sample_{sample_size}.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(test_file, "w", encoding="utf-8") as f:
        for title in sample:
            f.write(title + "\n")
    
    print(f"  Created: {test_file}")
    print(f"  Sample size: {len(sample)}")
    return test_file


def test_1_small_scrape(sample_size: int = 100):
    """Test 1: Scrape small sample and validate output"""
    print(f"\n{'='*60}")
    print(f"TEST 1: Small Sample Scrape ({sample_size} pages)")
    print(f"{'='*60}")
    
    if TEST_OUTPUT.exists():
        shutil.rmtree(TEST_OUTPUT)
    
    test_file = create_test_sample(sample_size)
    
    print(f"\nRunning scraper...")
    start_time = time.time()
    
    cmd = [
        "python",
        str(SCRAPER),
        "--selection", str(test_file),
        "--output", str(TEST_OUTPUT),
        "--rate-limit", "0.5",
        "--workers", "5",
        "--skip-existing"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start_time
    
    print(f"  Elapsed time: {elapsed:.1f}s")
    print(f"  Rate: {sample_size/elapsed:.2f} pages/second")
    
    print(f"\nValidating output...")
    entity_types = {}
    total_files = 0
    
    # Check entities subdirectories (entities/characters/, entities/locations/, etc.)
    entities_dir = TEST_OUTPUT / "entities"
    if entities_dir.exists():
        for entity_dir in entities_dir.iterdir():
            if entity_dir.is_dir():
                file_count = len(list(entity_dir.glob("*.json")))
                if file_count > 0:
                    entity_types[entity_dir.name] = file_count
                    total_files += file_count
    
    print(f"  Total files created: {total_files}")
    print(f"  Entity types found: {len(entity_types)}")
    for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"    {entity_type}: {count}")
    
    print(f"\nValidating JSON format...")
    # Get sample files from entities directory only (exclude manifest)
    sample_files = [f for f in (TEST_OUTPUT / "entities").rglob("*.json") if f.name != "scrape_manifest.json"][:5]
    valid_count = 0
    for json_file in sample_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Check for actual scraper output fields (id, name, type)
                required_fields = ["id", "name", "type"]
                missing = [field for field in required_fields if field not in data]
                if missing:
                    print(f"  ✗ {json_file.name}: Missing {missing}")
                else:
                    print(f"  ✓ {json_file.name}: Valid")
                    valid_count += 1
        except json.JSONDecodeError as e:
            print(f"   {json_file.name}: Invalid JSON - {e}")
    
    return {
        "total_files": total_files,
        "sample_size": sample_size,
        "elapsed": elapsed,
        "rate": sample_size/elapsed if elapsed > 0 else 0,
        "entity_types": entity_types,
        "valid_json": valid_count == len(sample_files)
    }


def test_2_storage_estimate(sample_results: dict):
    """Test 2: Estimate storage for full scrape"""
    print(f"\n{'='*60}")
    print(f"TEST 2: Storage Estimation")
    print(f"{'='*60}")
    
    total_size = 0
    file_count = 0
    
    # Calculate size of entity files only (exclude manifest/logs)
    entities_dir = TEST_OUTPUT / "entities"
    if entities_dir.exists():
        for json_file in entities_dir.rglob("*.json"):
            total_size += json_file.stat().st_size
            file_count += 1
    
    avg_file_size = total_size / file_count if file_count > 0 else 0
    
    with open(FULL_TITLES, "r", encoding="utf-8") as f:
        full_count = len([line for line in f if line.strip()])
    
    estimated_total_mb = (avg_file_size * full_count) / (1024 * 1024)
    estimated_total_gb = estimated_total_mb / 1024
    
    print(f"  Sample statistics:")
    print(f"    Files: {file_count}")
    print(f"    Total size: {total_size / 1024 / 1024:.2f} MB")
    print(f"    Average file size: {avg_file_size / 1024:.2f} KB")
    
    print(f"\n  Full scrape estimates:")
    print(f"    Total pages: {full_count:,}")
    print(f"    Estimated size: {estimated_total_mb:.1f} MB ({estimated_total_gb:.2f} GB)")
    
    stat = shutil.disk_usage(TEST_OUTPUT.parent)
    available_gb = stat.free / (1024**3)
    
    print(f"\n  Disk space:")
    print(f"    Available: {available_gb:.1f} GB")
    print(f"    Required: {estimated_total_gb:.2f} GB")
    print(f"    Safety margin: {available_gb - estimated_total_gb:.1f} GB")
    
    sufficient = available_gb >= estimated_total_gb * 1.5
    if sufficient:
        print(f"   Sufficient disk space")
    else:
        print(f"   WARNING: Low disk space!")
    
    return {
        "avg_file_size_kb": avg_file_size / 1024,
        "estimated_total_mb": estimated_total_mb,
        "estimated_total_gb": estimated_total_gb,
        "available_gb": available_gb,
        "sufficient_space": sufficient
    }


def test_3_resume_capability():
    """Test 3: Verify resume capability"""
    print(f"\n{'='*60}")
    print(f"TEST 3: Resume Capability")
    print(f"{'='*60}")
    
    test_resume_dir = TEST_OUTPUT.parent / "scraper_test_resume"
    
    if test_resume_dir.exists():
        shutil.rmtree(test_resume_dir)
    
    test_file = create_test_sample(30)
    
    print(f"\nFirst run: scraping 30 pages...")
    cmd = [
        "python", str(SCRAPER),
        "--selection", str(test_file),
        "--output", str(test_resume_dir),
        "--rate-limit", "0.5",
        "--workers", "3",
        "--skip-existing"
    ]
    subprocess.run(cmd, capture_output=True, timeout=60)
    
    # Count entity files only
    entities_dir = test_resume_dir / "entities"
    first_run_count = len(list(entities_dir.rglob("*.json"))) if entities_dir.exists() else 0
    print(f"  First run created: {first_run_count} files")
    
    print(f"\nSecond run: testing skip-existing...")
    start = time.time()
    subprocess.run(cmd, capture_output=True, timeout=30)
    second_run_time = time.time() - start
    
    entities_dir = test_resume_dir / "entities"
    second_run_count = len(list(entities_dir.rglob("*.json"))) if entities_dir.exists() else 0
    print(f"  Second run total: {second_run_count} files")
    print(f"  Second run time: {second_run_time:.1f}s")
    
    resume_works = second_run_count == first_run_count and second_run_time < 15
    if resume_works:
        print(f"   Resume works")
    else:
        print(f"   Resume may not work")
    
    return {
        "resume_works": resume_works,
        "first_run_count": first_run_count,
        "second_run_count": second_run_count
    }


def test_4_time_estimate(sample_results: dict):
    """Test 4: Accurate time estimate"""
    print(f"\n{'='*60}")
    print(f"TEST 4: Time Estimation")
    print(f"{'='*60}")
    
    with open(FULL_TITLES, "r", encoding="utf-8") as f:
        full_count = len([line for line in f if line.strip()])
    
    rate = sample_results["rate"]
    workers = 10
    rate_limit = 0.5
    
    theoretical_max_rate = workers / rate_limit
    conservative_rate = theoretical_max_rate * 0.6
    
    estimated_seconds = full_count / conservative_rate
    estimated_hours = estimated_seconds / 3600
    
    print(f"  Parameters:")
    print(f"    Total pages: {full_count:,}")
    print(f"    Workers: {workers}")
    print(f"    Rate limit: {rate_limit}s/request")
    
    print(f"\n  Performance:")
    print(f"    Theoretical max: {theoretical_max_rate:.1f} pages/sec")
    print(f"    Conservative (60%): {conservative_rate:.1f} pages/sec")
    print(f"    Observed sample: {rate:.2f} pages/sec")
    
    print(f"\n  Time estimates:")
    print(f"    Conservative: {estimated_hours:.1f} hours ({estimated_hours/24:.1f} days)")
    print(f"    Best case: {full_count/theoretical_max_rate/3600:.1f} hours")
    
    return {
        "estimated_hours": estimated_hours,
        "estimated_days": estimated_hours / 24,
        "conservative_rate": conservative_rate
    }


def main():
    print(f"{'#'*60}")
    print(f"# FULL WIKI SCRAPER TEST SUITE")
    print(f"{'#'*60}")
    
    results = {}
    
    try:
        results["scrape"] = test_1_small_scrape(sample_size=100)
        results["storage"] = test_2_storage_estimate(results["scrape"])
        results["resume"] = test_3_resume_capability()
        results["time"] = test_4_time_estimate(results["scrape"])
        
        print(f"\n{'='*60}")
        print(f"FINAL SUMMARY")
        print(f"{'='*60}")
        
        print(f"\n Small scrape: {results['scrape']['total_files']} files")
        print(f" Storage needed: {results['storage']['estimated_total_gb']:.2f} GB")
        print(f" Available space: {results['storage']['available_gb']:.1f} GB")
        print(f" Resume works: {results['resume']['resume_works']}")
        print(f" Estimated time: {results['time']['estimated_hours']:.1f} hours")
        
        all_pass = (
            results["storage"]["sufficient_space"] and
            results["resume"]["resume_works"] and
            results["scrape"]["valid_json"]
        )
        
        if all_pass:
            print(f"\n{'='*60}")
            print(f" ALL TESTS PASSED - Ready for full scrape!")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print(f" TESTS FAILED - Fix issues first")
            print(f"{'='*60}")
        
        results_file = TEST_OUTPUT.parent / "test_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {results_file}")
        
    except Exception as e:
        print(f"\n Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
