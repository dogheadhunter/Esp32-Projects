# Full Weather Simulation System - Implementation Plan

**Created:** January 17, 2026  
**Status:** Planning Complete - Ready for Implementation  
**Scope:** Year-long regional weather simulation with historical archives and emergency broadcasts

---

## Overview

Implement a comprehensive year-long weather simulation with separate region-specific calendars, historical weather archives for lore continuity, emergency broadcast interruptions, and manual override for debugging. System pre-generates 365-day weather calendars per DJ region (Appalachia, Mojave, Commonwealth) with post-apocalyptic modifications, persistent historical logging, and archive search tools.

---

## Implementation Steps

### 1. Design Regional Climate Profiles & Post-Apocalyptic Weather Logic

**File:** [tools/script-generator/regional_climate.py](../tools/script-generator/regional_climate.py)

- [ ] Create `RegionalClimate` dataclass (region_name, base_temps, seasonal_patterns, precipitation_freq, special_conditions)
- [ ] Implement climate profiles:
  - **Appalachia** (humid subtropical, four seasons, temp range 20-85°F, frequent fog/rain, mountain snow)
  - **Mojave** (desert, extreme temps 35-115°F, rare rain <5%, intense rad storms)
  - **Commonwealth** (humid continental, cold winters, temp range 10-80°F, moderate precipitation, nor'easters)
- [ ] Add post-apocalyptic modifiers for each region:
  - Appalachia: +25% rad storms from Scorchbeast activity, persistent Scorched Plague clouds
  - Mojave: +15% dust storms, extreme temp swings from lack of moisture regulation
  - Commonwealth: nuclear winter remnants, +10% snow year-round, glowing sea radiation drift
- [ ] Build `get_region_from_dj_name()` parsing DJ location:
  - Julie → Appalachia 2102
  - Mr. New Vegas → Mojave 2281
  - Travis Miles → Commonwealth 2287
- [ ] Create temperature calculation with regional base + seasonal offset + post-apocalyptic variance (+/-20°F random spikes from radioactive weather cells)

**Success Criteria:**
- Each region has distinct weather personality
- Appalachia gets more fog/rain than Mojave
- Post-apocalyptic twists feel authentic
- Region detection correctly maps all 5 DJs

---

### 2. Design Weather State Machine & Transition Logic

**File:** [tools/script-generator/weather_simulator.py](../tools/script-generator/weather_simulator.py)

- [ ] Create `WeatherState` dataclass (weather_type, started_at, duration_hours, intensity, transition_state, is_emergency, temperature, region)
- [ ] Implement `RegionalWeatherTransitionMatrix` with region-specific probabilities:
  - Appalachia: cloudy→rainy 40%
  - Mojave: sunny→sunny 70%
  - Commonwealth: cloudy→snow 25% in winter
- [ ] Build `WeatherPattern` class modeling multi-day regional fronts:
  - Appalachia: 1.5-3 day rain systems from mountain moisture
  - Mojave: 5-10 day sunny stretches
  - Commonwealth: 2-4 day snow systems
- [ ] Add weather duration logic varying by region:
  - Appalachia fog: 4-8 hours
  - Mojave sun: 8-16 hours
  - Commonwealth snow: 6-12 hours
- [ ] Add post-apocalyptic emergency conditions:
  - rad_storm (radioactive fallout cells)
  - dust_storm (Mojave only)
  - ash_fall (volcanic-like from distant detonations)
  - glowing_fog (Commonwealth only)
- [ ] Set emergency flag for rad_storm, dust_storm (Mojave only), glowing_fog (Commonwealth only) triggering broadcast interruption

**Success Criteria:**
- Regional transitions tested with 1000 iterations per region showing realistic patterns
- Mojave rarely gets rain
- Appalachia fog frequent
- Emergencies properly flagged with regional variation

---

### 3. Extend WorldState Schema for Multi-Region Weather Persistence

**File:** [tools/script-generator/world_state.py](../tools/script-generator/world_state.py#L38-L48)

- [ ] Add `weather_calendars` dict storing separate calendars per region (key=region_name, value=yearly_calendar_data)
- [ ] Add `current_weather_by_region`, `weather_history_archive`, `calendar_metadata`, `manual_overrides` fields for multi-region tracking
- [ ] Update `save()` and `load()` methods ([lines 179-220](../tools/script-generator/world_state.py#L179-L220)) to persist multiple regional calendars
  - 3 regions × 365 days × 4 slots = ~4380 entries total
  - Expected file size: ~800KB-1.2MB
- [ ] Add helper methods:
  - `get_current_weather(region)`
  - `update_weather_state(region)`
  - `get_weather_history(region, start_date, end_date)`
  - `set_manual_weather_override(region)`
  - `clear_manual_override(region)`
  - `get_calendar_for_region(region)`
- [ ] Implement calendar validation on load checking each region's calendar exists and has valid date range
- [ ] Implement migration logic for existing broadcast_state.json files (gracefully handles missing weather fields, initializes empty calendar dict)

**Success Criteria:**
- Multiple regional calendars save/restore independently
- Appalachia weather doesn't affect Mojave
- File size manageable (<2MB)
- Backward compatible
- Region switching works seamlessly

---

### 4. Build WeatherSimulator Core Engine with Multi-Region Yearly Calendars

**File:** [tools/script-generator/weather_simulator.py](../tools/script-generator/weather_simulator.py)

- [ ] Implement `WeatherSimulator` class with `generate_yearly_calendar(start_date, region)` creating 365-day region-specific weather timeline
- [ ] Add calendar caching system storing separate calendars per region in WorldState.weather_calendars dict (enables simultaneous multi-DJ broadcasts with different regional weather)
- [ ] Add seasonal biasing per region during generation:
  - **Appalachia:** Dec-Feb: +20% snow in mountains, Jun-Aug: +15% afternoon thunderstorms, Sep-Nov: +25% fog
  - **Mojave:** Year-round: sunny 60%, rad_storm 8%, rain <2%
  - **Commonwealth:** Nov-Mar: +30% snow, Apr-May: +20% rain, Jun-Aug: +15% thunderstorms
- [ ] Implement post-apocalyptic event injection per region:
  - Rare "hot zones" (radiation surges 1% monthly)
  - "Dead zones" (eerie calm 0.5% chance)
  - "Mutation storms" (multiple weather simultaneously 0.2% chance)
- [ ] Add `get_current_weather(current_datetime, region)` querying correct regional calendar by date/time-of-day slot with fallback to generation if calendar missing
- [ ] Create `apply_transition()` updating WorldState for specific region, logging to regional history, detecting region-appropriate emergencies
- [ ] Build manual override system per region: `set_weather_override(region, weather_type, duration_hours, override_region_rules=False)` allowing independent regional weather control

**Success Criteria:**
- Yearly calendars generate independently per region in <8s each
- Appalachia calendar shows more rain than Mojave
- Simultaneous DJ broadcasts use correct regional weather
- Seasonal patterns visible per region

---

### 5. Implement Historical Weather Archive System

**File:** [tools/script-generator/weather_simulator.py](../tools/script-generator/weather_simulator.py)

- [ ] Add `WeatherHistoryArchive` class with methods:
  - `log_actual_weather(region, datetime, weather_state)`
  - `get_historical_weather(region, start_date, end_date)`
  - `get_notable_events(region)`
- [ ] Extend WorldState schema with `weather_history_archive` storing actual broadcast weather by region/date
  - Structure: `{region: {date: {time_of_day: weather_state}}}`
- [ ] Implement automatic logging in [broadcast_engine.py](../tools/script-generator/broadcast_engine.py) after each weather segment generated, calling `world_state.log_weather_history(region, current_time, weather_state)`
- [ ] Create notable weather event detection:
  - Rad storms
  - 3+ day rain patterns
  - Temperature extremes >100°F or <10°F
  - Mutation storms
  - Auto-tag for easy DJ reference
- [ ] Add `get_weather_reference_context()` helper returning DJ-friendly historical snippets:
  - "Remember that big rad storm last October?"
  - "We haven't seen rain like this since June..."
- [ ] Build archive compression for old data (>1 year old) to prevent file bloat while maintaining queryable history

**Success Criteria:**
- Every weather segment logged to archive
- Historical queries return correct past weather
- Notable events auto-tagged
- Archive grows sustainably (<5MB per year)
- DJs can reference past weather accurately

---

### 6. Integrate Simulator with BroadcastEngine & Regional Emergency System

**File:** [tools/script-generator/broadcast_engine.py](../tools/script-generator/broadcast_engine.py#L346-L354)

- [ ] Modify to detect DJ region from dj_name, call `world_state.get_current_weather(region)` instead of `select_weather()`
- [ ] Pass simulator instance to BroadcastEngine `__init__`, auto-load/generate regional calendar for active DJ on startup
- [ ] Add `check_for_emergency_weather(region)` method detecting region-specific emergencies from current weather state
- [ ] Implement `generate_emergency_weather_alert(region, weather_state)` creating urgent region-specific warning segment (uses emergency_weather.jinja2 template)
- [ ] Update `_build_template_vars()` to include:
  - Regional context (region_name, regional_locations from RAG)
  - Forecast data
  - Historical references
  - is_emergency_alert flag
- [ ] Add `weather_changed` and `weather_notable` flags comparing current vs last broadcast and checking historical archive for reference opportunities
- [ ] Integrate historical archive logging after segment generation with region-specific tagging

**Success Criteria:**
- BroadcastEngine uses correct regional calendar per DJ
- Julie gets Appalachia weather while Mr. New Vegas gets Mojave simultaneously
- Emergency alerts region-appropriate
- Historical weather logged automatically
- DJs reference past weather

---

### 7. Create Dedicated Emergency Weather Template

**File:** [tools/script-generator/templates/emergency_weather.jinja2](../tools/script-generator/templates/emergency_weather.jinja2)

- [ ] Create template with urgent tone structure:
  - ATTENTION/WARNING header
  - Immediate danger description
  - Shelter instructions
  - Estimated duration
- [ ] Add regional emergency variations:
  - **Appalachia:** "Scorchbeast rad storm", "seek Vault-Tec shelter", "Responders protocols"
  - **Mojave:** "radioactive dust wall", "NCR shelter stations", "visibility zero"
  - **Commonwealth:** "glowing sea drift", "Minutemen safe zones", "Institute detection"
- [ ] Implement emergency severity levels based on weather intensity from calendar:
  - Minor: 30-min warning
  - Moderate: 15-min warning
  - Severe: immediate alert
- [ ] Add emergency-specific RAG query context in [broadcast_engine.py](../tools/script-generator/broadcast_engine.py#L385) for radiation safety, shelter locations, survival protocols per region
- [ ] Update [generator.py](../tools/script-generator/generator.py) to handle emergency_weather template type with elevated urgency parameters (temperature=0.6, max_words=75)

**Success Criteria:**
- Emergency template generates urgent distinct tone
- Regional references authentic
- Alerts <75 words
- Severity levels produce appropriate urgency
- RAG context includes region-specific safety info

---

### 8. Add Forecast Generation & Regional Announcement Capabilities

**Files:** [weather_simulator.py](../tools/script-generator/weather_simulator.py), [weather.py](../tools/script-generator/content_types/weather.py#L223), [weather.jinja2](../tools/script-generator/templates/weather.jinja2), [broadcast_scheduler.py](../tools/script-generator/broadcast_scheduler.py#L48)

- [ ] Create `get_forecast_from_calendar(current_date, days_ahead, region)` in weather_simulator.py querying regional calendar for 1-7 day forecasts
- [ ] Implement `get_forecast_template_vars(region)` in weather.py returning:
  - tomorrow_weather
  - three_day_summary
  - weekly_outlook
  - is_rad_storm_approaching
  - regional_outlook
- [ ] Add historical comparison in forecasts using archive queries:
  - "Warmer than this time last year..."
  - "Similar to the pattern we saw in August..."
- [ ] Extend weather.jinja2 template with blocks:
  - Regional weather context block
  - Historical reference block
  - Forecast blocks (6 AM morning outlook, 6 PM evening, 10 PM next-day preview)
- [ ] Add forecast scheduling in broadcast_scheduler.py with emergency priority (rad_storm alerts = 10.0, regular forecasts = time-based)
- [ ] Build regional forecast phrasing helpers:
  - Appalachia: "mountain fog", "valley rain"
  - Mojave: "desert heat", "sandstorm risk"
  - Commonwealth: "nor'easter", "coastal storm"

**Success Criteria:**
- Forecasts query correct regional calendar
- Historical comparisons accurate and natural
- Julie announces Appalachian mountain weather
- Mr. New Vegas references Mojave heat
- Forecasts match calendar 95%+

---

### 9. Implement Weather Continuity & Regional DJ References

**Files:** [session_memory.py](../tools/script-generator/session_memory.py#L96), weather template

- [ ] Add `get_weather_continuity_context(region)` to session_memory.py checking weather changes and querying historical archive for reference material
- [ ] Create regional continuity phrases database (200+ variations):
  - **Appalachia:** "That mountain fog finally lifted...", "Scorchbeast storm passed quicker than expected..."
  - **Mojave:** "Heat's holding steady like always...", "Dust storm cleared the Strip by noon..."
  - **Commonwealth:** "Snow's still coming down since Tuesday...", "Glowing fog dissipated near Cambridge..."
- [ ] Update weather template with blocks:
  - `{% if weather_changed %}`
  - `{% if is_emergency %}`
  - `{% if regional_context %}`
  - `{% if historical_reference %}`
- [ ] Add regional location name-dropping from ChromaDB metadata using RAG queries:
  - Appalachia: Flatwoods, Charleston, Vault 76
  - Mojave: Freeside, New Vegas Strip, Hoover Dam
  - Commonwealth: Diamond City, Sanctuary Hills, Cambridge
- [ ] Integrate historical archive notable events into DJ references:
  - "Remember that three-day rad storm last month?"
  - "Coldest it's been since that freeze in January..."

**Success Criteria:**
- DJs reference previous weather with regional locations 90%+
- Historical references accurate and natural
- Julie mentions Appalachian towns
- Emergency alerts regional
- Continuity feels seamless across broadcasts

---

### 10. Add Manual Override & Debugging Capabilities

**Files:** [weather_simulator.py](../tools/script-generator/weather_simulator.py), CLI scripts

- [ ] Create `WeatherOverrideConfig` class in weather_simulator.py with methods:
  - `set_override(region, weather_type, duration_hours, start_time, temperature)`
  - `clear_override(region)`
  - `regenerate_calendar(region)`
- [ ] Add command-line script [tools/script-generator/set_weather.py](../tools/script-generator/set_weather.py):
  - Usage: `python set_weather.py --region Appalachia --type rad_storm --duration 2 --start "2026-01-18 14:00" --temp 68`
- [ ] Add command-line script [tools/script-generator/regenerate_weather_calendar.py](../tools/script-generator/regenerate_weather_calendar.py):
  - Usage: `python regenerate_weather_calendar.py --region Appalachia --start-date 2102-10-23 --seed 42`
- [ ] Add command-line script [tools/script-generator/query_weather_history.py](../tools/script-generator/query_weather_history.py) with search functionality:
  - Usage: `python query_weather_history.py --region Appalachia --start 2102-10-01 --end 2102-10-31 --notable-only --search "rad storm"`
- [ ] Implement archive search with filters:
  - Date range
  - Region
  - Weather type
  - Notable events only
  - Temperature range
- [ ] Implement override priority system (manual override > calendar lookup > fallback random) with region validation and warnings for cross-region issues
- [ ] Add override and regeneration logging to WorldState with timestamps, user/reason, region info for debugging audit trail
- [ ] Create status display in broadcast stats showing:
  - Active overrides per region
  - Calendar info (region, generation date, coverage)
  - Archive statistics

**Success Criteria:**
- Manual overrides work per region independently
- Regeneration creates new calendar <8s
- History search finds patterns accurately (all rad storms in October)
- Overrides logged clearly
- Archive search supports lore continuity research

---

### 11. Build Weather API Export (Optional Feature)

**Files:** [tools/script-generator/weather_api.py](../tools/script-generator/weather_api.py), [export_weather.py](../tools/script-generator/export_weather.py)

- [ ] Create weather_api.py with JSON export functions:
  - `export_calendar_json(region, output_path)`
  - `export_archive_json(region, start_date, end_date, output_path)`
- [ ] Add export CLI script:
  - Usage: `python export_weather.py --region Appalachia --type calendar --output weather_data.json`
- [ ] Implement JSON schema for calendar export:
  - Includes all 365 days with weather_type, temperature, time_of_day, is_emergency, regional_context
- [ ] Implement JSON schema for archive export:
  - Historical actual weather with timestamps
  - Notable events tagged
  - Continuity references
- [ ] Add optional CSV export format for spreadsheet analysis using pandas/csv module

**Success Criteria:**
- Calendar exports generate valid JSON <2s
- Archive exports include all historical data
- CSV format compatible with Excel/Google Sheets
- Exports useful for visualization and external tools

---

### 12. Testing & Validation Suite

**File:** [test_weather_simulator.py](../tools/script-generator/tests/test_weather_simulator.py)

- [ ] Create 30+ unit tests covering:
  - Regional climate profiles
  - Multi-region calendar generation
  - State transitions
  - Emergency detection
  - Manual override
  - Persistence
  - Historical archive
  - Region switching
  - Archive search
- [ ] Build regional yearly simulation tests verifying 365-day calendars for each region statistically distinct:
  - Appalachia: more rain/fog
  - Mojave: 60%+ sunny
  - Commonwealth: heavy winter snow
- [ ] Test multi-region independence:
  - Generate Appalachia + Mojave calendars
  - Verify same date has different weather
  - Run simultaneous broadcasts
- [ ] Test historical archive:
  - Log 100 weather events
  - Query by date range
  - Verify notable events tagged
  - Test search filtering
  - Test compression for old data
- [ ] Test post-apocalyptic weather events frequency:
  - Hot zones ~3-4/year
  - Mutation storms <1/year
  - Dead zones rare
- [ ] Test emergency broadcast insertion per region with historical context:
  - Appalachia rad_storm + historical reference
  - Mojave dust_storm
- [ ] Test manual override scenarios (8 cases):
  - Per-region override
  - Multi-region override
  - Scheduled override
  - Override expiration
  - Override during emergency
  - Override clear
  - Region mismatch warning
  - Temperature override
- [ ] Test calendar regeneration and historical continuity:
  - Regenerate Appalachia calendar
  - Verify archive preserved
  - Test region switching
- [ ] Test archive search functionality:
  - Find all rad storms
  - Filter by temperature
  - Notable events only
  - Date range queries
- [ ] Test migration from old world_state.json files:
  - Backward compatibility with 5 fixtures
  - Missing region defaults to Appalachia
  - Empty calendars initialize
- [ ] Performance test:
  - Calendar generation <8s per region
  - 10,000 weather queries <500ms
  - State save/load with 3 regional calendars + archive <300ms
  - Historical queries <50ms
  - Archive search <100ms
- [ ] Test JSON/CSV export validity and completeness:
  - Schema validation
  - All fields present
  - Parseable by external tools

**Success Criteria:**
- All tests pass
- Regional calendars statistically distinct (chi-squared p<0.01)
- Historical archive accurate
- Archive search finds patterns reliably
- Multi-region independence verified
- Emergency system works per region
- Manual overrides reliable per region
- Exports valid
- Backward compatible

---

## Architecture Overview

### Regional Climate Profiles

```
Appalachia (2102)
├── Base Climate: Humid Subtropical
├── Temp Range: 20-85°F
├── Precipitation: High (fog, rain, mountain snow)
├── Post-Apocalyptic: +25% rad storms (Scorchbeasts)
└── Emergency Types: rad_storm, ash_fall

Mojave (2281)
├── Base Climate: Desert
├── Temp Range: 35-115°F
├── Precipitation: Rare (<5% rain)
├── Post-Apocalyptic: +15% dust storms, extreme temp swings
└── Emergency Types: rad_storm, dust_storm

Commonwealth (2287)
├── Base Climate: Humid Continental
├── Temp Range: 10-80°F
├── Precipitation: Moderate (nor'easters)
├── Post-Apocalyptic: +10% year-round snow (nuclear winter)
└── Emergency Types: rad_storm, glowing_fog
```

### Weather State Machine

```
WeatherState {
    weather_type: str           # sunny, cloudy, rainy, rad_storm, etc.
    started_at: datetime
    duration_hours: float
    intensity: str              # minor, moderate, severe
    transition_state: str       # stable, building, clearing
    is_emergency: bool
    temperature: float
    region: str
}
```

### Calendar Storage Structure

```json
{
  "weather_calendars": {
    "Appalachia": {
      "2102-10-23": {
        "morning": { "weather_type": "foggy", "temp": 52, ... },
        "afternoon": { "weather_type": "cloudy", "temp": 68, ... },
        "evening": { "weather_type": "rainy", "temp": 58, ... },
        "night": { "weather_type": "rainy", "temp": 45, ... }
      }
    },
    "Mojave": { ... },
    "Commonwealth": { ... }
  },
  "weather_history_archive": {
    "Appalachia": {
      "2102-10-23": {
        "08:00": { "actual_weather": "foggy", "notable": false },
        "14:00": { "actual_weather": "rad_storm", "notable": true }
      }
    }
  }
}
```

### Integration Flow

```
1. BroadcastEngine starts
   ↓
2. Detect DJ region (Julie → Appalachia)
   ↓
3. Load/Generate yearly calendar for region
   ↓
4. Query current weather from calendar
   ↓
5. Check for emergency conditions
   ↓
6. Generate weather segment (or emergency alert)
   ↓
7. Log actual weather to archive
   ↓
8. Save WorldState with updated archive
```

---

## File Structure

```
tools/script-generator/
├── regional_climate.py          # NEW: Climate profiles & region detection
├── weather_simulator.py         # NEW: Core simulation engine
├── weather_api.py              # NEW: Optional JSON/CSV export
├── world_state.py              # MODIFIED: Multi-region calendar storage
├── broadcast_engine.py         # MODIFIED: Regional weather integration
├── session_memory.py           # MODIFIED: Weather continuity context
├── content_types/
│   └── weather.py              # MODIFIED: Regional forecast helpers
├── templates/
│   ├── weather.jinja2          # MODIFIED: Regional + historical blocks
│   └── emergency_weather.jinja2 # NEW: Emergency alert template
├── set_weather.py              # NEW: Manual override CLI
├── regenerate_weather_calendar.py # NEW: Calendar regeneration CLI
├── query_weather_history.py    # NEW: Archive search CLI
├── export_weather.py           # NEW: Export CLI (optional)
└── tests/
    └── test_weather_simulator.py # NEW: Comprehensive test suite
```

---

## Design Decisions

### No Cross-Region Global Events
- Each region maintains independent weather
- Multi-DJ storytelling unlikely (temporal separation)
- Allows realistic regional variety

### Historical Weather Archive
- Logs all actual broadcast weather
- Enables DJ references to past events
- Supports lore continuity research
- Notable events auto-tagged

### JSON Export Format
- Primary format for calendar/archive export
- CSV optional for spreadsheet analysis
- Useful for visualization and external tools

### Manual Calendar Regeneration
- Requires explicit trigger (not automatic)
- Allows control over when patterns change
- Prevents unexpected disruptions

### Dedicated Emergency Template
- Separate from regular weather template
- More dramatic/urgent tone control
- Region-specific emergency language

### Archive Search Interface
- CLI tool for pattern finding
- Useful for lore research
- Continuity checking support

---

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Calendar Generation | <8s per region | 365 days, all time slots |
| Weather Queries | <50ms per query | Calendar lookup |
| State Save/Load | <300ms | 3 regions + archive |
| Historical Query | <50ms | Date range search |
| Archive Search | <100ms | Pattern matching |
| Export Generation | <2s | Full calendar JSON |

---

## Success Metrics

### Realism
- Regional calendars statistically distinct (chi-squared p<0.01)
- Mojave: 60%+ sunny days
- Appalachia: Frequent fog/rain
- Commonwealth: Heavy winter snow (Nov-Mar)

### Continuity
- DJs reference previous weather 90%+ when applicable
- Historical references accurate
- Notable events properly tagged

### Emergency System
- Emergency alerts trigger for appropriate weather
- Region-specific language authentic
- Alerts <75 words for quick delivery

### Archive
- All weather segments logged
- Archive grows sustainably (<5MB/year)
- Search finds patterns reliably

### Multi-Region
- Independent regional weather verified
- Simultaneous DJ broadcasts use correct regions
- No cross-contamination

---

## Implementation Priority

### Phase 1: Core Simulation (Steps 1-4)
- Regional climate profiles
- Weather state machine
- WorldState schema extension
- Calendar generation engine

### Phase 2: Integration (Steps 5-7)
- Historical archive system
- BroadcastEngine integration
- Emergency template

### Phase 3: Enhancement (Steps 8-9)
- Forecast generation
- Weather continuity & DJ references

### Phase 4: Tools & Testing (Steps 10-12)
- Manual override CLI tools
- Optional API export
- Comprehensive test suite

---

## Notes

- System designed for mock radio station script generation
- No actual real-time data integration needed
- Pre-generated calendars enable consistent storytelling
- Historical archive supports long-term lore building
- Regional independence matches Fallout timeline (different years, different locations)
