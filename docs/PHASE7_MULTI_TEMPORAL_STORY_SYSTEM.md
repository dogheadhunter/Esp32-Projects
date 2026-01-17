# Phase 7: Multi-Temporal Story System
## Implementation Plan

**Created**: January 17, 2026  
**Status**: Planning  
**Estimated Duration**: 6 weeks

---

## 1. Overview

The Multi-Temporal Story System adds four concurrent story timelines to the broadcast engine, enabling long-form narrative arcs that develop naturally across broadcasts.

### Timeline Scales

| Timeline | Duration | Broadcasts | Example |
|----------|----------|------------|---------|
| **Daily** | 1 day | 2-6 | Missing scavenger, local encounter |
| **Weekly** | 7 days | 14-42 | Investigation, faction skirmish |
| **Monthly** | 30 days | 60-180 | Major battle, settlement crisis |
| **Yearly** | 365 days | 700-2000 | War, world-changing events |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MULTI-TEMPORAL STORY SYSTEM                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │  STORY EXTRACTOR │───▶│  STORY SCHEDULER │───▶│  STORY WEAVER  │         │
│  │  (ChromaDB→Acts) │    │  (Multi-Timeline)│    │  (→Broadcast)  │         │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘         │
│           │                      │                       │                   │
│           ▼                      ▼                       ▼                   │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                        STORY STATE MANAGER                          │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │    │
│  │  │  DAILY   │ │  WEEKLY  │ │ MONTHLY  │ │  YEARLY  │              │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│           ┌────────────────────────┼────────────────────────┐              │
│           ▼                        ▼                        ▼              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │  LORE VALIDATOR │    │ DJ KNOWLEDGE    │    │ TIMELINE        │        │
│  │  (Canon Check)  │    │ FILTER          │    │ VALIDATOR       │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **StoryExtractor** queries ChromaDB for quest/event/arc content
2. **LoreValidator** checks canon consistency (factions, timeline, events)
3. **TimelineValidator** filters for DJ knowledge boundaries
4. **StoryScheduler** assigns to timeline slots and schedules acts
5. **StoryWeaver** combines stories into broadcast segments
6. **BroadcastEngine** receives story context for script generation

---

## 3. New Modules

### Directory Structure

```
tools/script-generator/
├── story_system/
│   ├── __init__.py
│   ├── story_models.py          # Pydantic models
│   ├── story_extractor.py       # ChromaDB → Story extraction
│   ├── lore_validator.py        # Canon validation
│   ├── timeline_validator.py    # DJ temporal validation
│   ├── story_scheduler.py       # Multi-timeline scheduling
│   ├── story_weaver.py          # Broadcast integration
│   ├── story_state.py           # Persistence
│   ├── escalation_engine.py     # Story promotion
│   └── tests/
```

### Module Descriptions

| Module | Purpose |
|--------|---------|
| **story_models.py** | Pydantic models: Story, StoryAct, ActiveStory, StoryTimeline enum, StoryStatus enum |
| **story_extractor.py** | Find narratives in ChromaDB, identify story-worthy content, break into acts |
| **lore_validator.py** | Validate faction relationships, timeline consistency, canon events |
| **timeline_validator.py** | Check DJ temporal/spatial boundaries, knowledge tier access |
| **story_scheduler.py** | Manage 4 concurrent timeline slots, probability-based scheduling |
| **story_weaver.py** | Combine multiple stories into broadcast, add transitions, manage callbacks |
| **story_state.py** | JSON persistence for story pools, scheduler state, completion history |
| **escalation_engine.py** | Promote stories between timelines (daily→weekly→monthly→yearly) |

---

## 4. Key Concepts

### 4.1 Story Structure

- **Story**: Complete narrative with title, timeline, acts, sources, DJ compatibility
- **StoryAct**: Individual segment with type (setup/rising/climax/falling/resolution), summary, source chunks
- **ActiveStory**: In-progress story tracking current act, broadcast count, engagement

### 4.2 Lore Validation

Checks performed:
- Faction conflicts (NCR vs Legion cannot cooperate)
- Faction existence in time period
- Canon event accuracy
- Location validity

### 4.3 DJ Knowledge Filtering

Validates stories against DJ profile:
- **Temporal**: DJ can't know future events
- **Spatial**: Regional knowledge boundaries
- **Tier**: Common/regional/restricted/classified access
- **Framing**: Suggests how DJ should present (direct/report/rumor)

### 4.4 Story Scheduling

- 4 concurrent slots (one per timeline)
- Probability-based beat inclusion per broadcast
- Minimum spacing between same-timeline beats
- Cooldown after story completion before new story starts

### 4.5 Story Weaving

