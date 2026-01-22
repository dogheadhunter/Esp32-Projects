# Should Answer Questions - Comprehensive Recommendations

**Created**: January 21, 2026  
**Context**: Based on current MVP implementation progress and 30-day autonomous generation strategy  
**Purpose**: Provide 4 options for each partially answered "should answer" question with pros, cons, complexity, and rationale

---

## Q16: DJ Knowledge Granularity

**Current State**: Chunk-level metadata filtering (year_max, region, era)  
**Gap**: Fact-level granularity, knowledge graph integration, "common knowledge" handling

### Option 1: Enhance Metadata with Knowledge Tiers

**Approach**: Add `knowledge_tier` field to ChromaDB metadata (common, regional, restricted, classified)

**Why**: Different facts have different accessibility - some knowledge spreads (common), others are location-specific (regional), others are faction-secret (restricted).

**Pros**:
- Simple metadata addition, no schema overhaul
- Integrates with existing DJ_QUERY_FILTERS
- Clear categorization for human curators
- Can be applied retroactively to existing chunks

**Cons**:
- Requires manual curation of knowledge tiers
- Binary tier system may miss nuanced cases
- "Common knowledge" still needs definition (what spreads vs. stays local)

**Complexity**: **Low** (2-3 days)
- Add `knowledge_tier` to metadata enrichment
- Update DJ filters to include tier constraints
- Create curation script for existing data

---

### Option 2: Implement Knowledge Graph with Relationship Tracking

**Approach**: Build knowledge graph tracking fact dependencies (X knows Y because Z)

**Why**: Knowledge spreads through networks - if traders travel between Vault 76 and Foundation, news travels. Need to model information flow.

**Pros**:
- Most accurate representation of information spread
- Can simulate realistic rumor propagation
- Enables temporal knowledge (DJ learns over time)
- Supports "how did they learn this?" validation

**Cons**:
- High complexity - requires graph database or Neo4j integration
- Difficult to populate initially (no existing data)
- Adds significant overhead to every query
- May be overkill for 30-day MVP

**Complexity**: **Very High** (3-4 weeks)
- Design knowledge graph schema
- Populate graph from lore sources
- Integrate with ChromaDB queries
- Create propagation simulation

---

### Option 3: Context-Aware "Common Knowledge" Classifier

**Approach**: LLM-based classifier determines if fact is "common knowledge" vs. "secret" based on context

**Why**: Some facts naturally spread (Scorchbeast attacks), others don't (secret Enclave bunker). Use AI to make judgment call.

**Pros**:
- Automated classification, minimal manual work
- Handles edge cases better than rigid tiers
- Can evolve with LLM improvements
- Works with existing ChromaDB data

**Cons**:
- Non-deterministic - same fact may classify differently
- Adds LLM call overhead to extraction pipeline
- Needs validation dataset to tune prompts
- May hallucinate classifications

**Complexity**: **Medium** (1 week)
- Create classification prompt template
- Build validation dataset (50-100 examples)
- Integrate into story extraction pipeline
- Add caching for repeated classifications

---

### Option 4: Hybrid: Tiers + Exceptions List

**Approach**: Use knowledge tiers (Option 1) with manual exception list for edge cases

**Why**: 90% of cases fit clean tiers, 10% need special handling. Best of both worlds.

**Pros**:
- Pragmatic balance of automation and control
- Easy to implement and maintain
- Exceptions list documents special cases clearly
- Can migrate to Option 2/3 later if needed

**Cons**:
- Still requires some manual curation
- Exception list may grow large over time
- Doesn't model knowledge spread dynamics

**Complexity**: **Low-Medium** (3-5 days)
- Implement tier system (Option 1)
- Add exceptions.json for special cases
- Create curation workflow documentation
- Build audit tool to find uncategorized facts

**RECOMMENDATION**: **Option 4** for MVP, consider Option 3 post-launch for automation

---

## Q17: Knowledge Contradictions

**Current State**: Era filtering + manual quest blacklist covers 95% of cases  
**Gap**: Same-era contradictions, automatic detection

### Option 1: Contradiction Detection via Semantic Similarity

**Approach**: Use embeddings to detect when new content contradicts existing content

