# Script Generation Quality Checklist

Use this checklist to ensure consistent quality across all generated radio scripts.

---

## Pre-Generation Checklist

**System Requirements:**
- [ ] Ollama server running (`ollama serve` in terminal)
- [ ] ChromaDB accessible at `tools/wiki_to_chromadb/chroma_db/`
- [ ] Model downloaded (`ollama pull fluffy/l3-8b-stheno-v3.2`)
- [ ] Output directory exists (`script generation/scripts/` or target folder)
- [ ] DJ personality files present for selected character (`dj personality/[DJ_Name]/character_card.json`)

**Environment Check:**
- [ ] Python environment activated (`chatterbox_env` or `wiki_to_chromadb/venv`)
- [ ] Dependencies installed (`jinja2`, `chromadb`, `requests`)
- [ ] VRAM available (need ~4.5GB for Ollama + ChromaDB)
- [ ] Disk space available (scripts are small, ~2KB each)

**Generation Parameters:**
- [ ] Script type selected (weather/news/time/gossip/music_intro)
- [ ] DJ name formatted correctly (e.g., `"Julie (2102, Appalachia)"`)
- [ ] Context query prepared (relevant to script type and DJ's knowledge)
- [ ] Template variables defined (hour, weather_type, news_topic, etc.)
- [ ] Output filename pattern decided (default: `{type}_{dj}_{timestamp}.txt`)

---

## During Generation: Per-Script Quality Checks

### 1. Word Count (Target ±20% acceptable)
- [ ] **Weather:** 80-180 words (target: 80-100, accepts up to 180)
- [ ] **News:** 120-200 words (target: 120-150, accepts up to 200)
- [ ] **Time:** 40-80 words (target: 40-60, accepts up to 80)
- [ ] **Gossip:** 80-180 words (target: 80-120, accepts up to 180)
- [ ] **Music Intro:** 60-100 words (target: 60-80, accepts up to 100)

**If out of range:**
- Mild overage (10-30%): Acceptable - provides better content
- Severe overage (>50%): Review for repetition, may need regeneration
- Underage (<80% of target): Script may feel rushed - consider regeneration

### 2. Character Voice Consistency
- [ ] **Catchphrase present:** Uses at least 1 signature phrase from DJ's catchphrase list
  - Julie examples: "This is Julie", "Hey wastelanders", "Stay safe out there"
  - Travis examples: "Um, this is Travis", "DCR - uh, Diamond City Radio"
  - Mr. New Vegas examples: "This is Mr. New Vegas", "Ain't that a kick in the head"
- [ ] **Tone appropriate:** Matches DJ's personality profile (upbeat/nervous/smooth/etc.)
- [ ] **No forbidden patterns:** Avoids phrases from DJ's "dont" list
  - Julie: No corporate jargon, no technical Vault-Tec speak
  - Travis (Nervous): No confident swagger
  - Travis (Confident): No nervous stuttering
- [ ] **Natural dialogue:** Sounds like spoken radio, not written essay

**Manual Test:** Read script aloud - does it sound like the DJ?

### 3. Lore Accuracy ⚠️ CRITICAL
- [ ] **Temporal consistency:** No references to events/factions after DJ's year
  - Julie (2102): No NCR, no Institute, no Railroad, no Minutemen (post-2102 events)
  - Mr. New Vegas (2281): No Institute/Railroad (Commonwealth 2287 events)
  - Travis (2287): Full Fallout timeline accessible
- [ ] **Geographic consistency:** Locations match DJ's region
  - Julie → Appalachia (WV): Vault 76, Flatwoods, Charleston, Morgantown, etc.
  - Mr. New Vegas → Mojave: New Vegas, Hoover Dam, Goodsprings, etc.
  - Travis → Commonwealth (MA): Diamond City, Goodneighbor, Sanctuary, etc.
- [ ] **No anachronisms:** No real-world references (modern tech, brands, politicians)
- [ ] **Faction accuracy:** Factions mentioned exist and are active in DJ's time/place
- [ ] **No contradictions:** Doesn't contradict established lore from games

**Red Flags:**
- Mentions of real-world brands (Coca-Cola, Google, Microsoft, etc.)
- Post-war factions in pre-founding timeframes
- Modern technology (smartphones, internet, satellites working)
- Events from wrong games/regions (e.g., Julie talking about Diamond City)

### 4. Content Quality
- [ ] **Sentence variety:** No excessively long sentences (>30 words)
- [ ] **Minimum structure:** At least 3 complete sentences
- [ ] **No excessive repetition:** No non-common word used >3 times
- [ ] **Natural pacing:** Script flows smoothly when read aloud
- [ ] **Engaging content:** Provides value (information, entertainment, atmosphere)
- [ ] **Context appropriate:** Weather talks about weather, news about events, etc.

### 5. Technical Format
- [ ] **Metadata present:** JSON metadata block included
- [ ] **Required fields:** script_type, dj_name, timestamp, model, word_count
- [ ] **Separator line:** 80 equals signs between script and metadata
- [ ] **Valid JSON:** Metadata parses without errors
- [ ] **Encoding:** UTF-8 text file (no corruption)

---

## Post-Generation Validation

### Automated Validation (Required)
- [ ] Run validation suite: `python tools/script-generator/tests/validate_scripts.py [script_file]`
- [ ] **Overall score ≥70/100** (passing threshold)
- [ ] **Character consistency ≥60/100** (voice must be recognizable)
- [ ] **Lore accuracy ≥70/100** (no major temporal/geographic violations)
- [ ] **Quality metrics ≥70/100** (structure and flow acceptable)
- [ ] **Format compliance ≥50/100** (metadata present - lower acceptable due to legacy markers)

**Score Interpretation:**
- **85-100:** Excellent - ready for production
- **70-84:** Good - acceptable with minor notes
- **60-69:** Marginal - review manually, may need regeneration
- **<60:** Failing - regenerate with adjusted parameters

### Manual Spot-Check (Recommended for important scripts)
- [ ] **Read aloud test:** Script sounds natural when spoken
- [ ] **ChromaDB cross-reference:** Spot-check 2-3 lore claims against RAG source
  - Open ChromaDB query tool
  - Search for mentioned locations/factions/events
  - Verify accuracy and temporal consistency
- [ ] **Peer review:** Have another person read script (if available)
- [ ] **Character comparison:** Compare to canonical DJ dialogue from game
  - Julie: Listen to Fallout 76 radio samples
  - Mr. New Vegas: Listen to Fallout NV radio
  - Travis: Listen to FO4 DCR before/after Confidence Man quest

### Approval Decision
- [ ] **APPROVED:** Move to `script generation/approved/` folder
- [ ] **APPROVED WITH NOTES:** Document minor issues for future reference
- [ ] **REVISION NEEDED:** Note specific issues, regenerate or manually edit
- [ ] **REJECTED:** Discard, try different generation parameters

**Document Decision:** Add entry to generation log or quality tracking database

---

## Batch Generation Checklist (10+ Scripts)

### Before Batch
- [ ] **Diversity planned:** 5 script types × 3+ variants each minimum
- [ ] **Theme cohesion:** Batch fits together (e.g., "Morning Show", "Full Day", "Special Event")
- [ ] **Temporal/thematic distribution:** Mix of times (morning/evening), moods (serious/lighthearted)
- [ ] **VRAM monitoring:** Track GPU usage, plan for model unload between phases

### During Batch
- [ ] **Incremental review:** Spot-check every 5th script during generation
- [ ] **Error tracking:** Log any generation failures, retry with adjusted params
- [ ] **Template variety:** Rotate through different template variables to avoid repetition
- [ ] **Progress tracking:** Update checklist showing X of Y completed

### After Batch
- [ ] **Batch validation:** Run validator on entire output directory
- [ ] **Representative sample review:** Manually review 20% of batch (random selection)
- [ ] **Statistical analysis:** Check average scores, identify outliers
- [ ] **Quality trending:** Compare batch metrics to previous batches
- [ ] **Unload model:** `generator.unload_model()` to free VRAM for next phase
- [ ] **Archive batch:** Move to dated subfolder with quality report
- [ ] **Update metrics:** Log batch statistics for historical tracking

---

## Common Issues & Solutions

### Issue: Low Character Consistency Score (<60)

**Symptoms:**
- Missing catchphrases
- Doesn't sound like DJ
- Uses forbidden phrases

**Solutions:**
1. Add catchphrase to template opening/closing
2. Increase `temperature` parameter (0.8 → 0.9) for more personality
3. Review DJ personality card - ensure examples are clear
4. Manually inject catchphrase during post-processing

### Issue: Lore Accuracy Failures (Anachronisms)

**Symptoms:**
- References to factions/events after DJ's time
- Wrong locations for DJ's region
- Real-world references

**Solutions:**
1. Add temporal filter to RAG query: `f"before {dj_year}"`
2. Regenerate with stricter context_query (emphasize DJ's location/era)
3. Review ChromaDB - ensure metadata filters are applied
4. Add explicit constraint to template: "Do not reference events after 2102"

### Issue: Word Count Severely Over/Under

**Symptoms:**
- Scripts 2x target length or <50% target
- Rambling or incomplete thoughts

**Solutions:**
- **Too long:** Reduce `num_predict` parameter (300 → 200)
- **Too short:** Increase `num_predict` (300 → 400)
- **Alternative:** Adjust `temperature` (lower = more focused/concise)
- **Last resort:** Accept current length or manually edit

### Issue: Repetitive Content

**Symptoms:**
- Same phrases repeated multiple times
- Batch of scripts all sound similar
- Overuse of specific words

**Solutions:**
1. Increase `top_p` parameter (0.9 → 0.95) for more variety
2. Vary `context_query` between scripts
3. Add "diversity" instruction to template prompt
4. Use different template variables for each variant

### Issue: Validator Crashes/Errors

**Symptoms:**
- JSON decode errors
- Missing personality errors
- Attribute access errors

**Solutions:**
1. Check file encoding (must be UTF-8)
2. Verify JSON metadata is valid (use online JSON validator)
3. Ensure DJ personality file exists in `dj personality/` folder
4. Check validator version matches generator version

---

## Quality Metrics Tracking Template

Use this template to track quality over time:

```
Batch: [Name/Date]
DJ: [Character Name]
Script Count: [X scripts]
Generation Time: [X minutes]
Model: [Ollama model name]

Average Scores:
- Overall: XX.X/100
- Character Consistency: XX.X/100
- Lore Accuracy: XX.X/100
- Quality Metrics: XX.X/100
- Format Compliance: XX.X/100

Pass Rate: XX% (X/Y scripts ≥70)

Issues Found:
- Critical: X
- Warnings: X

Top Issues:
1. [Issue description] - X occurrences
2. [Issue description] - X occurrences
3. [Issue description] - X occurrences

Improvements from Last Batch:
- [Metric]: +X.X points
- [Issue]: Reduced by X%

Next Batch Goals:
- [ ] [Improvement target]
- [ ] [Quality focus area]
```

---

## Approval Stamp (Use for Final Review)

**Script:** `[filename]`  
**DJ:** `[character]`  
**Type:** `[weather/news/etc.]`  
**Generated:** `[date]`  
**Validated:** `[date]`  

**Scores:**
- Overall: `____ / 100`
- Character: `____ / 100`
- Lore: `____ / 100`
- Quality: `____ / 100`

**Status:** [ ] APPROVED  [ ] REVISION NEEDED  [ ] REJECTED

**Reviewer:** `[Name]`  
**Notes:** `[Any comments, changes needed, or approval conditions]`

---

**Checklist Version:** 1.0  
**Last Updated:** 2026-01-12  
**Maintained by:** ESP32 AI Radio Project Team  
**Next Review:** After Phase 3 implementation
