#!/usr/bin/env python3
"""
Verify Phase 6 enrichment was applied to ChromaDB
"""

import chromadb

# Connect to database
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('fallout_wiki')

# Get first few chunks (should be enriched)
results = collection.get(limit=10, offset=0, include=['metadatas'])

print('=== VERIFICATION: First 10 Chunks (should be enriched) ===\n')

phase6_fields = [
    'emotional_tone', 'complexity_tier', 'freshness_score', 'broadcast_count',
    'primary_subject_0', 'theme_0', 'controversy_level', 'last_broadcast_time'
]

enriched_count = 0

for i, metadata in enumerate(results['metadatas'][:10]):
    wiki_title = metadata.get('wiki_title', 'Unknown')[:60]
    print(f'{i+1}. {wiki_title}')
    
    # Check for Phase 6 fields
    found = {}
    missing = []
    
    for field in phase6_fields:
        if field in metadata:
            value = metadata[field]
            if value is not None and value != '':
                found[field] = value
        else:
            missing.append(field)
    
    if found:
        enriched_count += 1
        print(f'   ✅ Phase 6 enriched:')
        for k, v in list(found.items())[:4]:
            print(f'      - {k}: {v}')
    else:
        print(f'   ❌ NOT enriched - missing all Phase 6 fields')
    
    print()

# Summary
print('=' * 60)
print('=== SUMMARY ===')
sample = results['metadatas'][0]
total_fields = len(sample)
phase6_present = sum(1 for f in phase6_fields if f in sample)

print(f'Total metadata fields in sample: {total_fields}')
print(f'Phase 6 fields found: {phase6_present}/{len(phase6_fields)}')
print(f'Chunks enriched: {enriched_count}/10')
print()

if enriched_count >= 8:
    print('✅ ENRICHMENT SUCCESSFUL!')
    print('   All sampled chunks have Phase 6 metadata')
elif enriched_count > 0:
    print('⚠️  PARTIAL ENRICHMENT')
    print(f'   Only {enriched_count}/10 chunks enriched')
else:
    print('❌ ENRICHMENT FAILED')
    print('   No Phase 6 metadata found')

# Show all field names
print(f'\nAll fields in first chunk: {sorted(sample.keys())}')
