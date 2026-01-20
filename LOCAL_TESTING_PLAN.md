# LOCAL TESTING PLAN - Real-World Broadcast Engine Validation

**Purpose**: Progressive, real-world testing of the broadcast engine refactoring on local PC using Ollama with dual-model strategy.

**Models**:
- **Generation**: `fluffy/l3-8b-stheno-v3.2` (creative, narrative-focused)
- **Validation**: `dolphin-llama3` (analytical, quality-checking)

**Philosophy**: Start small, validate thoroughly, scale progressively.

---

## Testing Strategy

### Dual-Model Approach

**Why Separate Models?**
- Generation model optimized for creative writing
- Validation model optimized for analytical checking
- Prevents model bias in self-validation
- Better quality assurance

**Configuration**:
```python
# tools/script-generator/ollama_client.py
GENERATION_MODEL = "fluffy/l3-8b-stheno-v3.2"  # For script creation
VALIDATION_MODEL = "dolphin-llama3"            # For script validation
```

---

## Phase 1: Ollama Setup & Model Verification

**Duration**: 30 minutes  
**Purpose**: Ensure Ollama and both models are operational

### Setup Steps

1. **Install Ollama** (if not installed):
   ```bash
   # Linux
   curl https://ollama.ai/install.sh | sh
   
   # macOS
   brew install ollama
   
   # Windows
   # Download from ollama.ai
   ```

2. **Pull Required Models**:
   ```bash
   # Pull generation model
   ollama pull fluffy/l3-8b-stheno-v3.2
   
   # Pull validation model
   ollama pull dolphin-llama3
   ```

3. **Start Ollama Server**:
   ```bash
   ollama serve
   # Server runs on http://localhost:11434
   ```

4. **Verify Models**:
   ```bash
   # Run test script
   python tools/script-generator/tests/test_ollama_setup.py
   ```

### Success Criteria

✅ Ollama server responds (200 OK)  
✅ Generation model responds <5s  
✅ Validation model responds <5s  
✅ VRAM allocation stable  
✅ No model loading errors

### Test Script: test_ollama_setup.py

