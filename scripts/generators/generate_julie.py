"""Generate broadcast scripts for Julie"""
import sys
from pathlib import Path
sys.path.insert(0, 'tools/script-generator')

from broadcast_engine import BroadcastEngine

# Initialize engine
engine = BroadcastEngine('Julie (2102, Appalachia)', enable_validation=True)
engine.start_broadcast()

# Generate 8 hours, 2 segments per hour = 16 scripts
segments = engine.generate_broadcast_sequence(8, 8, 2)
engine.end_broadcast(save_state=False)

# Save to files
output_dir = Path('output/scripts/pending_review/Julie')
output_dir.mkdir(parents=True, exist_ok=True)

for i, seg in enumerate(segments):
    hour = seg['metadata']['hour']
    segment_type = seg['segment_type'].replace('_', '-').title()
    filename = f'2026-01-17_{hour:02d}{i:02d}00_Julie_{segment_type}.txt'
    filepath = output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(seg['script'])
    
    print(f'✅ {filename}')

print(f'\n✅ Generated {len(segments)} Julie scripts in {output_dir}')
