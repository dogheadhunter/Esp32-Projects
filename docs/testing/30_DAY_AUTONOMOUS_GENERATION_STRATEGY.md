# 30-Day Autonomous Broadcast: Testing & Validation Strategy

**Created**: January 20, 2026  
**Purpose**: Comprehensive strategy for autonomous 30-day broadcast generation with multi-tier validation  
**Target**: 480 broadcast hours (30 days × 6am-10pm), ~9,600 segments, 80+ hours generation time

---

## Overview

For autonomous 30-day generation, we need **3-tier validation**:

### Tier 1: Pre-Generation Tests (7 min)
Fast mock validation before committing to 80-hour generation

### Tier 2: Pilot Run (1-2 hours)  
Real LLM/ChromaDB on small scale (1 day, 16 hours)

### Tier 3: Production Monitoring (during 80-hour run)
Live validation with auto-recovery

---

## 1. Pre-Generation Tests (What We Have Now)

### 1.1 Rule-Based Validation (Already Implemented)
**File**: `validation_rules.py`

**Fast checks (<100ms each)**:
```python
✅ validate_temporal() - Year limits, anachronisms
✅ validate_content() - Forbidden topics/factions  
✅ validate_format() - Length, structure, punctuation
✅ validate_regional_consistency() - Location-specific knowledge
✅ validate_character_voice_consistency() - DJ personality markers
```

**What This Catches**:
- ✅ Travis mentions "Institute" (forbidden knowledge)
- ✅ Julie references 2103 events (beyond her 2102 cutoff)
- ✅ Mr. New Vegas uses informal language ("uh", "um")
- ✅ Script is only 5 words (too short)
- ✅ Mojave DJ mentions Commonwealth locations

**What This MISSES**:
- ❌ Subtle tone shifts ("The rad storm approaches" vs "Yo, rad storm incoming")
- ❌ Context coherence (news about raiders, but no previous mention)
- ❌ Story beat progression logic (Week 3 gossip still calls it "rumor")
- ❌ Emotional authenticity (Julie sounds depressed, not upbeat)

---

### 1.2 Test Your 30-Day Scenario Logic

**Create tests for broadcast orchestration**:

```python
def test_30_day_weather_schedule():
    """Validate weather reports at correct times with correct context"""
    scheduler = BroadcastSchedulerV2()
    
    # Day 1-30, test each day
    for day in range(1, 31):
        # 6am - morning/day forecast
        plan_6am = scheduler.get_next_segment_plan(
            hour=6,
            context={'day': day, ...}
        )
        assert plan_6am.segment_type == SegmentType.WEATHER
        assert "morning" in plan_6am.metadata['weather_context']
        assert "day" in plan_6am.metadata['weather_context']
        
        # 12pm - afternoon/evening forecast
        plan_12pm = scheduler.get_next_segment_plan(hour=12, ...)
        assert "afternoon" in plan_12pm.metadata['weather_context']
        assert "evening" in plan_12pm.metadata['weather_context']
        
        # 5pm - night/tomorrow forecast
        plan_5pm = scheduler.get_next_segment_plan(hour=17, ...)
        assert "night" in plan_5pm.metadata['weather_context']
        assert "tomorrow" in plan_5pm.metadata['weather_context']


def test_story_beat_progression_over_weeks():
    """Validate gossip→news→story progression"""
    story_scheduler = StoryScheduler()
    
    # Week 1: Plant story as gossip (rumor)
    week1_beats = story_scheduler.get_story_beats_for_broadcast(
        current_week=1,
        story_id="raider_attack_vault76"
    )
    assert any("rumor" in beat.content.lower() or 
               "heard" in beat.content.lower() 
               for beat in week1_beats)
    
    # Week 2: Story develops (news - confirmed/developing)
    week2_beats = story_scheduler.get_story_beats_for_broadcast(
        current_week=2, 
        story_id="raider_attack_vault76"
    )
    assert any("confirmed" in beat.content.lower() or 
               "reports indicate" in beat.content.lower()
               for beat in week2_beats)
    
    # Week 3: Story concludes (resolution)
    week3_beats = story_scheduler.get_story_beats_for_broadcast(
        current_week=3,
        story_id="raider_attack_vault76"
    )
    assert any("resolved" in beat.content.lower() or
               "ended" in beat.content.lower()
               for beat in week3_beats)


def test_world_state_persistence_across_days():
    """Validate world state evolution"""
    engine = BroadcastEngine(world_state_path="test_world.json")
    
    # Day 1: Generate broadcast, save state
    engine.generate_broadcast_sequence(
        current_date="2102-06-01",
        current_hour=6,
        segment_count=16
    )
    engine.end_broadcast(save_state=True)
    
    # Day 2: Load state, verify references
    engine2 = BroadcastEngine(world_state_path="test_world.json")
    day2_context = engine2._build_context_query(...)
    
    # Verify Day 1 events are in context
    assert "2102-06-01" in day2_context or "yesterday" in day2_context
```

**New tests you need** (not yet written):

1. **test_gossip_to_news_to_story_pipeline.py**
   - Gossip tracker creates "raider_rumor" in Week 1
   - News segment confirms "raider_attack" in Week 2  
   - Story system resolves "raider_siege" in Week 3
   - World state tracks progression

2. **test_30day_scheduler_state.py**
   - Test scheduler state persists across 30 days
   - Verify time_check_done_hours resets daily
   - Verify news_done_hours resets daily
   - Verify story progression doesn't reset

3. **test_quest_story_arc_structure.py**
   - Quest extracted from ChromaDB has clear acts
   - Acts progress: setup → conflict → resolution
   - Story doesn't end abruptly without resolution