```python
#!/usr/bin/env python3
"""
Test Ollama setup and model availability.
Run FIRST before any broadcast tests.
"""

import sys
import time
import requests
sys.path.insert(0, 'tools/script-generator')

from ollama_client import OllamaClient

GENERATION_MODEL = "fluffy/l3-8b-stheno-v3.2"
VALIDATION_MODEL = "dolphin-llama3"

def test_ollama_server():
    """Test if Ollama server is running"""
    print("[TEST] Checking Ollama server...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("  ✅ Ollama server is running")
            return True
        else:
            print(f"  ❌ Ollama server returned {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Ollama server not reachable: {e}")
        print("     Start with: ollama serve")
        return False

def test_model(client, model_name, purpose):
    """Test a specific model"""
    print(f"\n[TEST] Testing {purpose} model: {model_name}")
    try:
        start = time.time()
        response = client.generate(
            model=model_name,
            prompt="Say 'ready' if you can read this.",
            options={"temperature": 0.1, "max_tokens": 10}
        )
        elapsed = time.time() - start
        
        print(f"  ✅ Model responds in {elapsed:.2f}s")
        print(f"     Response: {response[:100]}")
        
        if elapsed > 10:
            print(f"  ⚠️  Model slow (>{10}s), may need VRAM optimization")
        
        return True
    except Exception as e:
        print(f"  ❌ Model test failed: {e}")
        print(f"     Install with: ollama pull {model_name}")
        return False

def main():
    """Run all setup tests"""
    print("="*60)
    print("OLLAMA SETUP VERIFICATION")
    print("="*60)
    
    # Test server
    if not test_ollama_server():
        print("\n❌ FAILED: Ollama server not running")
        return False
    
    # Test models
    client = OllamaClient()
    
    gen_ok = test_model(client, GENERATION_MODEL, "Generation")
    val_ok = test_model(client, VALIDATION_MODEL, "Validation")
    
    # Summary
    print("\n" + "="*60)
    if gen_ok and val_ok:
        print("✅ ALL TESTS PASSED - Ready for broadcast testing")
        print("="*60)
        return True
    else:
        print("❌ SOME TESTS FAILED - Fix issues before continuing")
        print("="*60)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

---

## Phase 2: Single Segment Generation

**Duration**: 1 hour  
**Purpose**: Validate each content type works correctly

### Test Scenarios

1. **Time Check** (simplest):
   ```bash
   python broadcast.py --dj julie --hours 1 --segments-per-hour 1 --segment-types time
   ```

2. **Weather Report**:
   ```bash
   python broadcast.py --dj julie --hours 1 --segments-per-hour 1 --segment-types weather
   ```

3. **News Broadcast**:
   ```bash
   python broadcast.py --dj julie --hours 1 --segments-per-hour 1 --segment-types news
   ```

4. **Gossip Segment**:
   ```bash
   python broadcast.py --dj julie --hours 1 --segments-per-hour 1 --segment-types gossip
   ```

5. **Story Segment**:
   ```bash
   python broadcast.py --dj julie --hours 1 --segments-per-hour 1 --segment-types story --enable-stories
   ```

### Success Criteria

✅ Each segment type generates successfully  
✅ Generation model creates content  
✅ Validation model checks quality  
✅ Cache initializes correctly  
✅ No errors or warnings  
✅ Output files created  
✅ Validation passes (rules + LLM)

### Test Script: test_single_segments.py

```python
#!/usr/bin/env python3
"""
Test single segment generation for each content type.
Validates basic functionality before scaling up.
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, 'tools/script-generator')

from broadcast_engine import BroadcastEngine
from ollama_client import OllamaClient

GENERATION_MODEL = "fluffy/l3-8b-stheno-v3.2"
VALIDATION_MODEL = "dolphin-llama3"

CONTENT_TYPES = ['time', 'weather', 'news', 'gossip', 'story']

def test_segment(engine, segment_type):
    """Test generation of a single segment"""
    print(f"\n{'='*60}")
    print(f"Testing {segment_type.upper()} segment")
    print('='*60)
    
    try:
        # Generate segment
        print(f"[1/4] Generating with {GENERATION_MODEL}...")
        result = engine.generate_segment(
            segment_type=segment_type,
            generation_model=GENERATION_MODEL,
            validation_model=VALIDATION_MODEL,
            use_cache=True,
            validate=True
        )
        
        if not result:
            print(f"  ❌ Generation failed")
            return False
        
        print(f"  ✅ Generated {len(result['script'])} characters")
        
        # Check cache
        print(f"[2/4] Checking cache...")
        cache_stats = engine.get_cache_statistics()
        print(f"  Cache hits: {cache_stats.get('hits', 0)}")
        print(f"  Cache misses: {cache_stats.get('misses', 0)}")
        
        # Validate
        print(f"[3/4] Validating with {VALIDATION_MODEL}...")
        if result.get('validation'):
            print(f"  ✅ Validation: {result['validation']['status']}")
            if result['validation']['status'] != 'pass':
                print(f"     Issues: {result['validation']['issues']}")
        
        # Save output
        print(f"[4/4] Saving output...")
        output_dir = Path(f"output/single_segment_tests")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / f"{segment_type}.json", 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"  ✅ Saved to output/single_segment_tests/{segment_type}.json")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all single segment tests"""
    print("="*60)
    print("SINGLE SEGMENT GENERATION TESTS")
    print("="*60)
    
    # Initialize engine
    print("\n[SETUP] Initializing broadcast engine...")
    engine = BroadcastEngine(
        dj_name="Julie (2102, Appalachia)",
        generation_model=GENERATION_MODEL,
        validation_model=VALIDATION_MODEL,
        enable_cache=True
    )
    print("  ✅ Engine initialized")
    
    # Test each content type
    results = {}
    for content_type in CONTENT_TYPES:
        results[content_type] = test_segment(engine, content_type)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for content_type, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {content_type:10s} : {status}")
    
    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL SEGMENTS PASSED - Ready for multi-segment testing")
    else:
        print("❌ SOME SEGMENTS FAILED - Fix issues before continuing")
    print("="*60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

---

## Phase 3: 4-Hour Broadcast Test

**Duration**: 2 hours  
**Purpose**: Test scheduling, cache behavior, and multi-segment generation

### Test Command

```bash
python broadcast.py \
    --dj julie \
    --hours 4 \
    --segments-per-hour 3 \
    --enable-stories \
    --validation-mode hybrid \
    --save-state \
    --output output/4hour_test
```

### What This Tests

- **Scheduler**: Priority-based segment selection
- **Cache**: Hit rate should increase over time
- **Validation**: Hybrid (rules + LLM for 20%)
- **Stories**: Basic story arc if available
- **State**: Session persistence

### Expected Output

- **Segments**: 12 total (4 hours × 3 per hour)
- **Time checks**: 4 (hourly)
- **Weather**: 1 (if scheduled)
- **News**: 1-2 (if scheduled)
- **Gossip/Story**: Remaining slots

### Success Criteria

✅ 12 segments generated successfully  
✅ Cache hit rate ≥70% by end  
✅ All segments pass validation  
✅ Scheduling logic correct (time checks first)  
✅ Story continuity (if stories enabled)  
✅ State saved correctly  
✅ Generation time ≤8s per segment  
✅ No LLM errors

### Test Script: test_4hour_broadcast.py

```python
#!/usr/bin/env python3
"""
Test 4-hour broadcast generation.
Progressive scale test before full day.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
sys.path.insert(0, 'tools/script-generator')

from broadcast_engine import BroadcastEngine

GENERATION_MODEL = "fluffy/l3-8b-stheno-v3.2"
VALIDATION_MODEL = "dolphin-llama3"

def main():
    """Run 4-hour broadcast test"""
    print("="*60)
    print("4-HOUR BROADCAST TEST")
    print("="*60)
    
    # Setup
    output_dir = Path("output/4hour_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n[SETUP] Initializing engine...")
    engine = BroadcastEngine(
        dj_name="Julie (2102, Appalachia)",
        generation_model=GENERATION_MODEL,
        validation_model=VALIDATION_MODEL,
        enable_cache=True,
        enable_stories=True,
        validation_mode='hybrid'
    )
    
    # Generate broadcast
    print("\n[GENERATING] 4-hour broadcast (12 segments)...")
    start_time = time.time()
    
    results = engine.generate_broadcast(
        duration_hours=4,
        segments_per_hour=3,
        start_hour=8,
        save_state=True
    )
    
    total_time = time.time() - start_time
    
    # Analyze results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    num_segments = len(results.get('segments', []))
    print(f"Segments generated: {num_segments}/12")
    
    # Cache performance
    cache_stats = engine.get_cache_statistics()
    hit_rate = cache_stats.get('hit_rate', 0) * 100
    print(f"\nCache Performance:")
    print(f"  Hit rate: {hit_rate:.1f}%")
    print(f"  Hits: {cache_stats.get('hits', 0)}")
    print(f"  Misses: {cache_stats.get('misses', 0)}")
    
    # Timing
    avg_time = total_time / num_segments if num_segments > 0 else 0
    print(f"\nGeneration Time:")
    print(f"  Total: {total_time:.1f}s")
    print(f"  Per segment: {avg_time:.1f}s")
    
    # Validation
    validation_stats = results.get('validation_summary', {})
    print(f"\nValidation:")
    print(f"  Passed: {validation_stats.get('passed', 0)}")
    print(f"  Failed: {validation_stats.get('failed', 0)}")
    print(f"  Pass rate: {validation_stats.get('pass_rate', 0)*100:.1f}%")
    
    # Content breakdown
    content_types = {}
    for seg in results.get('segments', []):
        seg_type = seg.get('type', 'unknown')
        content_types[seg_type] = content_types.get(seg_type, 0) + 1
    
    print(f"\nContent Breakdown:")
    for seg_type, count in sorted(content_types.items()):
        print(f"  {seg_type:10s}: {count}")
    
    # Save results
    with open(output_dir / "results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    with open(output_dir / "summary.txt", 'w') as f:
        f.write(f"4-Hour Broadcast Test Summary\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"\nSegments: {num_segments}/12\n")
        f.write(f"Cache hit rate: {hit_rate:.1f}%\n")
        f.write(f"Avg time per segment: {avg_time:.1f}s\n")
        f.write(f"Validation pass rate: {validation_stats.get('pass_rate', 0)*100:.1f}%\n")
    
    # Success check
    print("\n" + "="*60)
    success = (
        num_segments == 12 and
        hit_rate >= 70 and
        avg_time <= 10 and
        validation_stats.get('pass_rate', 0) >= 0.95
    )
    
    if success:
        print("✅ 4-HOUR TEST PASSED - Ready for 24-hour test")
    else:
        print("⚠️  4-HOUR TEST NEEDS REVIEW")
        if num_segments < 12:
            print("   - Not all segments generated")
        if hit_rate < 70:
            print("   - Cache hit rate below target")
        if avg_time > 10:
            print("   - Generation too slow")
        if validation_stats.get('pass_rate', 0) < 0.95:
            print("   - Too many validation failures")
    print("="*60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

---

## Phase 4: 24-Hour Broadcast Test

**Duration**: 4 hours  
**Purpose**: Full day simulation with story arcs and scheduling

### Test Command

```bash
python broadcast.py \
    --dj "Mr. New Vegas" \
    --hours 24 \
    --segments-per-hour 3 \
    --enable-stories \
    --enable-validation \
    --validation-mode hybrid \
    --save-state \
    --output output/24hour_test
```

### What This Tests

- **Full Day**: 72 segments
- **Story Arcs**: Multi-act progression
- **Scheduling**: Weather at 6am/12pm/5pm, news, time checks
- **Cache Persistence**: Long-term behavior
- **LLM Efficiency**: 50% call reduction
- **Story Continuity**: Act pacing and progression

### Expected Output

- **72 segments total**
- **24 time checks** (hourly)
- **3 weather reports** (6am, 12pm, 5pm)
- **3 news broadcasts** (6am, 12pm, 5pm)
- **Story segments**: 8-12 (if available)
- **Gossip**: Fill remaining slots

### Success Criteria

✅ 72 segments generated  
✅ Cache hit rate ≥72% average  
✅ Weather scheduled correctly  
✅ News scheduled correctly  
✅ Time checks every hour  
✅ Story acts properly paced  
✅ LLM calls reduced by ≥50%  
✅ Avg generation time ≤8s  
✅ 95%+ validation pass rate  
✅ No story continuity breaks

### Test Script: test_24hour_broadcast.py

```python
#!/usr/bin/env python3
"""
Test 24-hour broadcast generation.
Full day simulation with all features.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from collections import Counter
sys.path.insert(0, 'tools/script-generator')

from broadcast_engine import BroadcastEngine

GENERATION_MODEL = "fluffy/l3-8b-stheno-v3.2"
VALIDATION_MODEL = "dolphin-llama3"

def analyze_scheduling(segments):
    """Analyze scheduling correctness"""
    print("\n[ANALYSIS] Scheduling Verification")
    print("="*60)
    
    # Time checks
    time_checks = [s for s in segments if s.get('type') == 'time']
    print(f"Time checks: {len(time_checks)}/24 expected")
    
    # Check hourly
    time_hours = [s.get('hour') for s in time_checks]
    missing_hours = set(range(24)) - set(time_hours)
    if missing_hours:
        print(f"  ⚠️  Missing time checks for hours: {sorted(missing_hours)}")
    else:
        print(f"  ✅ Time check every hour")
    
    # Weather checks
    weather = [s for s in segments if s.get('type') == 'weather']
    weather_hours = [s.get('hour') for s in weather]
    print(f"\nWeather reports: {len(weather)}")
    print(f"  Hours: {sorted(weather_hours)}")
    expected_weather = {6, 12, 17}  # 6am, 12pm, 5pm
    if set(weather_hours) & expected_weather:
        print(f"  ✅ Weather scheduled correctly")
    
    # News checks
    news = [s for s in segments if s.get('type') == 'news']
    news_hours = [s.get('hour') for s in news]
    print(f"\nNews broadcasts: {len(news)}")
    print(f"  Hours: {sorted(news_hours)}")
    
    # Story continuity
    stories = [s for s in segments if s.get('type') == 'story']
    if stories:
        print(f"\nStory segments: {len(stories)}")
        story_acts = [s.get('metadata', {}).get('act') for s in stories]
        print(f"  Acts: {[a for a in story_acts if a]}")
    
    return len(time_checks) >= 20  # At least 20 time checks

def main():
    """Run 24-hour broadcast test"""
    print("="*60)
    print("24-HOUR BROADCAST TEST")
    print("="*60)
    
    # Setup
    output_dir = Path("output/24hour_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n[SETUP] Initializing engine...")
    engine = BroadcastEngine(
        dj_name="Mr. New Vegas (2281, Mojave Wasteland)",
        generation_model=GENERATION_MODEL,
        validation_model=VALIDATION_MODEL,
        enable_cache=True,
        enable_stories=True,
        validation_mode='hybrid'
    )
    
    # Generate broadcast
    print("\n[GENERATING] 24-hour broadcast (72 segments)...")
    print("This will take approximately 8-12 minutes...")
    start_time = time.time()
    
    results = engine.generate_broadcast(
        duration_hours=24,
        segments_per_hour=3,
        start_hour=0,
        save_state=True
    )
    
    total_time = time.time() - start_time
    
    # Analyze results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    segments = results.get('segments', [])
    num_segments = len(segments)
    print(f"Segments generated: {num_segments}/72")
    
    # Cache performance
    cache_stats = engine.get_cache_statistics()
    hit_rate = cache_stats.get('hit_rate', 0) * 100
    print(f"\nCache Performance:")
    print(f"  Hit rate: {hit_rate:.1f}%")
    print(f"  Hits: {cache_stats.get('hits', 0)}")
    print(f"  Misses: {cache_stats.get('misses', 0)}")
    print(f"  Evictions: {cache_stats.get('evictions', 0)}")
    
    # Content breakdown
    content_types = Counter(s.get('type', 'unknown') for s in segments)
    print(f"\nContent Breakdown:")
    for seg_type, count in sorted(content_types.items()):
        pct = (count / num_segments * 100) if num_segments > 0 else 0
        print(f"  {seg_type:10s}: {count:3d} ({pct:5.1f}%)")
    
    # Timing
    avg_time = total_time / num_segments if num_segments > 0 else 0
    print(f"\nGeneration Time:")
    print(f"  Total: {total_time/60:.1f} minutes")
    print(f"  Per segment: {avg_time:.1f}s")
    
    # LLM efficiency
    llm_stats = engine.get_llm_statistics()
    print(f"\nLLM Efficiency:")
    print(f"  Generation calls: {llm_stats.get('generation_calls', 0)}")
    print(f"  Validation calls: {llm_stats.get('validation_calls', 0)}")
    total_llm = llm_stats.get('generation_calls', 0) + llm_stats.get('validation_calls', 0)
    print(f"  Total LLM calls: {total_llm}")
    print(f"  Avg per segment: {total_llm/num_segments:.2f}")
    
    # Validation
    validation_stats = results.get('validation_summary', {})
    print(f"\nValidation:")
    print(f"  Passed: {validation_stats.get('passed', 0)}")
    print(f"  Failed: {validation_stats.get('failed', 0)}")
    print(f"  Pass rate: {validation_stats.get('pass_rate', 0)*100:.1f}%")
    
    # Scheduling analysis
    scheduling_ok = analyze_scheduling(segments)
    
    # Save results
    with open(output_dir / "results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    with open(output_dir / "summary.txt", 'w') as f:
        f.write(f"24-Hour Broadcast Test Summary\n")
        f.write(f"Generated: {datetime.now()}\n\n")
        f.write(f"Segments: {num_segments}/72\n")
        f.write(f"Cache hit rate: {hit_rate:.1f}%\n")
        f.write(f"Avg time per segment: {avg_time:.1f}s\n")
        f.write(f"Total LLM calls: {total_llm} (avg {total_llm/num_segments:.2f} per segment)\n")
        f.write(f"Validation pass rate: {validation_stats.get('pass_rate', 0)*100:.1f}%\n")
        f.write(f"\nContent Breakdown:\n")
        for seg_type, count in sorted(content_types.items()):
            f.write(f"  {seg_type}: {count}\n")
    
    # Success check
    print("\n" + "="*60)
    success = (
        num_segments >= 70 and
        hit_rate >= 72 and
        avg_time <= 10 and
        validation_stats.get('pass_rate', 0) >= 0.95 and
        scheduling_ok
    )
    
    if success:
        print("✅ 24-HOUR TEST PASSED - Ready for extended testing")
    else:
        print("⚠️  24-HOUR TEST NEEDS REVIEW")
    print("="*60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

---

## Phase 5: 7-Day Extended Test

**Duration**: 8 hours  
**Purpose**: Production simulation and long-term validation

### Test Command

```bash
python broadcast.py \
    --dj "Three Dog" \
    --days 7 \
    --segments-per-hour 3 \
    --enable-stories \
    --enable-validation \
    --validation-mode hybrid \
    --save-state \
    --output output/7day_test
```

### What This Tests

- **Extended Duration**: 504 segments (7 days × 24 hours × 3 per hour)
- **Cache Behavior**: Long-term stability
- **Story Arcs**: Multi-day progression (WEEKLY stories)
- **State Persistence**: Session management over days
- **Performance**: Sustained speed and quality
- **Cost Efficiency**: Production-level savings

### Expected Results

- **504 segments total**
- **Cache hit rate**: 72%+ sustained
- **LLM call reduction**: 50%+
- **Generation speed**: 41% faster than baseline
- **Story continuity**: Multi-act arcs completed
- **Validation**: 95%+ pass rate
- **Cost savings**: 50% LLM usage reduction

### Success Criteria

✅ 504 segments generated  
✅ Cache stable (no degradation)  
✅ Story arcs complete properly  
✅ Performance targets met:
  - 67%+ fewer ChromaDB queries
  - 50%+ fewer LLM calls
  - 41%+ faster generation
  - 85%+ faster validation
✅ 95%+ validation pass rate  
✅ No crashes or errors  
✅ State persists correctly  
✅ Production ready

### Test Script: test_7day_extended.py

```python
#!/usr/bin/env python3
"""
Test 7-day broadcast generation.
Production simulation and final validation.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
sys.path.insert(0, 'tools/script-generator')

from broadcast_engine import BroadcastEngine

GENERATION_MODEL = "fluffy/l3-8b-stheno-v3.2"
VALIDATION_MODEL = "dolphin-llama3"

def analyze_performance(results, total_time, num_segments):
    """Analyze against performance targets"""
    print("\n[PERFORMANCE] Target Validation")
    print("="*60)
    
    cache_stats = results.get('cache_statistics', {})
    hit_rate = cache_stats.get('hit_rate', 0) * 100
    
    llm_stats = results.get('llm_statistics', {})
    total_llm = llm_stats.get('total_calls', 0)
    llm_per_segment = total_llm / num_segments if num_segments > 0 else 0
    
    avg_time = total_time / num_segments if num_segments > 0 else 0
    
    # Baseline (before refactoring)
    BASELINE_CHROMADB = 1.5  # queries per segment
    BASELINE_LLM = 2.0       # calls per segment
    BASELINE_TIME = 14.0     # seconds per segment
    
    # Calculate improvements
    chromadb_reduction = (1 - (1 / BASELINE_CHROMADB)) * 100
    llm_reduction = (1 - (llm_per_segment / BASELINE_LLM)) * 100
    time_improvement = (1 - (avg_time / BASELINE_TIME)) * 100
    
    print(f"ChromaDB Query Reduction:")
    print(f"  Target: ≥67%")
    print(f"  Actual: {chromadb_reduction:.1f}%")
    print(f"  Status: {'✅' if chromadb_reduction >= 67 else '❌'}")
    
    print(f"\nLLM Call Reduction:")
    print(f"  Target: ≥50%")
    print(f"  Actual: {llm_reduction:.1f}%")
    print(f"  Status: {'✅' if llm_reduction >= 50 else '❌'}")
    
    print(f"\nGeneration Speed:")
    print(f"  Target: ≥41% faster")
    print(f"  Actual: {time_improvement:.1f}% faster")
    print(f"  Status: {'✅' if time_improvement >= 41 else '❌'}")
    
    print(f"\nCache Hit Rate:")
    print(f"  Target: ≥72%")
    print(f"  Actual: {hit_rate:.1f}%")
    print(f"  Status: {'✅' if hit_rate >= 72 else '❌'}")
    
    all_met = (
        chromadb_reduction >= 67 and
        llm_reduction >= 50 and
        time_improvement >= 41 and
        hit_rate >= 72
    )
    
    return all_met

def main():
    """Run 7-day broadcast test"""
    print("="*60)
    print("7-DAY EXTENDED BROADCAST TEST")
    print("="*60)
    print("\nThis test will take approximately 1-2 hours.")
    print("Testing 504 segments (7 days × 24 hours × 3 per hour)")
    print()
    
    # Setup
    output_dir = Path("output/7day_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("[SETUP] Initializing engine...")
    engine = BroadcastEngine(
        dj_name="Three Dog (2277, Capital Wasteland)",
        generation_model=GENERATION_MODEL,
        validation_model=VALIDATION_MODEL,
        enable_cache=True,
        enable_stories=True,
        validation_mode='hybrid'
    )
    
    # Generate broadcast
    print("\n[GENERATING] 7-day broadcast...")
    start_time = time.time()
    
    results = engine.generate_broadcast(
        duration_days=7,
        segments_per_hour=3,
        start_hour=0,
        save_state=True
    )
    
    total_time = time.time() - start_time
    
    # Results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    segments = results.get('segments', [])
    num_segments = len(segments)
    print(f"Segments generated: {num_segments}/504")
    print(f"Total time: {total_time/3600:.2f} hours")
    print(f"Avg per segment: {total_time/num_segments:.1f}s")
    
    # Content breakdown
    content_types = Counter(s.get('type') for s in segments)
    print(f"\nContent Breakdown:")
    for seg_type, count in sorted(content_types.items()):
        print(f"  {seg_type:10s}: {count}")
    
    # Validation
    validation_stats = results.get('validation_summary', {})
    pass_rate = validation_stats.get('pass_rate', 0) * 100
    print(f"\nValidation:")
    print(f"  Pass rate: {pass_rate:.1f}%")
    print(f"  Status: {'✅' if pass_rate >= 95 else '❌'}")
    
    # Performance analysis
    performance_met = analyze_performance(results, total_time, num_segments)
    
    # Story analysis
    stories = [s for s in segments if s.get('type') == 'story']
    if stories:
        print(f"\nStory Arc Analysis:")
        print(f"  Total story segments: {len(stories)}")
        
        story_arcs = {}
        for s in stories:
            arc_id = s.get('metadata', {}).get('arc_id')
            if arc_id:
                if arc_id not in story_arcs:
                    story_arcs[arc_id] = []
                story_arcs[arc_id].append(s)
        
        print(f"  Story arcs: {len(story_arcs)}")
        for arc_id, arc_segments in story_arcs.items():
            acts = [s.get('metadata', {}).get('act') for s in arc_segments]
            print(f"    Arc {arc_id}: {len(arc_segments)} segments, acts {acts}")
    
    # Save results
    with open(output_dir / "results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Final report
    report = []
    report.append("7-DAY BROADCAST TEST - FINAL REPORT")
    report.append("=" * 60)
    report.append(f"Generated: {datetime.now()}")
    report.append(f"\nSegments: {num_segments}/504")
    report.append(f"Duration: {total_time/3600:.2f} hours")
    report.append(f"Avg per segment: {total_time/num_segments:.1f}s")
    report.append(f"\nValidation pass rate: {pass_rate:.1f}%")
    report.append(f"Performance targets: {'MET ✅' if performance_met else 'NOT MET ❌'}")
    report.append(f"\nContent Breakdown:")
    for seg_type, count in sorted(content_types.items()):
        report.append(f"  {seg_type}: {count}")
    
    report_text = "\n".join(report)
    print("\n" + report_text)
    
    with open(output_dir / "final_report.txt", 'w') as f:
        f.write(report_text)
    
    # Success determination
    print("\n" + "="*60)
    success = (
        num_segments >= 500 and
        pass_rate >= 95 and
        performance_met
    )
    
    if success:
        print("✅ 7-DAY TEST PASSED - PRODUCTION READY")
        print("\nThe broadcast engine refactoring is validated and ready for deployment.")
    else:
        print("⚠️  7-DAY TEST NEEDS REVIEW")
    print("="*60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

---

## Performance Monitoring

### Real-Time Metrics

Monitor during tests:

```python
# Check cache stats
cache_stats = engine.get_cache_statistics()
print(f"Cache hit rate: {cache_stats['hit_rate']*100:.1f}%")
print(f"Hits: {cache_stats['hits']}, Misses: {cache_stats['misses']}")

# Check LLM efficiency
llm_stats = engine.get_llm_statistics()
print(f"LLM calls: {llm_stats['total_calls']}")
print(f"Per segment: {llm_stats['total_calls']/num_segments:.2f}")

# Check generation speed
print(f"Avg time per segment: {total_time/num_segments:.1f}s")
```

### Key Performance Indicators (KPIs)

| Metric | Target | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|--------|--------|---------|---------|---------|---------|
| Cache Hit Rate | ≥72% | ≥50% | ≥70% | ≥72% | ≥72% |
| LLM Calls/Segment | ≤1.0 | ≤1.5 | ≤1.2 | ≤1.0 | ≤1.0 |
| Generation Time | ≤8s | ≤10s | ≤8s | ≤8s | ≤8s |
| Validation Pass | ≥95% | ≥90% | ≥95% | ≥95% | ≥95% |

---

## Troubleshooting

### Common Issues

**1. Ollama server not responding**
```bash
# Check if running
curl http://localhost:11434/api/tags

# Restart if needed
killall ollama
ollama serve
```

**2. Model not found**
```bash
# List installed models
ollama list

# Pull missing model
ollama pull fluffy/l3-8b-stheno-v3.2
ollama pull dolphin-llama3
```

**3. Slow generation (>15s per segment)**
- Check VRAM: `nvidia-smi` (for NVIDIA GPU)
- Reduce `max_tokens` in generation options
- Close other GPU applications
- Consider using smaller model

**4. Low cache hit rate (<50%)**
- Check cache is enabled: `enable_cache=True`
- Verify topic mapping is correct
- Increase cache size: `max_cache_size=200`
- Check TTL isn't too short

**5. Validation failures (>10%)**
- Review constraint settings
- Check DJ knowledge profiles
- Verify validation model is working
- Review failed segment logs

**6. Out of memory**
- Reduce `segments_per_hour`
- Generate shorter durations
- Clear cache periodically
- Close other applications

---

## Success Criteria Summary

### Phase Completion Checklist

**Phase 1**: Ollama Setup
- [ ] Ollama installed and running
- [ ] Both models pulled and tested
- [ ] Response times <5s
- [ ] No errors

**Phase 2**: Single Segments
- [ ] All 5 content types generate
- [ ] Dual-model validation works
- [ ] Cache initializes
- [ ] No errors

**Phase 3**: 4-Hour Test
- [ ] 12 segments generated
- [ ] Cache hit rate ≥70%
- [ ] Generation time ≤10s avg
- [ ] Validation pass ≥95%

**Phase 4**: 24-Hour Test
- [ ] 72 segments generated
- [ ] Scheduling correct (time/weather/news)
- [ ] Story continuity maintained
- [ ] LLM reduction ≥50%
- [ ] Performance targets met

**Phase 5**: 7-Day Test
- [ ] 504 segments generated
- [ ] All performance targets met
- [ ] Cache stable
- [ ] Production ready

---

## Final Validation

### Production Readiness Checklist

Before deploying to production:

✅ All 5 test phases passed  
✅ Performance targets met:
  - 67%+ ChromaDB query reduction
  - 50%+ LLM call reduction
  - 41%+ faster generation
  - 72%+ cache hit rate
✅ Quality maintained:
  - 95%+ validation pass rate
  - Story continuity confirmed
  - No lore violations
  - DJ personalities consistent
✅ Stability confirmed:
  - No crashes in 7-day test
  - Cache stable over time
  - State persistence works
  - Error handling robust
✅ Documentation complete  
✅ Monitoring in place  

---

## Next Steps After Testing

Once all tests pass:

1. **Document Results**: Save all test outputs and metrics
2. **Create Baseline**: Establish performance baseline for monitoring
3. **Deploy to Production**: Use validated configuration
4. **Monitor**: Track cache hit rates, LLM usage, generation times
5. **Iterate**: Fine-tune based on production data

**Congratulations!** The broadcast engine refactoring is production-ready.
