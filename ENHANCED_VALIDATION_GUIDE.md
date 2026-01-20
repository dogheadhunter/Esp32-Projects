# Enhanced Validation Features - User Guide

## Overview

The validation system has been enhanced with **regional consistency checking**, **character voice consistency validation**, and **continuity-aware LLM validation** to ensure scripts are temporally accurate, regionally appropriate, and maintain consistent character voice across broadcasts.

---

## Table of Contents

1. [Enhanced Rule-Based Validation](#enhanced-rule-based-validation)
2. [Regional Consistency Validation](#regional-consistency-validation)
3. [Character Voice Consistency Validation](#character-voice-consistency-validation)
4. [Enhanced LLM Validation Prompt](#enhanced-llm-validation-prompt)
5. [Usage Examples](#usage-examples)
6. [Integration Guide](#integration-guide)

---

## Enhanced Rule-Based Validation

### New Validation Methods

#### 1. Regional Consistency Validation

**Purpose**: Ensures DJs only reference locations, factions, and events from their home region.

**Method**: `validate_regional_consistency(script, dj_region, dj_name)`

**Supported Regions**:
- **Commonwealth** (2287): Diamond City, Goodneighbor, Institute, Railroad, Minutemen, Brotherhood of Steel
- **Mojave** (2281): New Vegas, Hoover Dam, NCR, Caesar's Legion, Mr. House  
- **Appalachia** (2102): Vault 76, Charleston, Responders, Free States

**Example**:
```python
from validation_rules import ValidationRules

rules = ValidationRules()

# Valid: Commonwealth DJ mentioning local faction
script = "The Minutemen are helping settlers in Sanctuary Hills."
result = rules.validate_regional_consistency(script, "Commonwealth", "Travis Miles")
# result['is_valid'] = True

# Invalid: Commonwealth DJ mentioning Mojave faction
script = "I heard the NCR is moving troops near Hoover Dam."
result = rules.validate_regional_consistency(script, "Commonwealth", "Travis Miles")
# result['is_valid'] = False
# result['issues'] = ["Regional violation: Travis Miles in Commonwealth 
#                      shouldn't know about NCR, Hoover Dam (from other regions)"]
```

**What it Catches**:
- ✓ Cross-region faction references (e.g., Commonwealth DJ mentioning NCR)
- ✓ Cross-region location references (e.g., Mojave DJ mentioning Diamond City)
- ✓ Out-of-timeline events for the region

---

#### 2. Character Voice Consistency Validation

**Purpose**: Validates scripts maintain the DJ's characteristic voice, tone, and personality.

**Method**: `validate_character_voice_consistency(script, character_card)`

**Character Card Requirements**:
```python
character_card = {
    'name': 'Travis Miles (Nervous)',
    'tone': 'nervous, uncertain, conversational',
    'do': [                          # Guidelines DJ MUST follow
        'Use filler words (um, like, you know)',
        'Sound uncertain and hesitant'
    ],
    'dont': [                        # Guidelines DJ MUST NOT violate
        'Sound polished or slick',
        'Be aggressive or confrontational'
    ],
    'catchphrases': [               # Expected phrases (warnings if missing)
        'This is Travis... uh, Miles',
        'Stay safe out there, I guess'
    ]
}
```

**Example**:
```python
from validation_rules import ValidationRules

rules = ValidationRules()

# Valid: Matches nervous character voice
script = "Um, this is Travis... Miles. So, uh, the weather is clear today."
result = rules.validate_character_voice_consistency(script, travis_card)
# result['is_valid'] = True

# Invalid: Violates "don't be polished" guideline
script = "Good evening. The weather today is meticulously perfect."
result = rules.validate_character_voice_consistency(script, travis_card)
# result['is_valid'] = False
# result['issues'] = ["Character violation: guideline 'don't Sound polished 
#                      or slick' violated by using: meticulously"]
```

**What it Catches**:
- ✓ **Critical**: Violations of "don't" guidelines (e.g., using forbidden tone/words)
- ⚠ **Warning**: Missing expected tone markers
- ⚠ **Warning**: Missing catchphrases in longer scripts

**Tone Markers Detected**:
- `hopeful`: hope, believe, together, can do, will
- `earnest`: sincere, honest, true, real, important
- `conversational`: you know, like, um, i mean, think
- `friendly`: friend, folks, buddy, pal, hey
- `protective`: safe, careful, watch out, protect

**"Don't" Violation Patterns**:
- `polished or slick`: meticulously, perfectly, pristine, flawlessly
- `cynical`: hopeless, useless, pointless, never work
- `aggressive`: destroy them, kill them all, crush them
- `formal`: furthermore, henceforth, thus, whereas, hereby

---

#### 3. Improved Temporal Validation

**Enhancement**: Fixed false positives with word boundary detection.

**Old Behavior**: Detected "app" in "Appalachia" as anachronism
**New Behavior**: Uses `\b` word boundaries to avoid partial matches

```python
# Now correctly handles:
"Stay strong, Appalachia!"  # ✓ No longer flags "app" in Appalachia
"Check your app for updates"  # ✗ Correctly flags actual "app" reference
```

---

## Enhanced LLM Validation Prompt

### Key Improvements

The LLM validation prompt has been significantly enhanced to ensure comprehensive checking when using **LLM-only validation**.

#### 1. Structured Validation Task

**Old**: Simple task description
**New**: Explicit priority list

```
Your primary responsibility is to ensure COMPLETE CONSISTENCY with:
1. DJ Character Voice and Personality
2. Temporal Accuracy (timeline and knowledge constraints)
3. Tone and Emotional Consistency
4. Continuity with Previous Broadcast Segments
5. Regional/Location Accuracy
```

#### 2. Enhanced Character Profile

**New Sections**:
- **Voice Characteristics**: Prosody, pace, energy details
- **Signature Catchphrases**: List of expected phrases with examples
- **DO/DON'T Guidelines**: Formatted with ✓ and ✗ for clarity
- **Temporal Constraints**: Highlighted with `═══` separators for emphasis

```
Voice Characteristics:
  - prosody: natural with occasional filler words
  - pace: moderate
  - energy: warm and genuine

Signature Catchphrases (should appear naturally):
  - "Stay strong, Appalachia"
  - "We can do this together"

Character MUST DO:
  ✓ Sound encouraging and optimistic
  ✓ Show concern for listeners

Character MUST NOT DO:
  ✗ Be cynical or hopeless
  ✗ Sound overly formal
```

#### 3. Previous Scripts for Continuity Checking

**New Feature**: Includes up to 3 previous broadcast segments for continuity validation.

```python
context = {
    'previous_scripts': [
        "Good morning, Appalachia! It's a sunny day.",
        "Temperature is rising to 75 degrees.",
    ]
}

# LLM prompt will include:
<previous_broadcast_segments>
IMPORTANT: Validate continuity with these previous segments from the same broadcast:

Segment 1: Good morning, Appalachia! It's a sunny day.
Segment 2: Temperature is rising to 75 degrees.

CHECK FOR:
  - Contradictions in information (weather, events, facts)
  - Inconsistent tone or mood
  - Voice pattern changes
  - Repetition of same information
</previous_broadcast_segments>
```

**What it Catches**:
- ✓ Weather contradictions ("sunny" then "rainy" 5 minutes later)
- ✓ Tone shifts (nervous to confident without explanation)
- ✓ Factual contradictions (temperature changes unrealistically)
- ✓ Excessive repetition of same information

#### 4. Detailed Validation Aspects

Each validation aspect now includes:
- Specific sub-checks to perform
- Expected severity levels
- Clear criteria for each category

**Example - Character Consistency**:
```
Character Voice Consistency:
  • Does the speech pattern match the DJ's personality?
  • Are characteristic filler words/phrases present?
  • Are catchphrases used naturally (if expected)?
  • Does vocabulary match education/background?
  • Are 'DO' guidelines followed?
  • Are 'DON'T' guidelines avoided?
  SEVERITY: CRITICAL for guideline violations, WARNING for voice drift
```

#### 5. Enhanced JSON Response Format

**New Field**: `evidence` - requires LLM to quote the problematic text

```json
{
  "overall_score": 0.85,
  "is_valid": true,
  "issues": [
    {
      "severity": "critical",
      "category": "temporal",
      "message": "DJ references events after knowledge cutoff",
      "evidence": "I heard the Institute was discovered in 2287",  // NEW
      "suggestion": "Remove reference to post-2102 events",
      "confidence": 0.95
    }
  ],
  "feedback": "Overall assessment"
}
```

**Benefits**:
- Makes issues more specific and actionable
- Prevents LLM hallucination (must quote actual text)
- Easier to verify and debug validation results

#### 6. Critical Rules Emphasis

**New Section** at end of prompt:
```
CRITICAL RULES:
• Include 'evidence' - quote the exact part of the script with the issue
• Be specific in 'message' - explain WHY it's a problem
• Empty issues array is fine if script is perfect
• Only report ACTUAL problems, not nitpicks
• Temporal and forbidden knowledge violations are ALWAYS critical
• Character guideline violations are ALWAYS critical
```

---

## Usage Examples

### Example 1: Comprehensive Validation with All Features

```python
from validation_rules import ValidationRules

rules = ValidationRules()

character_card = {
    'name': 'Julie',
    'tone': 'hopeful, protective',
    'do': ['Be encouraging', 'Show concern for listeners'],
    'dont': ['Be cynical', 'Sound overly formal'],
    'catchphrases': ['Stay strong, Appalachia', 'We can do this together']
}

script = """
Good morning, Appalachia! This is Julie, coming to you from Vault 76.
The weather today in 2102 is looking clear and beautiful. 
Stay strong out there, everyone. We can do this together!
"""

result = rules.validate_all(
    script=script,
    max_year=2102,
    forbidden_topics=['Institute', 'Railroad'],
    forbidden_factions=['NCR', 'Caesar\'s Legion'],
    max_length=500,
    dj_name='Julie',
    dj_region='Appalachia',
    character_card=character_card
)

print(f"Valid: {result['is_valid']}")
print(f"Issues: {result['issues']}")
print(f"Warnings: {result['warnings']}")

# Output:
# Valid: True
# Issues: []
# Warnings: []
```

### Example 2: LLM-Only Validation with Continuity

```python
from llm_validator import LLMValidator

validator = LLMValidator()

character_card = {
    'name': 'Julie',
    'tone': 'hopeful, earnest, protective',
    'do': ['Sound encouraging', 'Show concern'],
    'dont': ['Be cynical', 'Sound formal'],
    'catchphrases': ['Stay strong, Appalachia'],
    'voice': {
        'prosody': 'natural with filler words',
        'pace': 'moderate'
    },
    'knowledge_constraints': {
        'temporal_cutoff_year': 2102,
        'region': 'Appalachia',
        'forbidden_factions': ['NCR', 'Institute'],
        'forbidden_topics': ['New Vegas', 'Commonwealth']
    }
}

context = {
    'current_hour': 9,
    'weather': 'sunny',
    'previous_scripts': [
        "Good morning! It's a beautiful sunny day in Appalachia.",
        "Temperature is about 75 degrees this morning.",
    ]
}

current_script = """
And now, the weather update. As I mentioned, it's sunny today.
Expected to stay around 75 degrees through the afternoon.
Stay hydrated out there!
"""

# Validate with continuity checking
result = validator.validate(
    script=current_script,
    character_card=character_card,
    context=context,
    validation_aspects=['temporal', 'character', 'tone', 'lore', 'continuity']
)

print(result.to_dict())
```

### Example 3: Detecting Regional Violations

```python
from validation_rules import ValidationRules

rules = ValidationRules()

# Commonwealth DJ (2287)
script = """
Breaking news from the Commonwealth! 
I heard the NCR is moving troops through California.
The Institute has been making moves in the Mojave.
"""

result = rules.validate_regional_consistency(
    script=script,
    dj_region='Commonwealth',
    dj_name='Travis Miles'
)

print(f"Valid: {result['is_valid']}")
print(f"Issues: {result['issues']}")

# Output:
# Valid: False
# Issues: [
#   "Regional violation: Travis Miles in Commonwealth shouldn't know 
#    about NCR, Institute, Mojave (from other regions)"
# ]
```

---

## Integration Guide

### Integrating into Broadcast Pipeline

**Step 1**: Add regional and character card info to DJ context

```python
dj_context = {
    'name': 'Julie',
    'year': 2102,
    'region': 'Appalachia',  # NEW
    'character_card': {      # NEW
        'name': 'Julie',
        'tone': 'hopeful, protective',
        'do': ['Be encouraging'],
        'dont': ['Be cynical'],
        'catchphrases': ['Stay strong, Appalachia']
    }
}
```

**Step 2**: Pass previous scripts in context for continuity

```python
# In broadcast engine
class BroadcastEngine:
    def __init__(self):
        self.session_scripts = []  # Track scripts in current broadcast
    
    def validate_script(self, script, segment_type):
        context = {
            'segment_type': segment_type,
            'previous_scripts': self.session_scripts[-3:]  # Last 3 scripts
        }
        
        result = validator.validate(
            script=script,
            character_card=self.dj_context['character_card'],
            context=context
        )
        
        if result.is_valid:
            self.session_scripts.append(script)  # Add to session history
        
        return result
```

**Step 3**: Use comprehensive validation in generation loop

```python
from validation_rules import ValidationRules

def generate_validated_script(prompt, character_card, dj_region):
    """Generate script with comprehensive validation."""
    rules = ValidationRules()
    
    # Generate script
    script = ollama.generate(model, prompt)
    
    # Validate with all rules
    result = rules.validate_all(
        script=script,
        max_year=character_card['knowledge_constraints']['temporal_cutoff_year'],
        forbidden_topics=character_card['knowledge_constraints']['forbidden_topics'],
        forbidden_factions=character_card['knowledge_constraints']['forbidden_factions'],
        dj_name=character_card['name'],
        dj_region=dj_region,
        character_card=character_card
    )
    
    if not result['is_valid']:
        # Log issues and regenerate
        print(f"Validation failed: {result['issues']}")
        return None  # Trigger regeneration
    
    if result['warnings']:
        # Log warnings but accept script
        print(f"Warnings: {result['warnings']}")
    
    return script
```

---

## Testing

Run the comprehensive test suite:

```bash
python test_enhanced_validation.py
```

**Test Coverage**:
- ✓ Regional consistency validation
- ✓ Character voice consistency validation
- ✓ Enhanced LLM prompt generation
- ✓ Comprehensive validation with all features
- ✓ False positive prevention (e.g., "app" in "Appalachia")

**Expected Output**:
```
======================================================================
ENHANCED VALIDATION TESTING
======================================================================
...
======================================================================
ALL TESTS COMPLETED SUCCESSFULLY!
======================================================================
```

---

## Summary of Improvements

### What's New

1. **Regional Consistency Validation**
   - Prevents cross-region knowledge violations
   - Supports Commonwealth, Mojave, Appalachia regions
   - Catches faction/location references from other regions

2. **Character Voice Consistency Validation**
   - Validates "do" and "don't" guidelines  
   - Checks for expected tone markers
   - Warns about missing catchphrases
   - Detects violations like overly formal language

3. **Enhanced LLM Validation**
   - Includes previous scripts for continuity checking
   - Requires evidence quotes in issue reports
   - Detailed validation aspects with severity guidance
   - Catchphrases and voice characteristics in prompt

4. **Improved Temporal Validation**
   - Word boundary detection prevents false positives
   - Better anachronism detection

### What It Prevents

- ✓ Cross-region knowledge violations (Commonwealth DJ mentioning NCR)
- ✓ Temporal violations (DJ knowing future events)
- ✓ Character voice drift (formal language for casual DJ)
- ✓ Guideline violations (doing things in "don't" list)
- ✓ Continuity errors (contradicting previous statements)
- ✓ Tone inconsistencies across segments
- ✓ Missing expected catchphrases
- ✓ Regional inaccuracies

---

## Next Steps

1. **Add to character cards**: Include `catchphrases` and `voice` fields
2. **Track session scripts**: Store previous scripts for continuity validation
3. **Configure regions**: Set `dj_region` in character configurations
4. **Test thoroughly**: Run validation tests on your actual broadcasts
5. **Monitor warnings**: Review warnings to improve script quality

For questions or issues, see `VALIDATION_IMPROVEMENT_SUGGESTIONS.md` for detailed improvement suggestions and implementation guidance.
