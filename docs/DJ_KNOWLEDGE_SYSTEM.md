# DJ Knowledge & Information Access System

## Overview

This document defines how each DJ character in the ESP32 AI Radio project accesses and presents knowledge from the Fallout universe, ensuring temporal accuracy, regional consistency, and character-authentic narrative framing.

## Core Principles

1. **Temporal Constraints**: DJs cannot know about events that happen after their time period
2. **Regional Boundaries**: Local knowledge is high-confidence, distant regions are rumors only
3. **Information Sources**: Access is determined by in-universe information transmission methods
4. **Narrative Framing**: How knowledge is presented must match character personality and source reliability

## DJ Knowledge Profiles

### Julie (Appalachia Radio, 2102)

**Time Period**: 2102 (Fallout 76 era - 25 years after Great War)  
**Location**: Appalachia (West Virginia)  
**Age**: ~23 years old  
**Background**: Vault 76 survivor, amateur DJ

#### Knowledge Constraints
- **Temporal Cutoff**: `year_max ≤ 2102`
- **Cannot Know**: NCR expansion (2161+), Mojave events (2281), Commonwealth events (2287), New Vegas (179 years in her future)
- **Primary Location**: Appalachia
- **Adjacent Regions**: East Coast (Capital Wasteland rumors only)

#### Special Access: Vault-Tec Archives (Extended)
- **Scope**: ALL `info_source: "vault-tec"` content up to year 2102
- **Includes**: Any vault experiments, pre-war Vault-Tec documentation, classified projects, obscure vault lore
- **Justification**: She has access to Vault 76's terminal network and archives
- **Required Framing**: MUST be presented as recent discovery/new finding

#### Discovery Language Templates
Julie's Vault-Tec knowledge must be wrapped in discovery narrative:
- "I was digging through the old Vault-Tec terminals and found..."
- "Came across something in the archives today..."
- "You won't believe what I just uncovered..."
- "Found this buried in the old files..."
- "Been reading through some classified docs, and..."
- "Just discovered something in the database..."

#### Confidence Tiers
- **1.0 (High)**: Appalachia events, local factions (Responders, Free States, Scorched), Vault 76 knowledge
- **0.7 (Medium)**: Common wasteland knowledge, general pre-war history, basic survival info
- **0.4 (Low - Rumors)**: East Coast events (Capital Wasteland), major faction movements, big disasters
- **0.0 (Excluded)**: Technical specifications from other regions, future events, West Coast details