**Why**: Contradictions often manifest as semantically opposite statements about same entities.

**Pros**:
- Automated detection, no manual lists
- Works across all content types
- Can catch subtle contradictions
- Scales with content growth

**Cons**:
- False positives (different perspectives ≠ contradictions)
- Requires establishing "source of truth" hierarchy
- Computationally expensive (embedding all content)
- May miss logical contradictions that aren't semantic opposites

**Complexity**: **Medium** (1 week)
- Generate embeddings for all ChromaDB chunks
- Implement contradiction scoring algorithm
- Define contradiction threshold
- Create review UI for flagged contradictions

---

### Option 2: Entity State Tracking with Canonical Timeline

**Approach**: Track canonical state of entities (characters, factions, locations) over time

**Why**: Most contradictions involve entity states - "X is alive" vs "X died in 2102". Need single source of truth.

**Pros**:
- Prevents temporal logic errors
- Creates audit trail for entity changes
- Enables "as of date X" queries
- Foundation for future knowledge graph

**Cons**:
- Requires populating entity timeline database
- Needs consensus on canonical lore sources
- High initial setup cost
- Ongoing maintenance as lore evolves

**Complexity**: **High** (2-3 weeks)
- Design entity state schema
- Extract entity timelines from wiki/lore
- Implement state validation during extraction
- Create entity timeline visualization tool

---

### Option 3: LLM-Based Contradiction Validator

**Approach**: Before accepting new story, LLM checks if it contradicts existing active stories

**Why**: Leverage LLM's reasoning to catch contradictions humans might miss.

**Pros**:
- No manual database population
- Can explain WHY something contradicts
- Works immediately with existing content
- Catches nuanced logical contradictions

**Cons**:
- LLM may hallucinate contradictions
- Adds latency to story extraction
- Non-deterministic results
- Requires validation prompt engineering

**Complexity**: **Medium** (1 week)
- Design contradiction detection prompt
- Integrate into story extraction pipeline
- Build test suite with known contradictions
- Add override mechanism for false positives

---

### Option 4: Expand Quest Blacklist with Automated Suggestions

**Approach**: Enhance manual blacklist with LLM suggesting potential contradictions for human review

**Why**: Manual curation works but doesn't scale. Hybrid approach: AI suggests, human approves.

**Pros**:
- Leverages existing blacklist system
- Human-in-the-loop prevents false positives
- Builds institutional knowledge in blacklist
- Low risk - suggestions can be ignored

**Cons**:
- Still requires manual review time
- Blacklist may grow unwieldy (100+ entries)
- Reactive rather than proactive
- Doesn't prevent contradictions, just documents them

**Complexity**: **Low** (2-3 days)
- Create contradiction suggestion script
- Add structured comments to blacklist format
- Implement suggestion review workflow
- Schedule weekly blacklist review

**RECOMMENDATION**: **Option 4** for MVP (low risk), **Option 2** for long-term quality

---

## Q20: LLM Crash/Quota Handling

**Current State**: Retry with backoff, auto-pause on 5 failures, resume from checkpoint  
**Gap**: Fallback LLM provider, aggressive caching

### Option 1: Multi-Provider Fallback Chain

**Approach**: Primary: Ollama → Fallback 1: Cloud API (OpenRouter) → Fallback 2: Cached responses

**Why**: Single point of failure risk. If Ollama crashes, entire 80-hour generation halts.

**Pros**:
- High reliability - multiple failure modes needed to stop
- Cloud APIs have better uptime than local
- Automatic recovery without human intervention
- Can use cheaper cloud API only as backup

**Cons**:
- Cloud costs for fallback usage
- API keys management complexity
- Prompt tuning needed per provider
- Potential quality differences between providers

**Complexity**: **Medium** (1 week)
- Create provider abstraction layer
- Implement fallback chain logic
- Add provider health checks
- Test failure scenarios

---

### Option 2: Aggressive Response Caching with Cache Warming

**Approach**: Pre-generate and cache common segment types before 30-day run

**Why**: If 60% of segments are time checks/weather/gossip, pre-cache those variations to reduce LLM dependency.

**Pros**:
- Reduces LLM calls by 40-60%
- Faster generation (cache hits < 10ms)
- No external dependencies
- Deterministic fallback for critical segments

