#!/usr/bin/env python3
"""Analyze broadcast results for story integration and validation metrics."""
import json
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python analyze_broadcast_results.py <broadcast_json_file>")
    sys.exit(1)

filepath = Path(sys.argv[1])
data = json.load(open(filepath, encoding='utf-8'))

# Count story segments
story_segs = sum(1 for s in data['segments'] if s.get('story_context'))

# Validation stats
val_results = [s.get('validation_result') for s in data['segments'] if s.get('validation_result')]
passed = sum(1 for v in val_results if v.get('passed'))
failed = sum(1 for v in val_results if not v.get('passed'))
quality = sum(1 for v in val_results if v.get('quality_issues'))

# Story beat tracking
story_beats_used = set()
for seg in data['segments']:
    if seg.get('story_context'):
        # Extract story IDs from context
        context = seg['story_context']
        if 'Story story_' in context:
            # Parse story identifiers
            for line in context.split('\n'):
                if line.strip().startswith('1.') or line.strip().startswith('2.'):
                    if 'Story story_' in line:
                        story_id = line.split('Story ')[1].split(' ')[0]
                        story_beats_used.add(story_id)

# Segment types
types = {}
for seg in data['segments']:
    seg_type = seg.get('segment_type', 'unknown')
    types[seg_type] = types.get(seg_type, 0) + 1

print("\n" + "="*60)
print("BROADCAST RESULTS ANALYSIS")
print("="*60)
print(f"\nTotal segments: {len(data['segments'])}")
print(f"Segments with story context: {story_segs} ({story_segs/len(data['segments'])*100:.1f}%)")
print(f"Unique stories referenced: {len(story_beats_used)}")

print(f"\n--- Validation Results ---")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Segments with quality issues: {quality} ({quality/len(val_results)*100:.1f}%)")

print(f"\n--- Segment Types ---")
for seg_type, count in sorted(types.items(), key=lambda x: -x[1]):
    print(f"  {seg_type:20s} {count:3d} ({count/len(data['segments'])*100:5.1f}%)")

print(f"\n--- Story Beats Detected ---")
for story_id in sorted(story_beats_used):
    print(f"  {story_id}")

print("\n" + "="*60)
