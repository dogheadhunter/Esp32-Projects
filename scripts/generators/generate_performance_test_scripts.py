"""Generate 100+ test scripts for performance testing by duplicating category samples"""
import sys
from pathlib import Path
import shutil
from datetime import datetime
sys.path.insert(0, 'tools/script-generator')

from broadcast_engine import BroadcastEngine

print("🔧 Generating sample scripts (1 per category)...")

# Initialize engine with retry=0 for speed
engine = BroadcastEngine('Julie (2102, Appalachia)', enable_validation=False)
engine.start_broadcast()

# Generate one of each category
categories = ['weather', 'news', 'music', 'gossip', 'general', 'story']
templates = {}

for category in categories:
    print(f"  Generating {category}...")
    # Generate a single segment
    segments = engine.generate_broadcast_sequence(6, 1, 1)
    if segments:
        templates[category] = segments[0]['script']
    else:
        templates[category] = f"Sample {category} script content for performance testing."

engine.end_broadcast(save_state=False)

print(f"\n📋 Generated {len(templates)} template scripts")

# Create output directory
output_dir = Path('output/scripts/pending_review/Julie')
output_dir.mkdir(parents=True, exist_ok=True)

# Clear existing perf test scripts
for old_file in output_dir.glob('perf_test_*.txt'):
    old_file.unlink()

# Duplicate scripts to reach 100 total
target_count = 100
scripts_per_category = target_count // len(categories)
remainder = target_count % len(categories)

script_count = 0
timestamp = datetime.now().strftime('%Y-%m-%d')

print(f"\n💾 Creating {target_count} scripts (~{scripts_per_category} per category)...")

for i, (category, content) in enumerate(templates.items()):
    # Extra scripts for first categories to handle remainder
    count = scripts_per_category + (1 if i < remainder else 0)
    
    for j in range(count):
        filename = f'perf_test_{script_count:04d}_{timestamp}_{category}.txt'
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        script_count += 1
    
    print(f"  ✅ {category}: {count} scripts")

print(f"\n✅ Created {script_count} test scripts in {output_dir}")
print(f"🚀 Ready for performance testing!")
