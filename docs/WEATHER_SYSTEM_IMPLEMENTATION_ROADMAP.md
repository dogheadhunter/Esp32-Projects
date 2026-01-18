# Weather System Implementation Roadmap
## Integration with Broadcast Engine

**Created:** January 18, 2026  
**Status:** Ready for Implementation  
**Based on:** `research/WEATHER_SIMULATION_SYSTEM_PLAN.md`  
**Target:** `tools/script-generator/broadcast_engine.py` integration

---

## Executive Summary

This document outlines the implementation roadmap for integrating the comprehensive weather simulation system (detailed in `research/WEATHER_SIMULATION_SYSTEM_PLAN.md`) with the existing broadcast engine production system.

### Key Features to Implement

1. **Multi-Regional Weather Simulation** - Separate calendars for Appalachia, Mojave, and Commonwealth
2. **365-Day Pre-Generated Calendars** - Year-long weather patterns per region
3. **Historical Weather Archive** - Track past weather for continuity and DJ references
4. **Emergency Weather Alerts** - Rad storms, dust storms, and other post-apocalyptic hazards
5. **Manual Override System** - Debug tools for testing and special broadcasts

### Integration with Broadcast Engine

The weather system will enhance the existing `broadcast_engine.py` by:
- Automatically detecting DJ region from personality
- Loading/generating appropriate regional weather calendar
- Providing historical context for weather continuity
- Triggering emergency broadcasts when needed
- Logging all weather events to archive for future reference

---

## Current State Analysis

### Existing Weather System (`tools/script-generator/content_types/weather.py`)

**Strengths:**
- ✅ Basic weather types defined (sunny, cloudy, rainy, rad_storm, foggy, snow)
- ✅ RAG query integration for lore context
- ✅ Survival tips system
- ✅ Time-of-day variations
- ✅ Location-aware tips (Appalachia, Mojave)

**Limitations:**
- ❌ No persistent weather state across broadcasts
- ❌ Random selection doesn't create realistic patterns
- ❌ No multi-day weather fronts or seasonal variations
- ❌ No historical continuity ("remember last week's storm")
- ❌ No regional climate differences (Mojave vs Appalachia)
- ❌ No emergency weather system integration

### Broadcast Engine Integration Points

**Current:** `broadcast_engine.py` calls `select_weather()` for random weather  
**Future:** Will call `weather_simulator.get_current_weather(region, datetime)`

**Files to Modify:**
- `tools/script-generator/broadcast_engine.py` (lines ~346-354)
- `tools/script-generator/world_state.py` (schema extension)
- `tools/script-generator/session_memory.py` (weather continuity)

---

## Implementation Phases

### Phase 1: Core Regional Weather Foundation (Week 1)
**Goal:** Establish multi-regional weather system with persistent calendars

#### Step 1.1: Regional Climate Profiles
**File:** `tools/script-generator/regional_climate.py` (NEW)

```python
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class RegionalClimate:
    """Climate profile for a Fallout region"""
    region_name: str
    base_temp_range: tuple[float, float]  # (min, max) in °F
    seasonal_patterns: Dict[str, Dict]
    precipitation_frequency: float  # 0.0-1.0
    special_conditions: List[str]
    post_apocalyptic_modifiers: Dict[str, float]

# Implement climate profiles for:
# - Appalachia (2102): Humid subtropical, frequent fog/rain, Scorchbeast rad storms
# - Mojave (2281): Desert, extreme temps, rare rain, NCR-era dust storms
# - Commonwealth (2287): Humid continental, cold winters, Glowing Sea radiation drift
```

**Integration with Broadcast Engine:**
```python
def get_region_from_dj_name(dj_name: str) -> str:
    """Extract region from DJ personality name"""
    if "Appalachia" in dj_name or "Julie" in dj_name:
        return "Appalachia"
    elif "Mojave" in dj_name or "New Vegas" in dj_name:
        return "Mojave"
    elif "Commonwealth" in dj_name or "Travis" in dj_name:
        return "Commonwealth"
    return "Appalachia"  # Default
```

#### Step 1.2: Weather State Machine
**File:** `tools/script-generator/weather_simulator.py` (NEW)

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

@dataclass
class WeatherState:
    """Complete weather state at a point in time"""
    weather_type: str  # sunny, cloudy, rainy, rad_storm, etc.
    started_at: datetime
    duration_hours: float
    intensity: str  # minor, moderate, severe
    transition_state: str  # stable, building, clearing
    is_emergency: bool
    temperature: float
    region: str
    notable_event: bool = False