- Orders stories for narrative flow (daily first, then weekly, monthly, yearly)
- Adds intro/outro transitions
- Creates callbacks between related stories
- Generates context string for LLM prompt injection

### 4.6 Story Escalation

Promotes successful stories:
- Daily → Weekly → Monthly → Yearly
- Triggers based on engagement score and broadcast count
- Generates expanded act structure for higher timeline
- Tracks escalation history

---

## 5. Implementation Schedule

### Week 1: Foundation
- Create `story_system/` directory structure
- Implement `story_models.py` (Pydantic models)
- Write unit tests for models
- Implement `lore_validator.py`

### Week 2: Extraction & Validation
- Implement `story_extractor.py`
- Implement `timeline_validator.py`
- Integration tests with real ChromaDB data

### Week 3: Scheduling
- Implement `story_scheduler.py`
- Implement `story_state.py`
- Scheduler unit tests

### Week 4: Weaving & Integration
- Implement `story_weaver.py`
- Implement `escalation_engine.py`
- Modify `broadcast_engine.py` for story integration

### Week 5: Testing & Polish
- Integration testing with BroadcastEngine
- Modify `session_memory.py` for story context
- Modify `world_state.py` for story state linking
- End-to-end test suite

### Week 6: Documentation & Cleanup
- Update ARCHITECTURE.md
- Write STORY_SYSTEM.md
- Create example scripts
- Code review

---

## 6. Files to Modify

| File | Changes |
|------|---------|
| `broadcast_engine.py` | Add story system integration, call scheduler/weaver/escalation |
| `world_state.py` | Add story_state_path linking |
| `session_memory.py` | Add recent_story_beats tracking for continuity |

---

## 7. Persistence Schema

Stored in `story_state.json`:
- Story pools (queued stories per timeline)
- Scheduler state (active stories, cooldowns, broadcast counts)
- Completed stories archive
- Escalation history

---

## 8. Research Items

### High Priority
| Item | Question |
|------|----------|
| Quest detection | How to reliably identify quest content in ChromaDB metadata? |
| Narrative arc detection | Can we detect setup→climax→resolution patterns in wiki text? |
| Story coherence | How to ensure extracted acts form coherent narrative? |

### Medium Priority
| Item | Question |
|------|----------|
| Engagement simulation | How to simulate listener engagement without real feedback? |
| Escalation triggers | What criteria make a story worth escalating? |
| Cross-timeline callbacks | When should daily stories reference monthly arcs? |

### Low Priority (Future)
| Item | Question |
|------|----------|
| LLM-assisted extraction | Could Ollama help generate story structures from lore? |
| Dynamic act generation | Generate new acts mid-story from ChromaDB? |
| Real engagement tracking | Track listener feedback via ESP32 for escalation? |

---

## 9. Edge Cases & Failure Modes

### Story Extraction
- **No suitable content**: Use fallback gossip content
- **Single chunk per story**: Skip; require minimum 2 chunks
- **Conflicting metadata**: Use majority vote; flag for review

### Scheduling
- **All pools empty**: Extract on-demand or skip story content
- **Story deadline passed**: Force resolution; mark abandoned if 2x over
- **DJ switch mid-story**: Validate new DJ; pause incompatible stories

### Persistence
- **JSON corruption**: Keep backup; restore from reference
- **Missing file**: Initialize fresh state; log warning
- **Version migration**: Include schema version; implement migrations

---

## 10. Configuration Options

Key configurable values:
- Story inclusion rate (% of broadcasts with stories)
- Maximum stories per broadcast
- Pool sizes per timeline
- Escalation thresholds
- Minimum engagement for escalation
- Auto-save interval

---

## 11. Future Enhancements (Phase 8+)

1. **LLM-Assisted Story Generation**: Ollama generates original content from lore snippets
2. **Dynamic Act Generation**: Create new acts mid-story based on context
3. **Listener Feedback Integration**: ESP32 button for "more like this"
4. **Faction Reputation System**: Stories affect faction relations in WorldState
5. **Seasonal Events**: Calendar-based yearly story triggers
6. **Story Branching**: Multiple resolution paths based on simulated choices
7. **Cross-DJ Story Continuity**: Same story told from different DJ perspectives

---

## 12. Success Criteria

- [ ] All 4 timeline slots operating concurrently
- [ ] Stories extracted from ChromaDB with coherent act structure
- [ ] Lore validation prevents canon-breaking stories
- [ ] DJ knowledge filtering respects temporal/spatial boundaries
- [ ] Stories persist across sessions
- [ ] Escalation promotes successful stories appropriately
- [ ] Integration with BroadcastEngine is seamless
- [ ] 90%+ test coverage on story_system modules
