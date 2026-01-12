---
agent: Fallout 76 lore validator
---

# Fallout 76 Lore Database Validation

Validate all entities in the `lore/fallout76_canon/` database for canonical accuracy. Systematically review each folder and file to ensure all data is correct for Fallout 76 timeline and lore.

## Validation Structure

Work through the database in this order:

### 1. Events (`events/`)
- ✅ Verify event dates fall within FO76 timeline (2077-2103)
- ✅ Confirm events are FO76-specific, not from other games
- ✅ Check description accuracy
- ✅ Update confidence scores based on canonical verification

### 2. Factions (`entities/factions/`)
For each faction file:
- ✅ Verify faction exists in Fallout 76
- ✅ Confirm founded/defunct dates are accurate
- ✅ Check primary locations match FO76 geography
- ✅ Validate leaders/key members if listed
- ✅ Ensure no cross-game contamination (FO3/NV/FO4 factions)
- ✅ Classify knowledge accessibility for Julie (2102 timeline)

### 3. Locations (`entities/locations/`)
For each location file:
- ✅ Verify location exists in Appalachia
- ✅ Confirm correct region assignment (Forest, Toxic Valley, Savage Divide, Mire, Cranberry Bog, Ash Heap)
- ✅ Check temporal availability (exists in 2102-2103)
- ✅ Validate geographic relationships

### 4. Characters (`entities/characters/`)
For each character file:
- ✅ Verify character appears in Fallout 76
- ✅ Confirm role/affiliation accuracy
- ✅ Check if active during 2102-2103 or historical
- ✅ Ensure no confusion with characters from other games

### 5. Technology (`entities/technology/`)
For each technology file:
- ✅ Verify technology exists in FO76
- ✅ Check if it's FO76-specific or cross-game (note variants)
- ✅ Validate availability timeline

### 6. Creatures (`entities/creatures/`)
For each creature file:
- ✅ Verify creature appears in FO76
- ✅ Check for FO76-specific variants/lore
- ✅ Validate origins match Appalachia storyline

## Validation Actions

For **each file you review**:

1. **Read the entity JSON**
2. **Check current confidence score** in `verification.confidence`
3. **Verify accuracy** using your Fallout 76 canonical knowledge
4. **If errors found**: 
   - Document what's wrong
   - Provide correct information with sources
   - Update the entity file
   - Adjust confidence score appropriately
5. **If correct**:
   - Update `verification.lore_expert_validated = true`
   - Increase confidence to 0.85-0.95
   - Add validation notes citing sources

## Output Format

For each entity, report:

```
✅ [entity_name] - VERIFIED
   Confidence: 0.60 → 0.90
   Notes: [Brief verification note]

❌ [entity_name] - ERRORS FOUND
   Issue: [Description of error]
   Correction: [Accurate information]
   Confidence: 0.60 → 0.40 (flagged for manual review)
```

## Summary Report

After completing validation, provide:
- Total entities reviewed
- Entities verified and upgraded
- Entities with errors requiring correction
- Entities flagged for manual review
- Any systematic issues discovered

## Important Notes

- Use Sequential Thinking for complex temporal/cross-game analysis
- Use Brave Search ONLY when uncertain about specific facts
- Trust your canonical knowledge first
- Be thorough but efficient - work through systematically
- Update files as you validate them