class WeatherSimulator:
    """Core weather simulation engine"""
    
    def generate_yearly_calendar(self, start_date: datetime, region: str) -> Dict:
        """Generate 365-day weather calendar for region"""
        # Implementation per WEATHER_SIMULATION_SYSTEM_PLAN.md
        pass
    
    def get_current_weather(self, current_datetime: datetime, region: str) -> WeatherState:
        """Get weather for specific datetime and region"""
        # Query calendar, fallback to generation if missing
        pass
```

#### Step 1.3: WorldState Schema Extension
**File:** `tools/script-generator/world_state.py` (MODIFIED)

Add new fields to WorldState:
```python
class WorldState:
    def __init__(self, persistence_path: str = "./broadcast_state.json"):
        # ... existing fields ...
        
        # NEW: Multi-regional weather calendars
        self.weather_calendars: Dict[str, Dict] = {}  # {region: {date: {time_of_day: weather}}}
        self.current_weather_by_region: Dict[str, WeatherState] = {}
        self.weather_history_archive: Dict[str, Dict] = {}  # {region: {date: {time: weather}}}
        self.calendar_metadata: Dict[str, Dict] = {}  # Generation date, seed, etc.
        self.manual_overrides: Dict[str, Optional[WeatherState]] = {}
    
    def get_current_weather(self, region: str) -> Optional[WeatherState]:
        """Get current weather for region"""
        return self.current_weather_by_region.get(region)
    
    def get_weather_history(self, region: str, start_date: datetime, end_date: datetime) -> List[WeatherState]:
        """Query historical weather for region"""
        # Search archive
        pass
```

**Migration Strategy:**
- Existing `broadcast_state.json` files without weather fields will initialize empty
- Graceful handling of missing regional calendars (auto-generate on first access)
- Backward compatible with pre-weather broadcasts

---

### Phase 2: Broadcast Engine Integration (Week 2)
**Goal:** Connect weather simulator to broadcast generation

#### Step 2.1: Modify BroadcastEngine Initialization
**File:** `tools/script-generator/broadcast_engine.py` (lines ~46-100)

```python
from weather_simulator import WeatherSimulator
from regional_climate import get_region_from_dj_name

class BroadcastEngine:
    def __init__(self, dj_name: str, ...):
        # ... existing initialization ...
        
        # NEW: Weather simulation
        self.region = get_region_from_dj_name(dj_name)
        self.weather_simulator = WeatherSimulator()
        
        # Load or generate regional calendar
        if self.region not in self.world_state.weather_calendars:
            print(f"Generating yearly weather calendar for {self.region}...")
            calendar = self.weather_simulator.generate_yearly_calendar(
                start_date=datetime.now(),
                region=self.region
            )
            self.world_state.weather_calendars[self.region] = calendar
            self.world_state.save()
```

#### Step 2.2: Replace Weather Selection Logic
**File:** `tools/script-generator/broadcast_engine.py` (lines ~346-354)

**BEFORE:**
```python
# Old random weather selection
from content_types.weather import select_weather
weather_type = select_weather(recent_weathers=recent)
```

**AFTER:**
```python
# New calendar-based weather
current_weather = self.weather_simulator.get_current_weather(
    current_datetime=datetime.now(),
    region=self.region
)

# Check for emergency weather
if current_weather.is_emergency:
    return self._generate_emergency_weather_alert(current_weather)
```

#### Step 2.3: Historical Weather Logging
**File:** `tools/script-generator/broadcast_engine.py` (after segment generation)

```python
def _log_weather_to_archive(self, weather_state: WeatherState, broadcast_time: datetime):
    """Log actual broadcast weather to historical archive"""
    self.world_state.log_weather_history(
        region=self.region,
        timestamp=broadcast_time,
        weather_state=weather_state
    )
    self.world_state.save()