**Cons**:
- Cache may feel repetitive
- Doesn't help with unique story segments
- Cache warming takes time (2-3 hours pre-run)
- Cache invalidation complexity

**Complexity**: **Medium** (1 week)
- Design cache key structure (DJ + segment type + context)
- Generate cache warming dataset
- Implement cache-first generation strategy
- Add variety scoring to prevent repetition

---

### Option 3: Ollama Container Orchestration with Auto-Restart

**Approach**: Run Ollama in Docker/Kubernetes with health checks and automatic restart

**Why**: Most Ollama crashes are recoverable - auto-restart prevents manual intervention.

**Pros**:
- Transparent to generation code
- Industry-standard container tooling
- Health checks detect hangs, not just crashes
- Can add resource limits (memory, CPU)

**Cons**:
- Requires Docker/K8s infrastructure
- Container startup time (30-60 seconds)
- Model reload time on restart (1-2 minutes)
- Doesn't help if model itself is corrupted

**Complexity**: **Low-Medium** (3-5 days)
- Create Dockerfile for Ollama + models
- Implement health check endpoint
- Configure restart policy
- Test restart scenarios

---

### Option 4: Checkpoint Every Segment + Quick Resume

**Approach**: Save lightweight checkpoint after EVERY segment, enabling instant resume

**Why**: Current 1-hour checkpoints mean losing up to 2 segments on crash. Per-segment checkpoints minimize loss.

**Pros**:
- Minimal data loss (1 segment max)
- Fast resume (<1 second state reload)
- No external dependencies
- Works with existing checkpoint system

**Cons**:
- Disk I/O overhead (2 segments/minute = 120 writes/hour)
- Checkpoint files proliferate (960 files for 30-day run)
- Need aggressive cleanup strategy
- Doesn't prevent crashes, just minimizes impact

**Complexity**: **Low** (2-3 days)
- Implement lightweight checkpoint format (JSON, ~5KB)
- Add per-segment save logic
- Implement rolling cleanup (keep last 10 only)
- Test I/O performance impact

**RECOMMENDATION**: **Option 3** (most reliable) + **Option 4** (belt and suspenders)

---

## Q22: Metrics to Track

**Current State**: LIVE_STATUS.json with core metrics (progress, ETA, pass rate, cache hit)  
**Gap**: Detailed per-segment timing, token usage, story beat distribution graphs

### Option 1: Comprehensive Telemetry System with Time-Series DB

**Approach**: Log all metrics to InfluxDB/Prometheus with Grafana dashboards

**Why**: Industry-standard observability stack enables deep analysis and alerting.

**Pros**:
- Rich visualization (graphs, heatmaps, histograms)
- Historical trending and analysis
- Alerting on anomalies (e.g., slow generation)
- Can correlate metrics (slow segments = low cache hit?)

**Cons**:
- Infrastructure overhead (3 additional services)
- Overkill for 30-day one-off run
- Learning curve for setup and querying
- Data retention costs

**Complexity**: **High** (1-2 weeks)
- Set up InfluxDB + Grafana
- Instrument code with metrics collection
- Design dashboard layouts
- Configure alerts

---

### Option 2: Enhanced JSON Logging with Analysis Scripts

**Approach**: Log detailed metrics to structured JSON, analyze with Python scripts post-run

**Why**: Simple, no infrastructure, enables rich analysis without runtime overhead.

**Pros**:
- No external dependencies
- Easy to parse and analyze
- Can re-analyze historical runs
- Minimal runtime performance impact

**Cons**:
- No real-time visualization
- Manual analysis required
- Large log files (100MB+ for 30 days)
- Can't alert on issues during run

**Complexity**: **Low** (2-3 days)
- Design JSON log schema
- Add logging to key code paths
- Create analysis scripts (timing, token usage, etc.)
- Generate summary reports

---

### Option 3: SQLite Metrics Database with Jupyter Notebooks

**Approach**: Log metrics to SQLite, analyze interactively with Jupyter notebooks

**Why**: Best of both worlds - structured storage + interactive analysis without heavy infrastructure.

