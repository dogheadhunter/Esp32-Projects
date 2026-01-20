import sys
sys.path.insert(0, 'tools/script-generator')

from broadcast_engine import BroadcastEngine
import json
from datetime import datetime

print('='*70)
print('GENERATING 7-DAY BROADCAST WITH STORY SYSTEM')
print('='*70)

# Initialize with story system enabled
engine = BroadcastEngine(
    'Julie (2102, Appalachia)', 
    enable_validation=False,
    enable_story_system=True
)

engine.start_broadcast()

print('\nGenerating 7 days x 8 hours x 2 segments = 112 total segments')
print('This will test story progression across a full week...\n')

# Generate 7 days of content
segments = engine.generate_broadcast_sequence(
    start_hour=8,
    duration_hours=56,  # 7 days * 8 hours
    segments_per_hour=2
)

stats = engine.end_broadcast(save_state=True)

print('\n' + '='*70)
print('GENERATION COMPLETE')
print('='*70)

# Analyze story content
total = len(segments)
story_segs = [s for s in segments if s.get('segment_type') == 'story']

print(f'\nTotal Segments: {total}')
print(f'Story Segments: {len(story_segs)}')
print(f'Story Percentage: {len(story_segs)/total*100:.1f}%')

# Save results
output = {
    'metadata': {
        'duration_hours': 56,
        'segments_per_hour': 2,
        'total_days': 7,
        'generation_timestamp': datetime.now().isoformat()
    },
    'segments': segments,
    'stats': stats
}

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'output/broadcast_7day_story_test_{timestamp}.json'

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2)

print(f'\nSaved to: {output_file}')
print('\nDone!')
