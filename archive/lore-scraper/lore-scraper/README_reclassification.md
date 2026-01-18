# Entity Reclassification Workflow

## Overview

This directory contains scripts for post-processing scraped Fallout 76 wiki entities. The workflow performs:

1. **Entity Analysis** - Pattern-based classification with confidence scoring
2. **Reclassification** - Non-destructive entity reorganization with metadata tracking
3. **Duplicate Detection** - Fuzzy matching to find duplicate entities
4. **Quest Preservation** - Copy quests to reference folder for RAG queries

## Prerequisites

```bash
# Install required Python packages
pip install fuzzywuzzy python-Levenshtein
```

## Workflow Steps

### Step 1: Analyze Entities

Scan all entities and generate classification report with confidence scores.

```bash
# Analyze all entities
python tools/lore-scraper/analyze_entities.py \
  --input lore/fallout76_canon/entities \
  --output lore/fallout76_canon/metadata/analysis_report.json \
  --verbose

# View summary (without saving report)
python tools/lore-scraper/analyze_entities.py \
  --input lore/fallout76_canon/entities \
  --verbose
```

**Output:**
- Analysis report JSON with confidence scores for each entity
- Statistics: current vs suggested types, confidence distribution
- Top reclassification candidates

**Review:**
- Check top 10 high-confidence reclassifications
- Validate that pattern matching is working correctly
- Adjust patterns in `analyze_entities.py` if needed

### Step 2: Reclassify Entities

Apply reclassifications based on confidence thresholds.

```bash
# DRY RUN - Preview changes without applying
python tools/lore-scraper/reclassify_entities.py \
  --report lore/fallout76_canon/metadata/analysis_report.json \
  --auto \
  --dry-run

# Apply auto-reclassifications (≥0.8 confidence)
python tools/lore-scraper/reclassify_entities.py \
  --report lore/fallout76_canon/metadata/analysis_report.json \
  --auto

# Apply all reclassifications (auto + manual review)
python tools/lore-scraper/reclassify_entities.py \
  --report lore/fallout76_canon/metadata/analysis_report.json \
  --all
```

**Output:**
- Entities copied to new type folders with metadata
- Reclassification manifest for rollback capability
- Original files preserved

**Rollback (if needed):**
```bash
python tools/lore-scraper/reclassify_entities.py \
  --rollback lore/fallout76_canon/metadata/reclassification_manifest_YYYYMMDD_HHMMSS.json
```

### Step 3: Detect Duplicates

Find duplicate entities using fuzzy name + description matching.

```bash
# Find duplicates
python tools/lore-scraper/detect_duplicates.py \
  --input lore/fallout76_canon/entities \
  --output lore/fallout76_canon/metadata/duplicates_report.json \
  --verbose

# Adjust thresholds if needed
python tools/lore-scraper/detect_duplicates.py \
  --input lore/fallout76_canon/entities \
  --name-threshold 0.90 \
  --desc-threshold 0.75
```

**Output:**
- Duplicate pairs report with similarity scores
- Auto-merge candidates (≥0.90 similarity)
- Manual review needed (0.75-0.90 similarity)

**Review:**
- Check top 10 duplicate pairs
- Manually merge entities as appropriate
- Update entity IDs to reference merged entity

### Step 4: Preserve Quests

Copy quest entities to reference folder for RAG queries.

```bash
# DRY RUN - Preview quest preservation
python tools/lore-scraper/preserve_quests.py \
  --input lore/fallout76_canon/entities \
  --dry-run

# Preserve quests
python tools/lore-scraper/preserve_quests.py \
  --input lore/fallout76_canon/entities \
  --verbose
```

**Output:**
- Quests copied to `entities/quests_reference/` with special flags
- Marked as `reference_only: true` for RAG filtering
- Original quest files remain in place for cross-referencing

## Confidence Thresholds

Based on industry best practices:

| Threshold | Action | Description |
|-----------|--------|-------------|
| ≥0.8 | Auto-reclassify | High confidence, safe for automation |
| 0.5-0.8 | Manual review | Medium confidence, needs human approval |
| <0.5 | Keep in unknown | Low confidence, ambiguous classification |

## Pattern Matching Rules

Entity types are detected using keyword patterns:

### Quest Detection (Priority: 0.95)
- **Title keywords**: quest, mission, event:, operation:, ally:, daily:
- **Description keywords**: quest, mission, rewards, given by, complete, etc.
- **Boost**: Links to character/location entities

### Document Detection (Priority: 0.90)
- **Title keywords**: holotape, note, journal, diary, letter, log
- **Description keywords**: holotape, note, terminal, found at, written by
- **Boost**: Links to location/character entities

### Location Detection (Priority: 0.85)
- **Title keywords**: camp, vault, settlement, station, building, site
- **Description keywords**: located, settlement, north of, south of, etc.
- **Boost**: Links to other location entities

### Character Detection (Priority: 0.80)
- **Title keywords**: trader, vendor, resident, npc
- **Description keywords**: npc, character, person, found at, lives in
- **Boost**: Links to faction/location entities

## File Structure

```
lore/fallout76_canon/
├── entities/
│   ├── characters/          # Character entities
│   ├── documents/           # Holotapes, notes, journals
│   ├── factions/            # Organizations
│   ├── locations/           # Places and structures
│   ├── creatures/           # Enemies and animals
│   ├── quest/               # Quests (after reclassification)
│   ├── unknown/             # Unclassified entities
│   └── quests_reference/    # Quest reference data (RAG only)
├── metadata/
│   ├── analysis_report.json          # Entity analysis results
│   ├── reclassification_manifest_*.json  # Rollback manifests
│   └── duplicates_report.json        # Duplicate detection results
└── ...
```

## Validation Checklist

After running the workflow:

- [ ] Check analysis report statistics match expectations
- [ ] Review top 10 high-confidence reclassifications for accuracy
- [ ] Validate precision ≥90% on sample of auto-reclassifications
- [ ] Review duplicate pairs before merging
- [ ] Confirm quests marked as `reference_only: true`
- [ ] Test RAG queries on quest data
- [ ] Verify rollback capability works

## Troubleshooting

**Issue:** Too many false positives (wrong classifications)
- **Solution:** Raise confidence threshold to 0.85 or 0.90
- **Solution:** Adjust pattern weights in `analyze_entities.py`

**Issue:** Too many manual reviews (>50%)
- **Solution:** Lower confidence threshold to 0.75
- **Solution:** Add more keywords to patterns

**Issue:** Duplicates not detected
- **Solution:** Lower similarity thresholds (0.80 name, 0.65 desc)
- **Solution:** Check entity descriptions are properly extracted

**Issue:** Need to rollback reclassification
- **Solution:** Use `--rollback` with manifest file
- **Solution:** Original files are preserved, can manually restore

## Performance Notes

- **Analysis**: ~1-5 minutes for 3000 entities
- **Reclassification**: ~1-3 minutes for 1000 entities
- **Duplicate Detection**: ~2-10 minutes for 3000 entities (depends on comparisons)
- **Quest Preservation**: <1 minute

## Next Steps

1. Run analyzer on existing entities
2. Review top 100 suggestions
3. Adjust patterns if needed
4. Apply auto-reclassifications (≥0.8)
5. Manually review medium confidence (0.5-0.8)
6. Detect and merge duplicates
7. Preserve quests to reference folder
8. Index into ChromaDB for RAG queries