#### Content Type Filtering for Rumors
Low-confidence (caravan gossip) queries include:
- ✅ `content_type: ["event", "faction", "location", "character"]`
- ❌ `content_type: ["item", "technology", "quest"]` (technical details don't spread)

---

### Mr. New Vegas (Mojave Wasteland, 2281)

**Time Period**: 2281 (Fallout: New Vegas era)  
**Location**: Mojave Wasteland / New Vegas  
**Nature**: AI programmed by Mr. House (never admits this, believes he's human)  
**Background**: Sophisticated broadcasting personality

#### Knowledge Constraints
- **Temporal Cutoff**: `year_max ≤ 2281`
- **Cannot Know**: Institute details (2287), Railroad (2287), Commonwealth Minutemen (2287), Sole Survivor events
- **Primary Location**: Mojave Wasteland
- **Adjacent Regions**: West Coast (California, NCR territory)

#### Special Access: Expanded Pre-War Knowledge
- **Scope**: Broader access to `pre_war: true` content and expanded `knowledge_tier`
- **Includes**: Pre-war history, old world culture, lost civilization details
- **Justification**: AI with extensive databases (though he doesn't know he's AI)
- **Required Framing**: Nostalgic/romantic historical reflection

#### Romantic Historian Framing Templates
Mr. New Vegas's pre-war knowledge uses consistent nostalgic language:
- "Ah, the old days..."
- "Reminds me of a time when..."
- "The world that was..."
- "In those golden days..."
- "Such romance in the lost world..."
- "The old world had its charms..."
- "In the golden age before the fire..."
- "Ah, such elegance in ages past..."
- "Love conquers even the atom's fire..."
- "They knew how to live back then..."

**Note**: Romantic framing is CONSISTENT regardless of temporal distance. No speculation intensity scaling - all pre-war references maintain the same nostalgic tone.

#### Confidence Tiers
- **1.0 (High)**: Mojave events, New Vegas politics, Hoover Dam conflict, local factions (NCR, Legion, House)
- **0.7 (Medium)**: West Coast regional knowledge, NCR expansion history, Brotherhood presence
- **0.4 (Low - Rumors)**: East Coast major events, distant faction movements
- **0.0 (Excluded)**: Commonwealth events (future), Institute technology, technical specs from distant regions

---

### Travis Miles - Nervous (Diamond City Radio, 2287)

**Time Period**: 2287 (Fallout 4 era, pre-Confidence Man quest)  
**Location**: Commonwealth (Massachusetts)  
**Background**: Anxious, self-doubting DJ

#### Knowledge Constraints
- **Temporal Cutoff**: `year_max ≤ 2287`
- **Primary Location**: Commonwealth
- **Adjacent Regions**: East Coast only
- **Restricted Access**: `knowledge_tier: ["common", "regional"]` ONLY - NO classified, NO restricted

#### Confidence Tiers
- **1.0 (High)**: Diamond City, local settlements, Commonwealth dangers, common threats
- **0.7 (Medium)**: Brotherhood of Steel presence, Institute rumors (vague), Minutemen
- **0.4 (Low - Rumors)**: Major East Coast events, distant settlement news
- **0.0 (Excluded)**: Vault-Tec classified, Institute internal details, West Coast events, pre-war technical specs

---

### Travis Miles - Confident (Diamond City Radio, 2287)

**Time Period**: 2287 (Fallout 4 era, post-Confidence Man quest)  
**Location**: Commonwealth (Massachusetts)  
**Background**: Transformed into suave "cool cat" persona

#### Knowledge Constraints
- **Temporal Cutoff**: `year_max ≤ 2287`
- **Primary Location**: Commonwealth
- **Adjacent Regions**: East Coast regional knowledge
- **Access Level**: `knowledge_tier: ["common", "regional"]` - expanded regional awareness

#### Confidence Tiers
- **1.0 (High)**: Commonwealth factions, Brotherhood operations, Railroad rumors, Minutemen rebuilding
- **0.7 (Medium)**: East Coast history, Capital Wasteland connections, regional trade routes
- **0.4 (Low - Rumors)**: Major wasteland events, distant faction politics
- **0.0 (Excluded)**: Vault-Tec classified, Institute secrets (unless public knowledge), West Coast details

---

## Information Source Taxonomy

Based on `info_source` metadata field in ChromaDB:

### Public
- General wasteland knowledge
- Oral tradition and common lore
- Widely known survival information
- **Accessibility**: All DJs can access within time/location constraints

### Military
- Brotherhood of Steel codex
- Enclave records
- NCR military documents
- Army base archives
- **Accessibility**: Regional DJs with military faction presence (filtered by location)

### Corporate
- RobCo, West Tek, Poseidon Energy records
- General Atomics, Nuka-Cola Corp documentation
- Pre-war industrial archives
- **Accessibility**: Common tier if general knowledge, restricted if technical

### Vault-Tec
- Vault experiments and internal documentation
- Classified projects
- Pre-war Vault-Tec corporate records
- **Accessibility**: Julie has FULL access (with discovery framing), others only if common knowledge

### Faction
- Specific organization records (Followers of the Apocalypse, etc.)
- Faction-specific lore and history
- **Accessibility**: Regional filtering applies, confidence varies by faction prominence

---

## Information Transmission Methods (In-Universe)

### High Reliability (Confidence: 1.0)
1. **Direct Observation**: Local events the DJ or survivors witness
2. **Radio Broadcasts**: Other DJ transmissions within ~50 mile radius
3. **Terminal Networks**: Operational computer systems in the DJ's facility
4. **Vault Archives**: Preserved records (Julie's special access)

### Medium Reliability (Confidence: 0.7)
5. **Faction Communications**: Brotherhood, NCR, Enclave messengers
6. **Written Records**: Notes, letters, documents found locally
7. **Holotapes**: Audio recordings salvaged from nearby locations

### Low Reliability (Confidence: 0.4 - Rumors Only)
8. **Caravan/Trade Route Gossip**: Traveling merchant stories
9. **Survivor Reports**: Second-hand accounts from distant travelers
10. **Radio Relay**: News from other DJs at extreme range (degraded)

**Critical Constraint**: DJs are STATIONARY. They never leave their radio stations. All information comes TO them, not from personal travel.

---

## ChromaDB Query Implementation

### Base Query Structure

```python
DJ_KNOWLEDGE_PROFILES = {
    "Julie": {
        "temporal": {"year_max": {"$lte": 2102}},
        "high_confidence": {
            "$and": [
                {"year_max": {"$lte": 2102}},
                {"$or": [
                    {"location": "Appalachia"},
                    {"info_source": "vault-tec"},
                    {"knowledge_tier": "common"}
                ]}
            ]
        },
        "medium_confidence": {
            "$and": [
                {"year_max": {"$lte": 2102}},
                {"knowledge_tier": "common"}
            ]
        },
        "low_confidence": {
            "$and": [
                {"year_max": {"$lte": 2102}},
                {"content_type": {"$in": ["event", "faction", "location", "character"]}},
                {"info_source": "public"}
            ]
        },
        "narrative_context": {
            "vault_tec_prefix": [
                "I was digging through the old Vault-Tec terminals and found",
                "Came across something in the archives today",
                "You won't believe what I just uncovered",
                "Found this buried in the old files",
                "Been reading through some classified docs, and"
            ],
            "rumor_prefix": [
                "Heard from a caravan that",
                "Word is spreading that",
                "Travelers are saying",
                "Rumors from the trade routes suggest"
            ]
        }
    },
    
    "Mr. New Vegas": {
        "temporal": {"year_max": {"$lte": 2281}},
        "high_confidence": {
            "$and": [
                {"year_max": {"$lte": 2281}},
                {"$or": [
                    {"location": "Mojave Wasteland"},
                    {"region": "West Coast"},
                    {"knowledge_tier": "common"}
                ]}
            ]
        },
        "medium_confidence": {
            "$and": [
                {"year_max": {"$lte": 2281}},
                {"$or": [
                    {"region": "West Coast"},
                    {"knowledge_tier": "common"}
                ]}
            ]
        },
        "low_confidence": {
            "$and": [
                {"year_max": {"$lte": 2281}},
                {"content_type": {"$in": ["event", "faction", "location"]}},
                {"info_source": "public"}
            ]
        },
        "prewar_access": {
            "$and": [
                {"pre_war": True},
                {"year_max": {"$lt": 2077}}
            ]
        },
        "narrative_context": {
            "prewar_prefix": [
                "Ah, the old days",
                "Reminds me of a time when",
                "The world that was",
                "In those golden days",
                "Such romance in the lost world",
                "The old world had its charms",
                "In the golden age before the fire",
                "Ah, such elegance in ages past"
            ],
            "rumor_prefix": [
                "Word from the caravans is",
                "The traders speak of",
                "Rumors drift in from afar"
            ]
        }
    }
}
```

### Content Type Filtering Rules

**For Low-Confidence (Rumor) Queries**:
- **Include**: `content_type: ["event", "faction", "location", "character"]`
  - Major happenings travel through wasteland gossip
  - Faction movements are discussed by travelers
  - Significant events become legendary stories
  
- **Exclude**: `content_type: ["item", "technology", "quest"]`
  - Technical specifications don't spread reliably
  - Weapon details require firsthand examination
  - Quest-specific information is too localized

---

## Narrative Framing Requirements

### Julie's Vault-Tec Knowledge
**Trigger**: Any query result with `info_source: "vault-tec"`

**Required Elements**:
1. Discovery language (random selection from templates)
2. Casual, conversational tone matching character
3. Slight uncertainty or amazement ("I think...", "It's wild that...")
4. Personal reaction ("This is crazy...", "I can't believe...")

**Example**:
> "So, I was digging through the old Vault-Tec terminals last night—couldn't sleep, you know how it is—and I found something about Vault 12. Turns out the door was designed to never fully seal. Like, on purpose. That's... that's messed up, right?"

### Mr. New Vegas's Pre-War References
**Trigger**: Any query result with `pre_war: true` or `year_max < 2077`

**Required Elements**:
1. Nostalgic/romantic framing (random selection from templates)
2. Smooth, velvet delivery matching character
3. Consistent tone regardless of how ancient the knowledge
4. No speculation or uncertainty—always confident and wistful

**Example**:
> "Ah, the old world had its charms. The Chryslus Corvega—such elegance in automotive design. They knew how to craft beauty before the fire. Reminds me of a time when the open road meant freedom, not radiation."

### Low-Confidence (Rumor) Content
**Trigger**: Query confidence < 0.5

**Required Elements**:
1. Rumor prefix indicating source uncertainty
2. Qualifier words ("apparently", "supposedly", "I heard")
3. Character-appropriate hedging
4. Optional skepticism or curiosity

**Julie Example**:
> "Heard from a caravan passing through that there's some big faction out west called the NCR? I don't know much about it, but... sounds like they're trying to rebuild civilization or something. That's gotta be good, right?"

**Mr. New Vegas Example**:
> "Word from the caravans is there's trouble brewing in the Capital Wasteland. Something about purified water and noble sacrifices. Such drama, even in the ruins of the world."

---

## Validation & Testing

### Test Cases

#### Julie Temporal Validation
- ✅ Should retrieve: Vault 76, Scorched Plague, Responders (2102 or earlier)
- ❌ Should exclude: NCR expansion (2161), New Vegas events (2281), Commonwealth (2287)

#### Julie Vault-Tec Access
- ✅ Should retrieve with discovery framing: Any vault experiment, Vault-Tec corporate secrets (pre-2102)
- ✅ Should retrieve: Vault 12 door malfunction, Vault 11 sacrifice, Vault 87 FEV (if documented pre-2102)

#### Mr. New Vegas Pre-War Framing
- ✅ Should retrieve with romantic framing: Pre-war corporations, old world culture, lost technology
- ✅ Framing consistency: Same nostalgic tone for 2076 events and 1950s references

#### Cross-Regional Rumor Filtering
- ✅ Should retrieve as rumor: Major faction movements, significant events (content_type: event/faction)
- ❌ Should exclude from rumors: Weapon specifications, quest details (content_type: item/quest)

#### Travis Restricted Access
- ✅ Should retrieve: Commonwealth common knowledge, Brotherhood presence
- ❌ Should exclude: Vault-Tec classified, Institute internal secrets, detailed technical specs

---

## Implementation Checklist

- [ ] Create `dj_knowledge_profiles.py` in `tools/script-generator/`
- [ ] Define DJ_KNOWLEDGE_PROFILES dictionary with all filter configurations
- [ ] Add confidence tier query functions to `generator.py`
- [ ] Implement narrative framing template system
- [ ] Create content_type filtering for rumor queries
- [ ] Add discovery language rotation for Julie's Vault-Tec access
- [ ] Add romantic framing rotation for Mr. New Vegas pre-war content
- [ ] Write validation test suite in `tests/test_dj_knowledge.py`
- [ ] Update character card system prompts with knowledge constraints
- [ ] Document query examples and expected outputs

---

## Future Considerations

### Potential Enhancements
1. **Dynamic confidence scoring**: Adjust rumor confidence based on distance and time delay
2. **Faction relationship modifiers**: DJs aligned with factions get better info from those sources
3. **Knowledge decay**: Older pre-war knowledge degrades over time (lower confidence)
4. **Cross-DJ references**: Mr. New Vegas mentioning Three Dog's broadcasts, etc.
5. **Player interaction**: DJs learn about player actions in their region (game integration)

### Open Questions
1. Should Julie have access to OTHER vault's experiments if Vault-Tec network is connected?
   - **Resolution**: YES - terminal network justifies cross-vault knowledge
   
2. How to handle Mr. New Vegas knowing he's in a simulation/AI without breaking character?
   - **Resolution**: He never acknowledges it; maintains human illusion completely
   
3. Should confident Travis get slightly elevated access compared to nervous Travis?
   - **Consideration**: Confidence doesn't change information sources, only presentation style

---

## Version History

- **v1.0** (2026-01-16): Initial system design with confidence tiers, narrative framing, and DJ profiles