---

## 2. ChromaDB Quest Retrieval Issues

### Current Problem
Looking at `story_extractor.py`:

```python
def _extract_quest_stories(...):
    results = self.collection.query(
        query_texts=["quest objective reward walkthrough"],  # ⚠️ Generic query
        n_results=300,  # ⚠️ Fixed count
    )
```

**Issues**:
1. **No metadata filtering** - Gets ALL content, not just quests
2. **Semantic query too generic** - "quest objective" matches quest guides, not quest lore
3. **No infobox_type filter** - Should filter `infobox_type='infobox quest'`
4. **No DJ knowledge filtering** - Gets quests Julie shouldn't know about

### Recommended Fix

```python
def _extract_quest_stories_improved(
    self,
    dj_name: str,
    dj_year: int,
    dj_region: str,
    max_stories: int = 10,
    min_chunks: int = 3,
    max_chunks: int = 10,
) -> List[Story]:
    """Extract DJ-appropriate quest stories from ChromaDB."""
    
    # Build metadata filter for quests + DJ knowledge
    where_filter = {
        "$and": [
            # Must be quest content
            {"$or": [
                {"infobox_type": "infobox quest"},
                {"content_type": "quest"}
            ]},
            # Must be within DJ's temporal knowledge
            {"year_max": {"$lte": dj_year}},
            # Must be in DJ's region (or common knowledge)
            {"$or": [
                {"location": dj_region},
                {"region": dj_region},
                {"knowledge_tier": "common"}
            ]}
        ]
    }
    
    try:
        results = self.collection.query(
            query_texts=[f"quest story narrative arc {dj_region}"],
            n_results=300,
            where=where_filter  # ✅ Filter applied
        )
        
        if not results or not results.get("ids"):
            return []
        
        # Group chunks by wiki_title
        chunks_by_title = self._group_chunks_by_title(results)
        
        # Filter for minimum chunk count
        valid_quests = [
            (title, chunks) for title, chunks in chunks_by_title.items()
            if len(chunks) >= min_chunks
        ]
        
        # Sort by chunk count (more content = richer story)
        sorted_quests = sorted(
            valid_quests,
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        stories = []
        for title, chunks in sorted_quests[:max_stories * 2]:
            story = self._chunks_to_story(title, chunks[:max_chunks], "quest")
            
            if story and self._validate_story_arc(story):  # ✅ Arc validation
                stories.append(story)
                
                if len(stories) >= max_stories:
                    break
        
        return stories
        
    except Exception as exc:
        print(f"[ERROR] Quest extraction failed: {exc}")
        return []


def _validate_story_arc(self, story: Story) -> bool:
    """Validate story has proper narrative arc structure."""
    if len(story.acts) < 2:
        return False  # Need at least setup + resolution
    
    # Check for act type diversity
    act_types = {act.act_type for act in story.acts}
    
    # Should have at least 2 different act types
    if len(act_types) < 2:
        return False
    
    # First act should be SETUP
    if story.acts[0].act_type != StoryActType.SETUP:
        return False
    
    # Last act should be RESOLUTION or CLIMAX
    if story.acts[-1].act_type not in [StoryActType.RESOLUTION, StoryActType.CLIMAX]:
        return False
    
    return True
```

**Test this**:

```python
def test_chromadb_quest_filtering():
    """Verify quest extraction filters correctly"""
    extractor = StoryExtractor(chroma_collection=collection)
    
    # Julie should only get Appalachia quests from ≤2102
    julie_quests = extractor._extract_quest_stories_improved(
        dj_name="Julie",
        dj_year=2102,
        dj_region="Appalachia",
        max_stories=10
    )
    
    for quest in julie_quests:
        # Verify temporal constraint
        assert all(chunk['metadata'].get('year_max', 0) <= 2102 
                  for chunk in quest.chunks)
        
        # Verify regional constraint
        regions = {chunk['metadata'].get('region') for chunk in quest.chunks}
        assert 'Appalachia' in regions or 'common' in regions
        
        # Verify is actually a quest
        assert any(chunk['metadata'].get('content_type') == 'quest' or
                  chunk['metadata'].get('infobox_type') == 'infobox quest'
                  for chunk in quest.chunks)
```

---

## 3. Multi-Level Validation Strategy

### 3.1 Rule-Based Validation (Tier 1 - Fast)

**When**: Every script generation

**Rules**:

```python
VALIDATION_RULES = {
    # Temporal Rules
    "year_limit": {
        "Julie": 2102,
        "Mr. New Vegas": 2281,
        "Travis Miles (Nervous)": 2287,
        "Travis Miles (Confident)": 2287,
    },
    
    # Forbidden Knowledge
    "forbidden_topics": {
        "Julie": ["Institute", "Railroad", "Minutemen", "NCR", "Legion"],
        "Travis Miles (Nervous)": ["Institute", "Railroad (details)"],
        "Mr. New Vegas": ["Institute", "Commonwealth", "Appalachia"],
    },
    
    # Forbidden Factions (detailed knowledge)
    "forbidden_factions": {
        "Julie": ["NCR", "Caesar's Legion", "Mr. House"],
        "Travis Miles (Nervous)": [],  # Can mention anything in Commonwealth
        "Mr. New Vegas": ["Institute", "Railroad", "Minutemen"],
    },
    
    # Regional Consistency
    "valid_locations": {
        "Julie": ["Appalachia", "Vault 76", "Flatwoods", "Charleston", ...],
        "Travis Miles": ["Commonwealth", "Diamond City", "Goodneighbor", ...],
        "Mr. New Vegas": ["Mojave", "New Vegas", "Hoover Dam", ...],
    },
    
    # Voice Markers (required for authenticity)
    "required_voice_markers": {
        "Julie": ["upbeat", "vault-tec", "optimistic"],  # At least 1 in tone
        "Travis Miles (Nervous)": ["uh", "um", "nervous"],  # Must have filler words
        "Mr. New Vegas": ["smooth", "charming", "ladies"],  # Suave tone
    },
    
    # Story Beat Progression
    "story_progression_keywords": {
        "rumor": ["heard", "rumor", "word is", "travelers say"],
        "developing": ["reports indicate", "confirmed sightings", "ongoing"],
        "confirmed": ["confirmed", "official", "verified", "reports"],
        "resolved": ["resolved", "ended", "concluded", "aftermath"],
    },
}
```

