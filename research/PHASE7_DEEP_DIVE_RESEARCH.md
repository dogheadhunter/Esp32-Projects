# Phase 7: Deep Dive Research
## Multi-Temporal Story System

**Created**: January 17, 2026  
**Status**: Research Complete  
**Related**: [PHASE7_MULTI_TEMPORAL_STORY_SYSTEM.md](../docs/PHASE7_MULTI_TEMPORAL_STORY_SYSTEM.md)

---

## 1. Narrative Arc Detection

### Key Findings

**Academic Research (Boyd et al., 2020 - Science Advances)**
- Narrative arcs can be detected through linguistic analysis using three dimensions:
  1. **Staging**: Setup elements (scene-setting language, character introductions)
  2. **Plot Progression**: Movement through the story (pronouns, auxiliary verbs, connectives)
  3. **Cognitive Tension**: Peak moments where characters work through issues

**Detection Methods**
- **LIWC (Linguistic Inquiry and Word Count)**: Tool specifically designed for narrative arc analysis
- **Function words**: Pronouns and connectives indicate narrative cohesion and plot movement
- **Sentiment trajectory**: Emotional tone changes map to Freytag's pyramid stages

**Freytag's Pyramid Stages (Detectable)**
1. Exposition/Introduction
2. Rising Action
3. Climax
4. Falling Action
5. Resolution/Denouement

### Implementation Approach
- Use VADER sentiment analysis to track emotional trajectory through text chunks
- Map sentiment changes to act types (setup=neutral/positive, climax=high tension, resolution=return to neutral)
- Detect staging via presence of location descriptions, character introductions
- Detect climax via conflict keywords: "battle", "fight", "confrontation", "showdown"
- Detect resolution via outcome keywords: "victory", "defeat", "peace", "ended"

### Tools Available
- **VADER**: Lexicon-based sentiment analysis, works well on non-social-media text
- **spaCy**: NER for character/location detection
- **Custom keyword patterns**: For Fallout-specific narrative markers

---

## 2. Quest Structure Detection

### Doran & Parberry Research (2011)
Analysis of 750+ quests from Eve Online, World of Warcraft, Everquest, and Vanguard reveals:

**Common Quest Actions**
| Action | Description |
|--------|-------------|
| Kill | Defeat specific enemy or enemy type |
| Gather | Collect items from world or enemies |
| Escort | Protect NPC during travel |
| Deliver | Transport item to destination |
| Fetch | Retrieve specific item and return |
| Investigate | Discover information/location |
| Defend | Protect location or NPC for duration |
| Rescue | Free captured NPC |

**Quest Structure Grammar**
Quests can be expressed as trees with:
- **Motivation** (why NPC wants help) → root
- **Actions** (what player does) → branches
- **Subquests** (nested requirements) → sub-branches

**Fallout-Specific Quest Types**
From Fallout Wiki analysis:
- Main quests (story-critical)
- Side quests (optional narrative)
- Radiant quests (procedurally generated in Fallout 4)
- Miscellaneous (small objectives)

### Detection Strategy for ChromaDB
1. **Infobox-based**: Wiki infobox type = "quest" is direct indicator
2. **Content-type metadata**: Already have `content_type` field
3. **Keyword patterns**: Look for quest-indicator words in text:
   - "objective", "reward", "complete", "return to", "speak with"
   - "quest giver", "quest stages", "walkthrough"
4. **Structure markers**: Presence of numbered steps, bullet points

---

## 3. Story Coherence

### Semantic Chunking Research (Chroma Research)
- **ClusterSemanticChunker**: Algorithm that maximizes cosine similarity within chunks
- Preserving sentence boundaries maintains semantic coherence
- Embedding similarity can detect natural breakpoints in narratives

### Coherence Strategies
1. **Source Grouping**: Group chunks by `wiki_title` to keep related content together
2. **Temporal Ordering**: Use `year_min`/`year_max` metadata to order events chronologically
3. **Entity Consistency**: Track characters/locations across acts to ensure continuity
4. **Theme Threading**: Use existing `theme_*` metadata to maintain thematic coherence

### Validation Approach
- Query related chunks using semantic similarity
- Score coherence by measuring cross-chunk entity overlap
- Flag stories where characters appear in wrong time periods
- Use LoreValidator to catch faction/timeline inconsistencies

---

## 4. Engagement Simulation

### Player Engagement Metrics (Game Design Research)
Without real user feedback, simulate engagement using heuristics:

**Proxy Metrics**
| Metric | How to Simulate |
|--------|-----------------|
| Interest | Story novelty (not recently broadcast) |
| Variety | Diversity of themes/locations |
| Pacing | Broadcast spacing (not too frequent, not too rare) |
| Completion | Story reaching resolution vs abandonment |
| Complexity | Match to DJ's complexity tier |