**Pros**:
- SQL queries for flexible analysis
- Jupyter enables visual exploration
- Single-file database (easy to backup/share)
- Can run queries during live generation

**Cons**:
- SQLite write contention on high load
- No built-in alerting
- Jupyter setup required
- Manual dashboard creation

**Complexity**: **Medium** (3-5 days)
- Design metrics schema (segments, timing, validation, cache)
- Implement metrics logger with SQLite
- Create notebook templates for common analyses
- Add real-time monitoring notebook

---

### Option 4: Minimal Metrics with Focus on Actionable KPIs

**Approach**: Track only metrics that trigger actions (error rate, generation time, cache hit)

**Why**: Avoid analysis paralysis - focus on metrics that inform decisions, not just data collection.

**Pros**:
- Low overhead, simple implementation
- Clear signal-to-noise ratio
- Easy to understand and act on
- Works well with LIVE_STATUS.json

**Cons**:
- May miss insights from untracked metrics
- Can't do deep post-run analysis
- Limited historical comparison
- Hard to add metrics retroactively

**Complexity**: **Very Low** (1 day)
- Enhance LIVE_STATUS.json with 5-10 key metrics
- Add CSV export for historical tracking
- Create simple trend analysis script
- Define metric thresholds for alerts

**RECOMMENDATION**: **Option 2** for MVP (simple + flexible), **Option 3** for future runs (interactive analysis)

---

## Q23: "On Track" Indicators

**Current State**: Progress %, ETA, pass rate monitoring, terminal warnings  
**Gap**: Quality KPI trending, story milestone tracking

### Option 1: Traffic Light System with Predictive Alerts

**Approach**: Classify run health as GREEN/YELLOW/RED based on trending metrics

**Why**: Simple visual indicator enables quick assessment - "Is this run healthy or degrading?"

**Pros**:
- Intuitive at-a-glance status
- Predictive alerts (trending toward RED)
- Clear intervention triggers
- Works well in terminal UI