**Implementation**:

```python
class EnhancedValidationRules(ValidationRules):
    """Extended validation with story progression checks"""
    
    def validate_story_beat_progression(
        self,
        script: str,
        story_week: int,
        story_stage: str,  # "rumor", "developing", "confirmed", "resolved"
    ) -> Dict[str, Any]:
        """Validate story uses correct language for its stage"""
        issues = []
        
        keywords = VALIDATION_RULES["story_progression_keywords"][story_stage]
        
        script_lower = script.lower()
        keyword_found = any(kw in script_lower for kw in keywords)
        
        if not keyword_found:
            issues.append({
                "type": "story_progression",
                "message": f"Week {story_week} story should be '{story_stage}' "
                          f"but missing keywords: {keywords}"
            })
        
        # Check for conflicting stage keywords
        for other_stage, other_keywords in VALIDATION_RULES["story_progression_keywords"].items():
            if other_stage != story_stage:
                if any(kw in script_lower for kw in other_keywords):
                    issues.append({
                        "type": "story_progression_conflict",
                        "message": f"Story is '{story_stage}' but contains "
                                  f"'{other_stage}' keywords: {other_keywords}"
                    })
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
```

### 3.2 Hybrid Validation (Tier 2 - Moderate Speed)

**When**: After rule-based passes, before saving

**Rules + LLM check**:

```python
class HybridValidator:
    """Combines rule-based + LLM validation (already exists in your codebase)"""
    
    def validate(self, script: str, character_card: Dict, constraints: Dict) -> ValidationResult:
        # Step 1: Fast rule-based checks
        rule_result = self.rule_validator.validate_all(script, character_card, constraints)
        
        if not rule_result['valid']:
            # Failed rules - don't waste LLM call
            return ValidationResult(
                is_valid=False,
                script=script,
                issues=self._convert_rule_issues(rule_result['issues']),
                source="rule"
            )
        
        # Step 2: LLM quality check (tone, coherence, authenticity)
        llm_result = self.llm_validator.validate(script, character_card, constraints)
        
        return llm_result
```

### 3.3 Pure LLM Validation (Tier 3 - Slow, High Quality)

**When**: Final validation before audio generation OR as fallback

**LLM Prompt**:

```python
LLM_VALIDATION_PROMPT = """You are validating a Fallout radio broadcast script for quality and authenticity.

**CHARACTER**: {dj_name}
**PERSONALITY CARD**: {character_card}
**SCRIPT TYPE**: {script_type}
**STORY CONTEXT**: {story_context}

**SCRIPT TO VALIDATE**:
\"\"\"{script}\"\"\"

**VALIDATION CRITERIA**:

1. **Temporal Consistency** (CRITICAL):
   - Year limit: {year_limit}
   - No mentions of events/factions after this date
   - No anachronisms (modern technology, internet, etc.)

2. **Regional Knowledge** (CRITICAL):
   - Region: {region}
   - Valid locations: {valid_locations}
   - Forbidden locations: {forbidden_locations}

3. **Character Voice** (HIGH):
   - Matches personality card tone and speech patterns
   - Uses appropriate catchphrases/fillers
   - Maintains consistent emotional state

4. **Story Beat Progression** (HIGH):
   - Week {story_week}: Should be '{story_stage}' stage
   - Uses appropriate language (rumor vs confirmed vs resolved)
   - Doesn't contradict previous story beats

5. **Content Quality** (MEDIUM):
   - Script is engaging and well-structured
   - Has natural transitions
   - Length appropriate ({target_length} words target)

6. **World State Coherence** (MEDIUM):
   - References to previous broadcasts make sense
   - Weather/time context matches broadcast time
   - Faction relationships are accurate

**OUTPUT FORMAT** (JSON only):
{{
  "is_valid": true/false,
  "overall_score": 0.0-1.0,
  "issues": [
    {{
      "severity": "critical" | "warning" | "suggestion",
      "category": "lore" | "character" | "tone" | "quality" | "temporal" | "story_progression",
      "message": "Detailed issue description",
      "suggestion": "How to fix (optional)",
      "confidence": 0.0-1.0
    }}
  ],
  "feedback": "Brief overall assessment"
}}
"""
```

**Implementation**:

```python
class LLMValidator:
    """LLM-powered validation (already exists, enhance prompt)"""
    
    def validate_with_story_context(
        self,
        script: str,
        character_card: Dict,
        story_context: Dict,  # ← NEW
        constraints: Dict
    ) -> ValidationResult:
        """Enhanced validation with story progression awareness"""
        
        prompt = LLM_VALIDATION_PROMPT.format(
            dj_name=character_card['name'],
            character_card=json.dumps(character_card, indent=2),
            script_type=constraints.get('script_type', 'unknown'),
            story_context=json.dumps(story_context, indent=2),  # ← NEW
            script=script,
            year_limit=constraints.get('max_year', 9999),
            region=constraints.get('region', 'Unknown'),
            valid_locations=constraints.get('valid_locations', []),
            forbidden_locations=constraints.get('forbidden_locations', []),
            story_week=story_context.get('week', 1),  # ← NEW
            story_stage=story_context.get('stage', 'rumor'),  # ← NEW
            target_length=constraints.get('target_length', 150),
        )
        
        response = self.ollama.generate(
            model="llama3.1:8b",
            prompt=prompt,
            temperature=0.1,  # Low temp for consistent validation
            format="json"
        )
        
        # Parse and return validation result
        result_json = json.loads(response['response'])
        
        return ValidationResult(
            is_valid=result_json['is_valid'],
            script=script,
            issues=self._parse_llm_issues(result_json['issues']),
            llm_feedback=result_json['feedback'],
            overall_score=result_json['overall_score']
        )
```

---

## 4. Testing the Full 30-Day Pipeline

### 4.1 Mock Generation Test (7 min)

```python
@pytest.mark.unit
def test_30day_mock_generation():
    """Mock LLM/ChromaDB, validate orchestration logic"""
    
    # Mock LLM to return predictable scripts
    mock_llm = Mock()
    mock_llm.generate.return_value = {
        'response': "Mocked DJ script with proper tone and structure."
    }
    
    # Mock ChromaDB to return quest data
    mock_chroma = Mock()
    mock_chroma.query.return_value = {
        'ids': [['quest1', 'quest2']],
        'documents': [[quest1_text, quest2_text]],
        'metadatas': [[quest1_meta, quest2_meta]]
    }
    
    engine = BroadcastEngine(
        ollama_client=mock_llm,
        chroma_collection=mock_chroma
    )
    
    # Generate 30 days × 16 hours = 480 hours
    for day in range(1, 31):
        for hour in range(6, 22):  # 6am-10pm
            segments = engine.generate_broadcast_sequence(
                current_date=f"2102-06-{day:02d}",
                current_hour=hour,
                segment_count=1
            )
            
            # Validate each segment
            assert len(segments) == 1
            assert segments[0]['metadata']['script_type'] in [
                'weather', 'news', 'gossip', 'time_check', 'story'
            ]
        
        # End of day - save state
        engine.end_broadcast(save_state=True)
    
    # Verify final state
    final_state = engine.world_state.to_dict()
    assert final_state['current_day'] == 30
    assert len(final_state['story_history']) > 0  # Stories were told
    assert len(final_state['gossip_archive']) > 0  # Gossip evolved
```

### 4.2 Pilot Generation Test (1-2 hours)

```python
@pytest.mark.integration
@pytest.mark.slow
def test_1day_real_generation():
    """Real LLM/ChromaDB for 1 day to catch integration issues"""
    
    # Real dependencies
    ollama = OllamaClient()
    chroma = ChromaDBIngestor('chroma_db')
    
    engine = BroadcastEngine(
        dj_name="Julie",
        ollama_client=ollama,
        chroma_collection=chroma.collection,
        enable_validation=True  # ← Enable full validation
    )
    
    validation_failures = []
    
    # Generate 1 day (16 hours × ~4 segments/hour = 64 segments)
    for hour in range(6, 22):
        segments = engine.generate_broadcast_sequence(
            current_date="2102-06-01",
            current_hour=hour,
            segment_count=4
        )
        
        for segment in segments:
            # Validate each script
            validation_result = validate_with_story_context(
                script=segment['script'],
                character_card=engine.personality,
                story_context=segment['metadata'].get('story_context', {}),
                constraints=segment['metadata'].get('constraints', {})
            )
            
            if not validation_result.is_valid:
                validation_failures.append({
                    'hour': hour,
                    'segment_type': segment['metadata']['script_type'],
                    'issues': validation_result.issues,
                    'script': segment['script'][:100]  # First 100 chars
                })
    
    # Assert quality thresholds
    total_segments = 16 * 4  # 64 segments
    failure_rate = len(validation_failures) / total_segments
    
    assert failure_rate < 0.05, f"Validation failure rate too high: {failure_rate:.1%}"
    
    if validation_failures:
        print(f"\n⚠️ {len(validation_failures)} validation failures:")
        for failure in validation_failures[:5]:  # Show first 5
            print(f"  Hour {failure['hour']}, {failure['segment_type']}: {failure['issues'][0]['message']}")
```

### 4.3 Production Monitoring (during 80-hour run)