**Engagement Score Formula**
```
engagement = base_score 
           * novelty_factor      (0.5-1.5 based on freshness)
           * variety_bonus       (0.8-1.2 based on theme diversity)
           * pacing_penalty      (0.7-1.0 if too frequent)
           * completion_boost    (1.0-1.3 for stories near resolution)
```

**Decay Factors**
- Interest decays if same story beats repeat too often
- Variety factor drops if same location/faction dominates
- Pacing penalty increases if story advances too frequently

### Retention Heuristics
From narrative pacing research:
- **Tension Variation**: Constant high tension exhausts; constant low bores
- **Fichtean Curve**: Cyclical rising/crisis pattern prevents reader fatigue
- **Valley Progression**: Each "valley" (low tension moment) should be higher than the previous

---

## 5. Escalation Criteria

### When Stories Should Escalate

**Quantitative Triggers**
- Minimum broadcast count reached (e.g., daily story told 4+ times)
- High simulated engagement score (> 0.8)
- Story completed successfully (not abandoned)

**Qualitative Triggers**
- Story involves major faction (NCR, Legion, Brotherhood)
- Story impacts significant location
- Story has unresolved consequences (cliffhanger potential)
- Story connects to existing weekly/monthly arc

**Escalation Probability Formula**
```
prob = base_probability[timeline]
     * engagement_score
     * faction_importance_bonus     (1.0-1.5)
     * location_significance_bonus  (1.0-1.3)
     * connection_bonus             (1.0-1.2 if ties to larger arc)
```

### Escalation Transformation
- Daily → Weekly: Expand from 2 acts to 3-4 acts
- Weekly → Monthly: Add subplot, deepen consequences
- Monthly → Yearly: Generalize to world-changing event

---

## 6. Cross-Timeline Callbacks

### Episodic Storytelling Techniques
From TV writing research:

**Callback Types**
1. **Direct Reference**: "Remember that scavenger from yesterday? Well..."
2. **Thematic Echo**: Same theme in different timeline contexts
3. **Consequence Link**: Daily event is symptom of weekly cause
4. **Foreshadowing**: Weekly story hints at monthly development

**When to Use Callbacks**
| From → To | When Appropriate |
|-----------|------------------|
| Daily → Weekly | Daily event is example of weekly trend |
| Daily → Monthly | Daily character connected to major arc |
| Weekly → Monthly | Weekly resolution triggers monthly consequence |
| Any → Yearly | Any story contributes to epic narrative |

**Implementation**
- Track recent story segments (last 10-20)
- Check for shared entities (location, faction, theme)
- Probability-based callback injection (20-30% when related)
- Generate callback phrases: "Speaking of [location]...", "This reminds me of..."

---

## 7. LLM-Assisted Story Extraction

### Ollama Structured Outputs
Ollama supports JSON schema enforcement via:
- `format` parameter with Pydantic model schema
- Instructor library for structured extraction

**Recommended Approach**
```python
# Pydantic model for story extraction
class ExtractedStory(BaseModel):
    title: str
    summary: str
    acts: List[StoryAct]
    themes: List[str]
    emotional_arc: str
    
# Ollama call with structured output
response = ollama.generate(
    model="llama3.2",
    prompt=extraction_prompt,
    format=ExtractedStory.model_json_schema()
)
```

**Prompt Engineering for Story Extraction**
- Provide clear JSON schema in prompt
- Include examples of well-structured stories
- Ask for specific fields: acts, themes, conflicts, resolution
- Use role prompting: "You are a narrative analyst..."

### When to Use LLM vs Rule-Based
| Approach | Use When |
|----------|----------|
| Rule-based | Clear structural markers (infoboxes, headers) |
| LLM-assisted | Unstructured prose, implicit narrative structure |
| Hybrid | Rule-based extraction + LLM summarization |

---

## 8. Wiki Content Classification

### Infobox Types (from Fallout Wiki structure)
| Infobox Type | Maps To |
|--------------|---------|
| `infobox character` | character content |
| `infobox location` | location content |
| `infobox quest` | quest content |
| `infobox faction` | faction content |
| `infobox event` | event content |
| `infobox item` | item content |
| `infobox creature` | creature content |

### Content Type Detection (already in ChromaDB)
The Phase 6 enrichment already includes `content_type` classification:
- Use existing metadata for filtering
- Quest detection via infobox + content_type
- Event detection via year metadata + event keywords