**Cons**:
- Requires defining thresholds (what's YELLOW vs RED?)
- May oversimplify complex issues
- False positives cause alert fatigue
- Doesn't explain WHY status changed

**Complexity**: **Low-Medium** (3-5 days)
- Define health criteria per metric
- Implement trending analysis (sliding window)
- Add color-coded terminal output
- Create alert notification system

---

### Option 2: Story Milestone Tracking with Completion Forecasting

**Approach**: Track story progression (acts completed, beats broadcast) and forecast completion dates

**Why**: Stories are most complex part of system - tracking their health indicates overall system health.

**Pros**:
- Direct measure of content quality
- Identifies stuck/abandoned stories
- Forecasts when stories will complete
- Enables story pacing adjustments

**Cons**:
- Only tracks story segments (~30% of content)
- Complex calculation (multiple timeline stories)
- May not reflect overall health
- Requires story system maturity

**Complexity**: **Medium** (1 week)
- Enhance story_state tracking
- Calculate story completion velocity
- Forecast milestone dates
- Add story health to LIVE_STATUS

---

### Option 3: Quality Score Trending with Regression Detection

**Approach**: Track quality metrics over time, detect statistically significant degradation

**Why**: Quality can degrade subtly - need automated detection before human notice.

**Pros**:
- Data-driven degradation detection
- Catches subtle issues early
- Statistical rigor (not just thresholds)
- Can identify root causes (which metric degraded)

**Cons**:
- Requires baseline period (first 50-100 segments)
- False positives from natural variance
- Complex statistical analysis
- May not detect catastrophic failures quickly

**Complexity**: **Medium-High** (1-2 weeks)
- Implement moving average tracking
- Add statistical significance testing
- Create degradation alert system
- Build trend visualization

---

### Option 4: Hourly Health Reports with Anomaly Flagging

**Approach**: Generate hourly summary reports comparing current hour to historical average

**Why**: Regular checkpoints enable intervention before issues compound.

**Pros**:
- Regular monitoring rhythm
- Human-readable reports
- Can review during run or post-mortem
- Anomaly detection without ML complexity

**Cons**:
- Requires reviewing reports (manual)
- Hourly may be too frequent or too slow
- Anomaly definition is subjective
- Report fatigue if too verbose

**Complexity**: **Low** (2-3 days)
- Create hourly report template
- Implement anomaly detection (Z-score)
- Add report generation to checkpoint cycle
- Design email/Slack notification option

**RECOMMENDATION**: **Option 1** (immediate feedback) + **Option 4** (detailed records)

---

## Q34: Tolerance for Imperfection

**Current State**: Tiered thresholds (0% lore violations, <5% quality issues)  
**Gap**: Specific trade-off philosophy, "good enough" criteria

### Option 1: Accept-Refine-Perfect Framework

**Approach**: 3-tier acceptance criteria with post-processing refinement

**Why**: Perfect is enemy of good. Generate acceptable content, refine standouts, perfect featured stories.

**Tiers**:
- **Accept**: Meets minimum standards, use as-is (80% of content)
- **Refine**: Good but improvable, run refinement pass (15% of content)
- **Perfect**: Featured content, manual review (5% of content)

**Pros**:
- Realistic expectations for autonomous generation
- Focuses effort where it matters (featured stories)
- Enables completion over perfection
- Clear criteria for each tier

**Cons**:
- May ship mediocre content
- Refinement pass adds complexity
- "Accept" threshold may be too low
- Requires disciplined restraint

**Complexity**: **Medium** (1 week)
- Define tier criteria for each segment type
- Implement refinement pipeline for tier 2
- Add manual review queue for tier 3
- Track tier distribution

---

### Option 2: Progressive Quality Ratcheting

**Approach**: Start with loose tolerances, tighten over time as system learns

**Why**: Early segments help calibrate expectations. As cache builds and prompts improve, raise the bar.

**Schedule**:
- Hours 1-8: 90% pass rate acceptable (learning phase)
- Hours 9-24: 95% pass rate required (stabilized)
- Hours 25+: 98% pass rate expected (optimized)

**Pros**:
- Realistic for system warm-up period
- Allows learning without blocking
- Gradual improvement trajectory
- Data-driven threshold adjustments

**Cons**:
- Early content may be lower quality
- Complex logic (changing thresholds)
- May mask systemic issues
- Requires careful threshold calibration

**Complexity**: **Low-Medium** (3-5 days)
- Implement time-based threshold logic
- Add threshold tracking to metrics
- Create threshold adjustment mechanism
- Document rationale for each phase

---

### Option 3: Critical vs. Cosmetic Separation

**Approach**: Zero tolerance for critical errors, flexible on cosmetic issues

**Why**: Distinguish between breaking immersion (critical) and minor polish (cosmetic).

**Critical** (0% tolerance):
- Lore violations (wrong year, wrong faction)
- Character voice breaks (Julie sounds like Mr. New Vegas)
- Temporal impossibilities (references future events)

**Cosmetic** (10% tolerance):
- Minor grammar issues
- Repetitive phrasing
- Suboptimal word choice
- Length slightly off target

**Pros**:
- Clear prioritization
- Prevents blocking on perfection
- Maintains core quality standards
- Easy to explain and enforce

**Cons**:
- Requires categorizing every validation rule
- "Cosmetic" issues may compound
- Subjective boundary cases
- May accumulate technical debt

**Complexity**: **Low** (2-3 days)
- Categorize existing validation rules
- Implement separate threshold tracking
- Update quality gates with categories
- Document classification rationale

---

### Option 4: Human Review Sampling with Confidence Intervals

**Approach**: Sample random segments for human review, calculate confidence in overall quality

**Why**: Can't review all 9,600 segments, but statistical sampling gives confidence bounds.

**Method**:
- Review random sample (50-100 segments)
- Calculate quality metrics
- Estimate overall quality with 95% confidence interval
- If lower bound < threshold, investigate

**Pros**:
- Statistical rigor
- Manageable human review time
- Catches issues automation misses
- Provides defendable quality metrics

**Cons**:
- Requires human reviewers (time cost)
- Sample size calculation complexity
- May miss rare but critical issues
- Delayed feedback (post-run)

**Complexity**: **Medium** (1 week)
- Design sampling strategy (stratified by segment type)
- Create review interface/rubric
- Implement statistical analysis
- Generate confidence interval reports

**RECOMMENDATION**: **Option 3** for runtime (clear boundaries), **Option 4** for validation (statistical confidence)

---

## Q39: Subtle Degradation Detection

**Current State**: Manual LIVE_STATUS monitoring, performance trending in warnings  
**Gap**: Automatic degradation alerts, quality score trending

### Option 1: Statistical Process Control (SPC) Charts

**Approach**: Apply manufacturing quality techniques - control charts with upper/lower limits

**Why**: Proven industrial method for detecting process degradation before it becomes critical.

**Metrics**:
- Generation time per segment (detect slowdowns)
- Validation pass rate (detect quality decline)
- Cache hit rate (detect cache degradation)
- Token usage (detect prompt drift)

**Pros**:
- Well-established methodology
- Clear statistical thresholds (3-sigma limits)
- Distinguishes common vs. special cause variation
- Visual charts enable pattern recognition

**Cons**:
- Requires stable baseline period
- May not catch slow drift
- Complex for non-statisticians
- Multiple charts to monitor

**Complexity**: **Medium** (1 week)
- Implement SPC calculation (moving average, std dev)
- Generate control charts
- Define alert triggers (points outside limits)
- Create chart visualization

---

### Option 2: Anomaly Detection with Machine Learning

**Approach**: Train anomaly detection model on "healthy" metrics, flag deviations

**Why**: ML can detect complex patterns humans might miss (e.g., correlated metric changes).

**Pros**:
- Detects complex multi-metric anomalies
- No manual threshold setting
- Adapts to baseline drift
- Can catch novel failure modes

**Cons**:
- Requires training period (first day)
- Black box - hard to explain alerts
- May have false positives
- Overkill for simple metrics

**Complexity**: **High** (2-3 weeks)
- Collect training data from pilot runs
- Select anomaly detection algorithm (Isolation Forest, LSTM)
- Train and tune model
- Integrate into monitoring pipeline

---

### Option 3: Sliding Window Comparison with Alerting

**Approach**: Compare current N segments to previous N segments, alert on significant changes

**Why**: Simple, interpretable, catches both sudden and gradual degradation.

**Method**:
- Window size: 10-20 segments
- Metrics: avg generation time, pass rate, cache hit rate
- Alert if current window deviates >10% from previous window

**Pros**:
- Simple to implement and understand
- Catches gradual degradation
- No training period needed
- Low false positive rate

**Cons**:
- Lag time (need full window to detect)
- May miss sudden spikes
- Window size is arbitrary
- Doesn't explain root cause

**Complexity**: **Low** (2-3 days)
- Implement sliding window tracking
- Calculate window statistics
- Define alerting thresholds
- Add alerts to LIVE_STATUS

---

### Option 4: Canary Segment Testing

**Approach**: Periodically generate "canary" segments with known inputs, check quality

**Why**: Like canary in coal mine - if canary segments fail, production segments at risk.

**Method**:
- Every 50 segments, generate canary from fixed test case
- Compare quality to baseline canary
- If degraded, trigger investigation

**Pros**:
- Deterministic test case
- Isolates system degradation from content variance
- Clear pass/fail criteria
- Easy to debug (same input every time)

**Cons**:
- Adds overhead (extra generation)
- Canary may not represent real content
- Only detects issues if canary triggers them
- Delays detection (only every 50 segments)

**Complexity**: **Low-Medium** (3-5 days)
- Create canary test cases (5-10 per segment type)
- Implement canary generation logic
- Define baseline quality metrics
- Add canary tracking to monitoring

**RECOMMENDATION**: **Option 3** (simple + effective) with **Option 4** (validation)

---

## Q40: Rollback Strategy

**Current State**: Checkpoint restore documented, state file backups  
**Gap**: Segment-level versioning, continuity repair after rollback

### Option 1: Git-Style Segment Versioning

**Approach**: Store every segment version, enable rollback to any point in history

**Why**: Like git for code, enable precise rollback without losing work.

**Pros**:
- Granular rollback (single segment)
- Full history for debugging
- Can cherry-pick good segments
- Enables A/B comparison

**Cons**:
- Storage overhead (10x disk usage)
- Complex diff/merge logic
- Overkill for most use cases
- Slower writes (versioning overhead)

**Complexity**: **High** (2-3 weeks)
- Design versioning schema
- Implement content-addressed storage
- Create rollback CLI tool
- Build segment diff viewer

---

### Option 2: Checkpoint Branching with Continuity Repair

**Approach**: Support multiple checkpoint branches, auto-repair continuity after rollback

**Why**: Rolling back to Hour 12 creates discontinuity - Hour 13 references Hour 12 events that no longer exist.

**Method**:
- Mark checkpoint as branch point
- On rollback, detect broken references
- Either regenerate dependent segments or inject continuity bridges

**Pros**:
- Solves continuity problem
- Maintains story coherence
- Enables "what if" exploration
- Future-proof for multi-timeline stories

**Cons**:
- Complex dependency tracking
- Regeneration cascade may be large
- Continuity repair may fail
- High development complexity

**Complexity**: **Very High** (3-4 weeks)
- Build dependency graph for segments
- Implement reference detection
- Create continuity repair engine
- Test various rollback scenarios

---

### Option 3: Immutable Logs with Compensating Transactions

**Approach**: Never delete segments, only append "corrections" or "retractions"

**Why**: Like accounting - mistakes are corrected by adding offsetting entries, not deleting.

**Example**:
- Hour 12: "Raiders attack Vault 76"
- Hour 13: "Vault 76 defenders repel attack" (depends on Hour 12)
- Rollback Hour 12 → Insert "Raiders retreat before reaching Vault 76" (compensating transaction)
- Hour 13 context updated to reflect new reality

**Pros**:
- Full audit trail
- No data loss
- Enables forensics/analysis
- Theoretically sound approach

**Cons**:
- Extremely complex to implement
- Requires deep story understanding
- May create weird discontinuities
- Over-engineered for use case

**Complexity**: **Very High** (4+ weeks)
- Design compensating transaction logic
- Implement story dependency analyzer
- Create correction segment generator
- Build verification system

---

### Option 4: Simple Rollback with Manual Continuity Check

**Approach**: Rollback to checkpoint, mark subsequent segments as "may have continuity issues", human review

**Why**: Rollback is rare (emergency only). Manual fix is acceptable for rare events.

**Method**:
- Rollback to checkpoint
- Flag next 5-10 segments for review
- Human checks for broken references
- Either accept or regenerate flagged segments

**Pros**:
- Simple implementation
- Human judgment for edge cases
- Low risk of automation errors
- Adequate for emergency use

**Cons**:
- Requires human intervention
- May miss subtle issues
- Not fully autonomous
- Review time delays recovery

**Complexity**: **Low** (1-2 days)
- Add rollback CLI command
- Implement segment flagging
- Create review checklist
- Document rollback procedure

**RECOMMENDATION**: **Option 4** for MVP (pragmatic), **Option 2** if rollbacks become common

---

## Summary: Recommended Implementation Priority

### Immediate (Before 30-Day Run)
1. **Q20**: Option 3 (Ollama orchestration) + Option 4 (per-segment checkpoints)
2. **Q34**: Option 3 (Critical vs. Cosmetic separation)
3. **Q16**: Option 4 (Tiers + Exceptions hybrid)

### Week 1 Post-Launch
4. **Q23**: Option 1 (Traffic light) + Option 4 (Hourly reports)
5. **Q39**: Option 3 (Sliding window) + Option 4 (Canary testing)
6. **Q22**: Option 2 (Enhanced JSON logging)

### Future Iterations
7. **Q17**: Option 2 (Entity state tracking)
8. **Q40**: Option 4 (Manual rollback, upgrade if needed)

### Research/Defer
9. **Q16**: Option 3 (LLM classifier - research project)
10. **Q17**: Option 1 (Semantic contradiction detection)

---

## Key Principles Across All Recommendations

1. **Start Simple**: MVP-first approach, enhance based on real data
2. **Human-in-Loop**: Automation with human oversight for edge cases
3. **Measure First**: Can't optimize what you don't measure
4. **Fail Safe**: Graceful degradation over hard failures
5. **Document Rationale**: Every decision should answer "why this way?"

This approach balances pragmatism (ship the 30-day run) with quality (ensure it's good enough) while avoiding over-engineering (don't build what you don't need yet).