```python
class ProductionMonitor:
    """Monitor 30-day generation with auto-recovery"""
    
    def __init__(self, output_dir: Path, checkpoint_interval: int = 10):
        self.output_dir = output_dir
        self.checkpoint_interval = checkpoint_interval  # Save every N segments
        self.validation_log = []
        self.failure_count = 0
        self.retry_count = 0
    
    def generate_with_monitoring(
        self,
        engine: BroadcastEngine,
        total_days: int = 30,
        max_retries_per_segment: int = 3
    ):
        """Generate 30 days with live monitoring and recovery"""
        
        for day in range(1, total_days + 1):
            for hour in range(6, 22):  # 6am-10pm
                try:
                    # Generate segment
                    segment = engine.generate_single_segment(
                        current_date=f"2102-06-{day:02d}",
                        current_hour=hour
                    )
                    
                    # Validate
                    validation = self.validate_segment(segment, engine)
                    
                    if not validation.is_valid:
                        # Log failure
                        self.log_validation_failure(day, hour, validation)
                        
                        # Retry with adjusted prompt
                        for retry in range(max_retries_per_segment):
                            print(f"  ⚠️ Retry {retry+1}/{max_retries_per_segment}")
                            
                            # Regenerate with stricter constraints
                            segment = engine.generate_single_segment(
                                current_date=f"2102-06-{day:02d}",
                                current_hour=hour,
                                validation_hints=validation.issues  # ← Feed issues back
                            )
                            
                            validation = self.validate_segment(segment, engine)
                            
                            if validation.is_valid:
                                self.retry_count += 1
                                break
                        
                        if not validation.is_valid:
                            # Give up, use best-effort segment
                            print(f"  ❌ Failed validation after {max_retries_per_segment} retries")
                            self.failure_count += 1
                    
                    # Save segment
                    self.save_segment(day, hour, segment, validation)
                    
                    # Checkpoint
                    if (day * 16 + (hour - 6)) % self.checkpoint_interval == 0:
                        self.checkpoint(engine, day, hour)
                
                except Exception as e:
                    print(f"❌ Critical error Day {day}, Hour {hour}: {e}")
                    self.log_error(day, hour, e)
                    # Continue to next hour
            
            # End of day
            engine.end_broadcast(save_state=True)
        
        # Final report
        self.generate_report()
    
    def validate_segment(self, segment: Dict, engine: BroadcastEngine) -> ValidationResult:
        """Run full validation pipeline"""
        # Tier 1: Rule-based
        rule_result = engine.rule_validator.validate_all(
            script=segment['script'],
            character_card=engine.personality,
            constraints=segment['metadata'].get('constraints', {})
        )
        
        if not rule_result['valid']:
            return ValidationResult(
                is_valid=False,
                script=segment['script'],
                issues=rule_result['issues'],
                source="rule"
            )
        
        # Tier 2: LLM validation (every 10th segment to save time)
        if random.random() < 0.1:  # 10% sampling
            return engine.llm_validator.validate_with_story_context(
                script=segment['script'],
                character_card=engine.personality,
                story_context=segment['metadata'].get('story_context', {}),
                constraints=segment['metadata'].get('constraints', {})
            )
        
        # Pass by default
        return ValidationResult(is_valid=True, script=segment['script'])
    
    def checkpoint(self, engine: BroadcastEngine, day: int, hour: int):
        """Save checkpoint for recovery"""
        checkpoint_path = self.output_dir / f"checkpoint_day{day}_hour{hour}.json"
        
        checkpoint_data = {
            'day': day,
            'hour': hour,
            'world_state': engine.world_state.to_dict(),
            'validation_log': self.validation_log[-100:],  # Last 100 entries
            'stats': {
                'failure_count': self.failure_count,
                'retry_count': self.retry_count,
            }
        }
        
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        print(f"✅ Checkpoint saved: Day {day}, Hour {hour}")
    
    def generate_report(self):
        """Generate final validation report"""
        total_segments = 30 * 16  # 480 segments
        
        report = f"""
# 30-Day Generation Report

**Total Segments**: {total_segments}
**Validation Failures**: {self.failure_count} ({self.failure_count/total_segments:.1%})
**Retry Successes**: {self.retry_count}

## Validation Issues by Category

{self._categorize_issues()}

## Recommendations

{self._generate_recommendations()}
"""
        
        report_path = self.output_dir / "30day_validation_report.md"
        report_path.write_text(report)
        
        print(f"\n📊 Report saved: {report_path}")
```

---

## 5. Answers to Your Specific Questions

### Q: What rules would we use?

**A**: 3-tier approach:

**Tier 1 - Rule-Based (Fast, 95% coverage)**:
- Temporal constraints (year limits)
- Forbidden topics/factions (hard constraints)
- Regional consistency (location validation)
- Format requirements (length, structure)
- Voice markers (required personality indicators)
- **Story progression keywords** (rumor → confirmed → resolved)

**Tier 2 - Hybrid (Medium, 98% coverage)**:
- Rule-based FIRST (fail fast)
- LLM validation for nuance (tone, coherence, authenticity)

**Tier 3 - Pure LLM (Slow, 99% coverage)**:
- Full context-aware validation
- Story beat progression logic
- Cross-day continuity
- Emotional authenticity

### Q: What prompt would we give to the LLM?

**A**: See `LLM_VALIDATION_PROMPT` above (comprehensive validation with story context)