### Additional Markers for Story-Worthy Content
- Has associated quest(s)
- Involves named characters
- Has temporal markers (dates, eras)
- Contains conflict/resolution language
- Located in explorable area

---

## 9. Radio DJ Dialogue Patterns

### Mr. New Vegas Analysis
From Fallout Wiki dialogue files:

**Structural Patterns**
1. **Greeting**: "This is Mr. New Vegas..." / "Welcome back to..."
2. **Transition**: "And now..." / "Speaking of which..."
3. **News Intro**: "News time, children..." / "Word from the wasteland..."
4. **Commentary**: Adds personal reaction to news
5. **Music Lead-in**: "Here's a song for you..." / "Let's have some music..."

**Tonal Characteristics**
- Smooth, reassuring delivery
- Uses endearments ("children", "you beautiful people")
- Maintains positive spin on negative news
- References Courier's deeds dynamically

### Callback Integration for DJs
- Mr. New Vegas: Casual, warm callbacks ("Remember when I told you about...")
- Three Dog: Energetic, emphatic callbacks ("And get THIS, children!")
- Travis (Nervous): Hesitant callbacks ("Oh, uh, speaking of which...")
- Julie: Clinical, informative callbacks ("Following up on our earlier report...")

---

## 10. Pacing and Tension Curves

### Fichtean Curve
Alternative to Freytag's pyramid:
- Starts with immediate conflict (no slow exposition)
- Multiple rising crises before climax
- Shorter falling action
- Better for serialized/episodic content

### Tension Variation Principles
1. **Never constant**: Alternate high/low tension
2. **Valleys rise**: Each rest should be "higher" than previous
3. **Match timeline**: Daily=quick cycles, Yearly=slow build
4. **Avoid fatigue**: Long high-tension exhausts audience

### Broadcast Spacing by Timeline
| Timeline | Min Spacing | Max Spacing | Tension Pattern |
|----------|-------------|-------------|-----------------|
| Daily | 1 broadcast | 3 broadcasts | Quick spike/resolve |
| Weekly | 3 broadcasts | 6 broadcasts | Building waves |
| Monthly | 5 broadcasts | 15 broadcasts | Slow crescendo |
| Yearly | 10 broadcasts | 30 broadcasts | Epic build |

---

## 11. Implementation Priorities

Based on research, recommended implementation order:

### Must-Have (Week 1-2)
1. **Quest detection via infobox_type + content_type** - Already have metadata
2. **Basic sentiment tracking with VADER** - Well-documented, easy to implement
3. **Keyword-based act detection** - Conflict/resolution word lists

### Should-Have (Week 3-4)
4. **Engagement simulation formula** - Use proxy metrics
5. **Cross-timeline callback system** - Entity matching
6. **Escalation probability engine** - Configurable thresholds

### Nice-to-Have (Week 5-6)
7. **LLM-assisted story summarization** - Ollama structured outputs
8. **Advanced coherence scoring** - Semantic similarity validation
9. **Fichtean curve pacing** - Tension variation optimization

---

## 12. Risk Mitigation

### Potential Issues & Mitigations

| Risk | Mitigation |
|------|------------|
| Story extraction finds no quests | Fallback to event/location-based stories |
| Sentiment analysis inaccurate for Fallout tone | Custom lexicon additions for wasteland terms |
| Engagement simulation doesn't correlate with quality | Tune weights iteratively, add randomness |
| LLM extraction inconsistent | Use rule-based as primary, LLM as enhancement |
| Callbacks feel forced | Probability-based with low baseline (20%) |

---

## 13. References

### Academic Papers
- Boyd et al. (2020) "The narrative arc: Revealing core narrative structures through text analysis" - Science Advances
- Doran & Parberry (2011) "A Prototype Quest Generator Based on a Structural Analysis of Quests from Four MMORPGs" - PCG Workshop
- Chambers & Jurafsky (2008) "Unsupervised Learning of Narrative Event Chains" - Stanford NLP

### Tools & Libraries
- VADER Sentiment Analysis: github.com/cjhutto/vaderSentiment
- Ollama Structured Outputs: ollama.com/blog/structured-outputs
- Instructor (Pydantic + LLM): python.useinstructor.com
- Chroma Chunking Research: research.trychroma.com/evaluating-chunking

### Game Design Resources
- Pinelle et al. "Heuristic Evaluation for Games" - CHI 2008
- Desurvire "Heuristics for Evaluating Playability" - Game UX research
- Fallout Wiki dialogue files: fallout.fandom.com

### Narrative Craft
- Mythcreants "How to Pace Your Story" - mythcreants.com
- Novlr "The Fichtean Curve" - novlr.org
- Fiveable "Writing the Episodic Drama" course notes