```

---

### Phase 3: Historical Context & Continuity (Week 3)
**Goal:** Enable DJs to reference past weather events

#### Step 3.1: Weather Continuity in Session Memory
**File:** `tools/script-generator/session_memory.py` (lines ~96+)

```python
def get_weather_continuity_context(self, region: str, world_state: WorldState) -> Dict:
    """Get weather continuity context for DJ references"""
    
    # Check if weather changed since last broadcast
    last_weather = self._get_last_weather_from_memory()
    current_weather = world_state.get_current_weather(region)
    
    # Query historical archive for notable events
    notable_events = world_state.get_notable_weather_events(
        region=region,
        days_back=30
    )
    
    return {
        'weather_changed': last_weather != current_weather.weather_type if last_weather else False,
        'last_weather_type': last_weather,
        'notable_recent_events': notable_events,  # "Big rad storm on Oct 15"
        'continuity_phrases': self._generate_continuity_phrases(last_weather, current_weather)
    }
```

#### Step 3.2: Update Weather Template
**File:** `tools/script-generator/templates/weather.jinja2` (MODIFIED)

Add historical context blocks:
```jinja2
{% if weather_changed %}
{# DJ acknowledges weather change #}
{{ continuity_phrases.transition }}
{% endif %}

{% if historical_reference %}
{# DJ references past weather event #}
{{ historical_reference }}
{% endif %}

{# Regional location name-dropping from RAG #}
{% if regional_locations %}
Current conditions near {{ regional_locations[0] }}...
{% endif %}
```

---

### Phase 4: Emergency Weather System (Week 4)
**Goal:** Implement emergency weather alerts and interruptions

#### Step 4.1: Emergency Weather Template
**File:** `tools/script-generator/templates/emergency_weather.jinja2` (NEW)

```jinja2
{# URGENT TONE - Emergency Weather Alert #}

⚠️ ATTENTION {{ location }} RESIDENTS ⚠️

{{ emergency_type|upper }} ALERT IN EFFECT

{% if emergency_type == "rad_storm" %}
RADIOACTIVE STORM DETECTED. Radiation levels rising rapidly.
{% elif emergency_type == "dust_storm" %}
SEVERE DUST WALL APPROACHING. Visibility dropping to zero.
{% elif emergency_type == "glowing_fog" %}
GLOWING SEA RADIATION DRIFT. Contaminated fog spreading.
{% endif %}

IMMEDIATE ACTION REQUIRED:
{{ shelter_instructions }}

Estimated Duration: {{ duration_hours }} hours

{{ dj_emergency_signoff }}

{# RAG context: region-specific shelter locations, safety protocols #}
```

#### Step 4.2: Emergency Detection in Broadcast Engine
**File:** `tools/script-generator/broadcast_engine.py`

```python
def check_for_emergency_weather(self) -> Optional[WeatherState]:
    """Check if current weather requires emergency alert"""
    current_weather = self.world_state.get_current_weather(self.region)
    
    if current_weather and current_weather.is_emergency:
        # Check if we already alerted for this event
        if not self._already_alerted(current_weather):
            return current_weather
    
    return None

def _generate_emergency_weather_alert(self, weather_state: WeatherState) -> Dict:
    """Generate emergency weather alert segment"""
    
    # Get region-specific RAG context
    rag_context = self._get_emergency_rag_context(weather_state)
    
    template_vars = {
        'emergency_type': weather_state.weather_type,
        'location': self.region,
        'severity': weather_state.intensity,
        'duration_hours': weather_state.duration_hours,
        'shelter_instructions': self._get_regional_shelter_instructions(),
        'rag_context': rag_context
    }
    
    # Use emergency template with high urgency
    return self.generator.generate(
        template_name='emergency_weather',
        template_vars=template_vars,
        temperature=0.6,  # More focused for emergencies
        max_words=75  # Keep it brief and urgent
    )
```

---

### Phase 5: Manual Override & Debug Tools (Week 5)
**Goal:** Provide CLI tools for testing and manual weather control

#### Step 5.1: Manual Weather Override Script
**File:** `tools/script-generator/set_weather.py` (NEW)

```python
#!/usr/bin/env python3
"""
Manual Weather Override Tool

Usage:
    python set_weather.py --region Appalachia --type rad_storm --duration 2
    python set_weather.py --region Mojave --type sunny --temp 110 --duration 8
    python set_weather.py --clear-override --region Commonwealth
"""

import argparse
from datetime import datetime, timedelta
from weather_simulator import WeatherSimulator
from world_state import WorldState

def main():
    parser = argparse.ArgumentParser(description='Set manual weather override')
    parser.add_argument('--region', required=True, choices=['Appalachia', 'Mojave', 'Commonwealth'])
    parser.add_argument('--type', help='Weather type (sunny, rainy, rad_storm, etc.)')
    parser.add_argument('--duration', type=float, help='Duration in hours')
    parser.add_argument('--temp', type=float, help='Temperature in °F')
    parser.add_argument('--clear-override', action='store_true', help='Clear existing override')
    
    args = parser.parse_args()
    
    world_state = WorldState()
    
    if args.clear_override:
        world_state.clear_manual_override(args.region)
        print(f"✓ Cleared weather override for {args.region}")
    else:
        # Set override
        override = WeatherState(
            weather_type=args.type,
            started_at=datetime.now(),
            duration_hours=args.duration or 4.0,
            temperature=args.temp or 70.0,
            region=args.region,
            is_emergency='storm' in args.type
        )
        
        world_state.set_manual_weather_override(args.region, override)
        print(f"✓ Set {args.region} weather to {args.type} for {args.duration}h")
    
    world_state.save()

if __name__ == '__main__':
    main()
```

#### Step 5.2: Weather History Query Tool
**File:** `tools/script-generator/query_weather_history.py` (NEW)

```python
#!/usr/bin/env python3
"""
Weather History Query Tool

Usage:
    python query_weather_history.py --region Appalachia --start 2102-10-01 --end 2102-10-31
    python query_weather_history.py --region Mojave --notable-only
    python query_weather_history.py --region Commonwealth --search "rad storm"
"""

import argparse
from datetime import datetime
from world_state import WorldState

def main():
    parser = argparse.ArgumentParser(description='Query weather history archive')
    parser.add_argument('--region', required=True)
    parser.add_argument('--start', help='Start date YYYY-MM-DD')
    parser.add_argument('--end', help='End date YYYY-MM-DD')
    parser.add_argument('--notable-only', action='store_true')
    parser.add_argument('--search', help='Search for weather type')
    
    args = parser.parse_args()
    
    world_state = WorldState()
    
    history = world_state.get_weather_history(
        region=args.region,
        start_date=datetime.fromisoformat(args.start) if args.start else None,
        end_date=datetime.fromisoformat(args.end) if args.end else None
    )
    
    # Filter results
    if args.notable_only:
        history = [h for h in history if h.notable_event]
    
    if args.search:
        history = [h for h in history if args.search.lower() in h.weather_type.lower()]
    
    # Display results
    print(f"\n📊 Weather History for {args.region}")
    print(f"Found {len(history)} matching events\n")
    
    for event in history:
        print(f"  {event.started_at.strftime('%Y-%m-%d %H:%M')} - {event.weather_type}")
        if event.notable_event:
            print(f"    ⭐ Notable Event")
        print(f"    Temp: {event.temperature}°F, Duration: {event.duration_hours}h")
        print()

if __name__ == '__main__':
    main()
```

---

## Testing Strategy

### Unit Tests
**File:** `tools/script-generator/tests/test_weather_simulator.py` (NEW)

```python
class TestRegionalClimate:
    def test_appalachia_climate_profile(self):
        """Appalachia has humid subtropical characteristics"""
        
    def test_mojave_climate_profile(self):
        """Mojave has desert characteristics"""
    
    def test_commonwealth_climate_profile(self):
        """Commonwealth has humid continental characteristics"""

class TestWeatherSimulator:
    def test_yearly_calendar_generation(self):
        """365-day calendar generates in <8s"""
        
    def test_regional_independence(self):
        """Appalachia and Mojave calendars are different"""
    
    def test_seasonal_patterns(self):
        """Winter in Commonwealth has more snow than summer"""
    
    def test_emergency_detection(self):
        """Rad storms flagged as emergency"""

class TestBroadcastEngineIntegration:
    def test_region_detection_from_dj_name(self):
        """Julie → Appalachia, Mr. New Vegas → Mojave"""
    
    def test_weather_calendar_loading(self):
        """Engine loads correct regional calendar"""
    
    def test_emergency_alert_generation(self):
        """Emergency weather triggers alert segment"""
    
    def test_historical_weather_logging(self):
        """Each weather segment logged to archive"""
```

### Integration Tests
```python
class TestMultiRegionalBroadcast:
    def test_simultaneous_dj_broadcasts(self):
        """Julie and Mr. New Vegas get different weather"""
        
    def test_weather_continuity_across_sessions(self):
        """Weather state persists between broadcasts"""
    
    def test_historical_references_accuracy(self):
        """DJs reference past weather correctly"""
```

---

## Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Calendar Generation | <8s per region | 365 days × 4 time slots |
| Weather Query | <50ms | Calendar lookup |
| State Save/Load | <300ms | 3 regions + archive |
| Historical Query | <50ms | Date range search |
| Emergency Detection | <10ms | Real-time check |

---

## File Checklist

### New Files to Create
- [ ] `tools/script-generator/regional_climate.py`
- [ ] `tools/script-generator/weather_simulator.py`
- [ ] `tools/script-generator/templates/emergency_weather.jinja2`
- [ ] `tools/script-generator/set_weather.py`
- [ ] `tools/script-generator/query_weather_history.py`
- [ ] `tools/script-generator/regenerate_weather_calendar.py`
- [ ] `tools/script-generator/tests/test_weather_simulator.py`

### Files to Modify
- [ ] `tools/script-generator/broadcast_engine.py` (weather integration)
- [ ] `tools/script-generator/world_state.py` (schema extension)
- [ ] `tools/script-generator/session_memory.py` (continuity context)
- [ ] `tools/script-generator/content_types/weather.py` (forecast helpers)
- [ ] `tools/script-generator/templates/weather.jinja2` (historical blocks)

### Files to Reference (No Changes)
- ✓ `research/WEATHER_SIMULATION_SYSTEM_PLAN.md` (Complete specification)
- ✓ `tools/script-generator/content_types/weather.py` (Existing weather types)
- ✓ `dj_personalities/` (DJ region information)

---

## Implementation Schedule

### Week 1: Core Foundation
- Regional climate profiles
- Weather state machine
- WorldState schema extension
- Basic calendar generation

### Week 2: Broadcast Integration
- Modify BroadcastEngine initialization
- Replace weather selection logic
- Implement historical logging
- Basic testing

### Week 3: Continuity & Context
- Session memory weather context
- Update weather template
- Historical references
- RAG integration for regional lore

### Week 4: Emergency System
- Emergency weather template
- Emergency detection logic
- Regional shelter instructions
- Alert generation

### Week 5: Tools & Testing
- Manual override CLI
- History query CLI
- Calendar regeneration tool
- Comprehensive test suite
- Performance optimization

---

## Success Criteria

### Functionality
- ✅ Each region has distinct weather patterns
- ✅ Weather persists across broadcast sessions
- ✅ DJs reference past weather accurately
- ✅ Emergency alerts trigger appropriately
- ✅ Manual overrides work per region

### Quality
- ✅ Appalachia gets more fog/rain than Mojave
- ✅ Mojave is 60%+ sunny
- ✅ Commonwealth has heavy winter snow
- ✅ Historical references feel natural
- ✅ Regional lore context accurate

### Performance
- ✅ Calendar generation <8s per region
- ✅ Weather queries <50ms
- ✅ State persistence <300ms
- ✅ No noticeable slowdown in broadcast generation

### Testing
- ✅ 30+ unit tests passing
- ✅ Integration tests verify multi-region independence
- ✅ Historical archive tests confirm accuracy
- ✅ Emergency system tests verify regional variations

---

## Migration Path

### For Existing Broadcasts
1. Run first broadcast with new system
2. System detects missing weather calendar
3. Auto-generates calendar for DJ's region
4. Saves to `broadcast_state.json`
5. Subsequent broadcasts use calendar

### For Development/Testing
1. Use `set_weather.py` to force specific conditions
2. Use `query_weather_history.py` to verify continuity
3. Use `regenerate_weather_calendar.py` to reset if needed

---

## Related Documentation

- **Full Specification:** `research/WEATHER_SIMULATION_SYSTEM_PLAN.md`
- **Architecture:** `docs/ARCHITECTURE.md`
- **Broadcast Engine:** `tools/script-generator/broadcast_engine.py`
- **World State:** `tools/script-generator/world_state.py`

---

## Next Steps

1. ✅ Review this roadmap
2. ⏳ Begin Phase 1 implementation (regional climate profiles)
3. ⏳ Validate with unit tests
4. ⏳ Integrate with broadcast_engine
5. ⏳ Test with real broadcast generation
6. ⏳ Deploy and monitor

---

**Status:** Ready for Implementation  
**Priority:** High - Enhances broadcast realism and continuity  
**Complexity:** Moderate - Well-defined scope, clear integration points  
**Risk:** Low - Non-breaking changes, backward compatible