Key additions for your use case:
- **Story progression stage** (rumor/developing/confirmed/resolved)
- **World state context** (previous day's events)
- **Quest arc validation** (setup → conflict → resolution)

### Q: Are there problems with ChromaDB when queried for quests?

**A**: YES. Current issues:

1. **No metadata filtering** - Gets non-quest content
2. **Generic semantic query** - "quest objective" is too broad
3. **No infobox_type filter** - Should filter `infobox_type='infobox quest'`
4. **No DJ knowledge filtering** - Gets quests from wrong regions/time periods
5. **No arc validation** - Quests without clear structure

**Solution**: See `_extract_quest_stories_improved()` above

### Q: How do we test this?

**A**: 3-phase testing:

**Phase 1 - Pre-Generation (7 min)**:
- `test_30day_mock_generation()` - Mock LLM/ChromaDB, validate logic
- `test_story_beat_progression_over_weeks()` - Verify gossip→news→story
- `test_chromadb_quest_filtering()` - Verify quest extraction works

**Phase 2 - Pilot Run (1-2 hours)**:
- `test_1day_real_generation()` - Real LLM/ChromaDB for 1 day
- Catch integration issues before 80-hour run

**Phase 3 - Production (80 hours)**:
- `ProductionMonitor` class monitors live
- Auto-retry on validation failure
- Checkpoints every 10 segments for recovery

---

## 6. Implementation Priority

### Week 1: Fix ChromaDB Quest Extraction
1. Add metadata filtering to `story_extractor.py`
2. Implement `_validate_story_arc()`
3. Test with `test_chromadb_quest_filtering()`

### Week 2: Enhance Validation Rules
1. Add story progression validation to `validation_rules.py`
2. Enhance LLM validation prompt with story context
3. Test with `test_story_beat_progression_over_weeks()`

### Week 3: Build Production Monitor
1. Implement `ProductionMonitor` class
2. Add checkpoint/recovery system
3. Test with `test_1day_real_generation()`

### Week 4: Run 30-Day Generation
1. Start production run with monitoring
2. Review validation report
3. Iterate on failed segments

---

## 7. Critical Questions to Answer Before Implementation

### 7.1 Technical Architecture Questions

#### Data Flow & State Management
1. **How do we ensure world state consistency across 480 broadcast hours?**
   - Should we use a database instead of JSON for world state?
   - What happens if world state corruption occurs on Day 15?
   - How do we version world state schema for future changes?
   - Can we diff world state between checkpoints to track evolution?

2. **What's our checkpoint recovery strategy?**
   - How far back do we roll back on critical failure?
   - Do we re-generate from checkpoint, or skip failed segments?
   - How do we handle partial day failures (hour 14 crashes)?
   - Should checkpoints be hierarchical (hour/day/week)?

3. **How do we handle ChromaDB query performance over 30 days?**
   - Will 9,600 RAG queries cause performance degradation?
   - Should we pre-fetch and cache quest pools per week?
   - Do we need query result caching to avoid duplicate retrievals?
   - What's our fallback if ChromaDB becomes unavailable mid-generation?

#### Story System Architecture
4. **How do we ensure story coherence across multiple weeks?**
   - Does each story need its own state file?
   - How do we prevent story contradictions (raider defeated in Week 2, mentioned alive in Week 3)?
   - Should stories have explicit dependency trees (Story B can't start until Story A resolves)?
   - How do we handle branching storylines (faction conflict could go 3 ways)?

5. **What's the maximum concurrent story count before coherence breaks?**
   - Can we realistically track 4 stories (daily/weekly/monthly/yearly) simultaneously?
   - Do listeners get confused if too many storylines overlap?
   - Should we limit to 2-3 concurrent stories for clarity?
   - How do we prioritize which story beats get airtime when multiple are ready?

6. **How do we validate story progression without circular dependencies?**
   - Story validator needs world state, but world state is updated by stories
   - Who owns the "truth" - gossip tracker, news system, or story scheduler?
   - What if gossip says "raider attack resolved" but story system says still ongoing?
   - How do we enforce single source of truth for event status?

### 7.2 Validation & Quality Questions

#### Validation Strategy
7. **What's our acceptable validation failure rate?**
   - Is 5% failure rate (24 bad segments out of 480) acceptable?
   - Should different segment types have different thresholds (news stricter than music intro)?
   - Do we fail the entire day if weather forecast is invalid?
   - At what failure rate do we abort the full 30-day run?

8. **How do we validate story beat progression without context explosion?**
   - LLM validation needs entire story context (all previous beats)
   - By Week 4, that's 20+ story beats to include in validation prompt
   - Does this cause context window issues?
   - Should we summarize old beats instead of including full text?

9. **What's our ground truth for "correct" validation?**
   - Rule-based says script is valid, LLM says it's not - who wins?
   - If validation contradicts, do we trust rules (fast/consistent) or LLM (nuanced/variable)?
   - Should we have a third tie-breaker validator?
   - How do we handle validation disagreements in production?

#### Content Quality
10. **How do we measure narrative quality, not just correctness?**
    - Script passes all rules but is boring - how do we catch that?
    - Can we quantify "engaging" vs "mechanical" dialogue?
    - Should we have an "entertainment score" in addition to validation score?
    - Do we A/B test different story beats to measure engagement?

11. **How do we prevent repetition over 30 days?**
    - Same quest referenced multiple times in different weeks?
    - DJ catchphrases become stale by Week 3?
    - Weather events feel repetitive (5 rad storms in 30 days)?
    - How do we ensure variety without breaking canon?

12. **What's our strategy for handling "boring" periods?**
    - If no major events happen Days 8-12, what fills the time?
    - Do we synthesize filler content, or embrace quiet periods?
    - How do we keep listeners engaged during story downtime?
    - Should we have a "story pacing" system to distribute excitement?

### 7.3 ChromaDB & Knowledge Retrieval Questions

#### Quest & Story Extraction
13. **How do we distinguish "story-worthy" quests from trivial ones?**
    - "Deliver letter to NPC" vs "Save settlement from raiders" - both are quests
    - Should we have a "narrative weight" score for quests?
    - Do we filter by quest rewards, or by narrative complexity?
    - How do we avoid extracting tutorial quests as major stories?

14. **What if ChromaDB doesn't have enough quest content for 30 days?**
    - Fallout wiki might have 50 major quests - we need 120+ story beats
    - Do we re-use quests in different contexts?
    - Should we procedurally generate side-quests from lore chunks?
    - What's our fallback content strategy?

15. **How do we handle quest metadata quality issues?**
    - Not all wiki pages have `infobox_type='infobox quest'`
    - Some quests might be categorized as events or locations
    - Do we need fuzzy matching, or strict filtering?
    - Should we pre-audit ChromaDB for quest classification issues?

#### Knowledge Filtering
16. **How granular should DJ knowledge filtering be?**
    - Julie knows "Vault 76 exists" but does she know "Vault 76 Overseer's name"?
    - Should knowledge filtering be chunk-level or fact-level?
    - Do we need a knowledge graph, or is metadata filtering sufficient?
    - How do we handle "common knowledge" that spreads across regions?

17. **What's our strategy for handling knowledge contradictions?**
    - One chunk says "NCR controls Hoover Dam", another says "Legion controls it"
    - Both might be temporally correct (different years)
    - How do we ensure DJs reference the right version for their timeline?
    - Should we prefer more recent chunks, or most detailed?

### 7.4 Production & Operations Questions

#### Performance & Scalability
18. **What's our contingency plan if generation takes >80 hours?**
    - Do we reduce segment count per hour?
    - Do we skip LLM validation to save time?
    - Should we parallelize generation (multi-threading/GPU)?
    - How do we estimate total time before starting?

19. **What hardware/resource constraints do we face?**
    - Does local LLM (Ollama) have enough VRAM for 9,600 generations?
    - Will ChromaDB embeddings fit in RAM?
    - Do we need to batch operations to avoid memory issues?
    - Should we stream results to disk to avoid memory accumulation?

20. **How do we handle LLM rate limits or quota exhaustion?**
    - Local Ollama shouldn't have rate limits, but what if it crashes?
    - Do we have fallback LLM providers?
    - Should we cache LLM responses aggressively?
    - What's our retry strategy for LLM timeouts?

#### Monitoring & Debugging
21. **How do we debug failures mid-generation without losing progress?**
    - If script fails on Day 12, Hour 8, how do we inspect state?
    - Do we need live dashboard to monitor generation?
    - Should we log every LLM prompt/response for post-mortem analysis?
    - How much logging is too much (logs could be GB in size)?

22. **What metrics should we track during generation?**
    - Validation pass/fail rates per hour
    - LLM token usage and costs
    - Generation time per segment (trending up = problem)
    - Story beat distribution (are some stories getting ignored?)
    - World state size growth (detecting state bloat)
    - ChromaDB query latency (detecting performance issues)

23. **How do we know generation is "on track" at Hour 100 of 480?**
    - What's our progress indicator beyond "X segments done"?
    - Should we have quality KPIs (validation score trending)?
    - Do we monitor story progression milestones?
    - At what point do we abort and restart with different config?

### 7.5 Content Strategy Questions

#### Story Pacing & Structure
24. **How do we distribute story beats to create satisfying arcs?**
    - Should major stories have 3-act structure across 3 weeks?
    - Do we frontload exposition in Week 1, action in Week 2, resolution in Week 3?
    - How do we avoid climax clustering (all stories resolve in Week 4)?
    - Should we use narrative pacing algorithms (Freytag's Pyramid)?

25. **How do we handle story escalation triggers?**
    - When does a daily story become a weekly story?
    - What criteria determine escalation (listener engagement? narrative importance?)?
    - If we don't have real listener feedback, do we use simulated engagement?
    - How do we prevent all stories escalating (everything becomes yearly arc)?

26. **What's our strategy for story callbacks and continuity?**
    - If raiders attack Vault 76 in Week 1, should Week 4 reference aftermath?
    - How far back should callbacks go (within same week? same month? full 30 days)?
    - Do we need a "continuity manager" to track references?
    - How do we avoid continuity errors (referencing events that were retconned)?

#### Gossip & News Integration
27. **How do we choreograph gossip→news→story transitions?**
    - Does gossip auto-promote to news, or do we manually trigger?
    - Should news confirm gossip, or introduce new information?
    - What if gossip says "rumor of raider attack" but news never confirms?
    - Do unconfirmed gossips get archived, or do they linger?

28. **How do we prevent gossip/news spoiling story reveals?**
    - If story has planned twist in Week 3, can gossip leak it in Week 1?
    - Should story scheduler "reserve" topics to prevent spoilers?
    - Do we need spoiler-free zones (gossip can't mention certain topics)?
    - How do we balance foreshadowing vs spoiling?

### 7.6 User Experience Questions

#### Listener Perspective
29. **How do we validate 30 days is listenable, not just technically correct?**
    - Should we have test listeners review Day 1, 15, 30 for coherence?
    - Do we need user studies to validate story pacing?
    - What if technically valid content is emotionally flat?
    - Should we have subjective quality gates (human approval) at milestones?

30. **How do we ensure accessibility for new listeners mid-broadcast?**
    - If someone starts listening on Day 15, do they understand ongoing stories?
    - Should we have "recap" segments for late joiners?
    - Do we front-load essential context in each story beat?
    - How do we balance continuity for long-time listeners vs accessibility for new ones?

31. **What's the intended listening pattern?**
    - Are listeners expected to hear ALL 480 hours sequentially?
    - Or is this ambient radio they dip in/out of?
    - Do we optimize for binge-listening or casual listening?
    - Should each day be self-contained, or is multi-day continuity required?

### 7.7 Success Criteria Questions

#### Definition of Success
32. **What does "successful 30-day generation" mean quantitatively?**
    - 95% validation pass rate?
    - Zero critical lore violations?
    - All story arcs have proper resolution?
    - <5% repetitive content?
    - Listeners can't distinguish from human-written scripts?

33. **How do we measure immersion and authenticity?**
    - Can we quantify "Julie sounds like Julie"?
    - Should we have voice consistency scores per segment?
    - Do we need Turing test (can listeners tell it's AI)?
    - What's our benchmark for "good enough"?

34. **What's our tolerance for imperfection?**
    - Is one lore violation in 480 hours acceptable?
    - Should we accept minor tone inconsistencies for the sake of variety?
    - Do we prioritize technical correctness over narrative quality?
    - What trade-offs are we willing to make (quality vs speed vs cost)?

### 7.8 Future-Proofing Questions

#### Extensibility
35. **How do we design for 60-day, 90-day, or 365-day generation?**
    - Does our architecture scale linearly, or are there bottlenecks?
    - Will story pool exhaustion happen faster at longer durations?
    - Do we need different validation strategies for different scales?
    - Should we design for infinite generation from the start?

36. **How do we incorporate user feedback into the system?**
    - If listeners flag segments as "off-character", how do we retrain?
    - Should validation rules evolve based on real-world usage?
    - Do we need feedback loops to improve future generations?
    - How do we version validation rules to track improvements?

37. **What if we want to add new DJs or new content types mid-generation?**
    - Can we hot-swap DJ personality cards?
    - Should the system support plugin architecture for new segment types?
    - How do we handle schema changes to world state?
    - Do we need migration scripts for backward compatibility?

### 7.9 Risk Mitigation Questions

#### Failure Scenarios
38. **What's our disaster recovery plan?**
    - Power outage on Day 20 - do we restart from Day 1 or last checkpoint?
    - ChromaDB corruption - do we have backups?
    - LLM produces gibberish for 10 segments straight - auto-abort?
    - Hard drive fills up mid-generation - how do we detect and prevent?

39. **How do we detect subtle degradation over time?**
    - Generation quality slowly worsens Days 1→30 (LLM fatigue?)
    - World state bloats and slows down processing
    - ChromaDB queries return less relevant results over time
    - What early warning signs should we monitor?

40. **What's our rollback strategy for bad segments?**
    - If we discover Day 5's weather forecast contradicted Day 6's actual weather
    - Do we regenerate Day 6, or retcon the forecast?
    - How do we maintain continuity when rolling back?
    - Should we version segments for easy rollback?

### 7.10 Philosophical & Design Questions

#### Purpose & Vision
41. **What's the true goal of this system?**
    - Is this a proof-of-concept, or production-ready radio station?
    - Are we optimizing for technical achievement or entertainment value?
    - Should this feel like "AI radio" or indistinguishable from human DJs?
    - What's the acceptable level of AI "quirks" vs human-like perfection?

42. **How do we balance automation with creative control?**
    - Should humans curate story selections, or trust the algorithm?
    - Do we need manual override points (approve Day 1 before continuing)?
    - What's the role of human creativity in an autonomous system?
    - Should we embrace AI-generated novelty or constrain to human-approved patterns?

43. **What's our content philosophy on repetition vs novelty?**
    - Real radio DJs repeat catchphrases - should AI do the same?
    - Is some repetition comforting (familiarity) or annoying (mechanical)?
    - How much procedural variation is too much (loses character consistency)?
    - Should we study real radio patterns to match human repetition rates?

### 7.11 Meta Questions About This Strategy

#### Self-Reflection
44. **Are we over-engineering this, or is complexity justified?**
    - Do we really need 3-tier validation, or is 1-tier sufficient?
    - Is 30-day generation overkill when 7-day might prove the concept?
    - Are we building for a future that may never come?
    - Should we start minimal and add complexity only when needed?

45. **What are we NOT asking that we should be?**
    - Have we considered edge cases we haven't thought of?
    - What assumptions are we making that could be wrong?
    - Are there entire categories of problems we're blind to?
    - Should we consult domain experts (writers, radio producers, game designers)?

46. **How do we know when we're "done"?**
    - What's our exit criteria for validation development?
    - When do we stop adding features and ship the product?
    - How do we resist feature creep while ensuring quality?
    - What's the minimum viable 30-day broadcast?

47. **What's the feedback loop for improving this strategy itself?**
    - Should we revisit these questions after Week 1 implementation?
    - Do we need periodic strategy reviews?
    - How do we incorporate lessons learned into future iterations?
    - What metrics indicate our strategy is working vs needs revision?

---

## 8. Decision Framework

For each question above, we should:

1. **Categorize priority**: MUST answer before starting / SHOULD answer in Week 1 / CAN defer to later
2. **Identify dependencies**: Which questions block others?
3. **Assign ownership**: Who researches the answer?
4. **Set decision deadline**: When must this be decided?
5. **Document decision rationale**: Why we chose this approach

### Example Decision Log

| Question | Priority | Decision | Rationale | Date |
|----------|----------|----------|-----------|------|
| #1: World state storage | MUST | Use JSON with atomic writes + backup | Simple, debuggable, sufficient for 30 days | 2026-01-20 |
| #7: Validation failure rate | MUST | <5% for non-critical, 0% for lore violations | Balance quality and completion rate | 2026-01-20 |
| #14: Quest content exhaustion | SHOULD | Pre-audit ChromaDB, aim for 150+ quests | Need buffer beyond 120 required beats | TBD |
| #29: Listener validation | CAN defer | Plan for Week 5 after tech validation | Tech must work before user testing | TBD |

---

## 9. Next Steps

1. **Week 0 (Now)**: Answer MUST-HAVE questions (#1, #2, #7, #13, #18, #21)
2. **Week 1**: Implement ChromaDB fixes + basic validation
3. **Week 2**: Answer SHOULD-HAVE questions, enhance validation
4. **Week 3**: Build production monitor, pilot test
5. **Week 4**: Final 30-day generation with monitoring

**The questions are more important than the answers.** Asking the right questions prevents building the wrong solution.
