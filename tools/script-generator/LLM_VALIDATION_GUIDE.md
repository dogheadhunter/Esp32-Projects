# LLM-Based Script Validation

## Overview

The script validation system has been enhanced to use LLM-based validation in addition to traditional rule-based checks. This provides intelligent, context-aware validation tailored for LLM-generated scripts.

## Why LLM Validation?

### Advantages of LLM Validation
- **Context Understanding**: LLMs can understand nuanced context and narrative flow
- **Quality Assessment**: Can evaluate writing quality, engagement, and naturalness
- **Soft Constraints**: Better at evaluating tone, voice, and style consistency
- **Adaptive**: Can consider multiple factors simultaneously and weigh trade-offs

### Advantages of Rule-Based Validation
- **Speed**: Much faster than LLM calls
- **Deterministic**: Always produces same results for same input
- **Hard Constraints**: Perfect for checking facts (dates, factions, locations)
- **No API Required**: Works offline without Ollama

### Hybrid Approach (Recommended)
The hybrid validator combines both approaches:
1. **Fast rule-based checks** catch hard constraint violations (dates, forbidden topics)
2. **LLM validation** assesses quality, tone, and context-awareness
3. **Combined results** provide comprehensive validation

## Architecture

### Components

```
llm_validator.py
├── ValidationSeverity (Enum)
│   ├── CRITICAL - Must fix, breaks lore/character
│   ├── WARNING - Should fix, quality/consistency issue
│   └── SUGGESTION - Nice to have, minor improvement
│
├── ValidationIssue (Dataclass)
│   ├── severity: ValidationSeverity
│   ├── category: str (lore, character, temporal, quality, tone)
│   ├── message: str
│   ├── suggestion: Optional[str]
│   ├── source: str (llm or rule)
│   └── confidence: float (0.0-1.0)
│
├── ValidationResult (Dataclass)
│   ├── is_valid: bool
│   ├── script: str
│   ├── issues: List[ValidationIssue]
│   ├── llm_feedback: Optional[str]
│   └── overall_score: Optional[float]
│
├── LLMValidator
│   ├── validate() - Main validation method
│   ├── quick_validate() - Faster validation for iteration
│   └── _build_validation_prompt() - Builds structured prompts
│
├── HybridValidator
│   ├── validate() - Combines LLM + rule-based validation
│   └── _run_rule_based_validation() - Rule checks
│
└── validate_script() - Convenience function
```

## Usage

### 1. Basic LLM Validation

```python
from llm_validator import LLMValidator
from personality_loader import load_personality

# Initialize validator
validator = LLMValidator(
    model="fluffy/l3-8b-stheno-v3.2",
    temperature=0.1  # Low temp for consistent validation
)

# Load character card
character_card = load_personality("Julie (2102, Appalachia)")

# Validate a script
script = "Happy to have you with us! Weather's sunny today."

result = validator.validate(
    script=script,
    character_card=character_card,
    context={"weather": "sunny", "time_of_day": "morning"}
)

# Check results
if result.is_valid:
    print("✅ Script is valid!")
else:
    print(f"❌ Found {len(result.get_critical_issues())} critical issues")
    for issue in result.get_critical_issues():
        print(f"  - {issue.message}")
```

### 2. Hybrid Validation (Recommended)

```python
from llm_validator import HybridValidator

# Initialize hybrid validator
validator = HybridValidator(
    use_llm=True,
    use_rules=True
)

# Validate with both approaches
result = validator.validate(
    script=script,
    character_card=character_card,
    context={"weather": "sunny"}
)

# Get detailed breakdown
result_dict = result.to_dict()
print(f"Valid: {result_dict['is_valid']}")
print(f"Score: {result_dict['overall_score']}")
print(f"Critical: {result_dict['summary']['critical']}")
print(f"Warnings: {result_dict['summary']['warnings']}")
print(f"Suggestions: {result_dict['summary']['suggestions']}")
```

### 3. Integrated with Script Generator

```python
from generator import ScriptGenerator

generator = ScriptGenerator()

# Generate with automatic LLM validation
result = generator.generate_and_validate(
    script_type="weather",
    dj_name="Julie (2102, Appalachia)",
    context_query="Appalachia weather sunny conditions",
    validation_strategy="hybrid",  # "llm", "rules", or "hybrid"
    max_validation_retries=3,
    weather_type="sunny",
    time_of_day="morning",
    hour=8
)

# Check validation results
validation = result["validation"]
if validation["is_valid"]:
    print("✅ Generated and validated!")
else:
    print("⚠️ Script has issues:")
    for issue in validation["issues"]:
        print(f"  [{issue['severity']}] {issue['message']}")
```

### 4. Convenience Function

```python
from llm_validator import validate_script

# Quick validation with strategy choice
result = validate_script(
    script="Your script here...",
    character_card=character_card,
    context={"weather": "rainy"},
    strategy="hybrid"  # "llm", "rules", or "hybrid"
)

result_dict = result.to_dict()
```

## Validation Aspects

The LLM validator checks five key aspects:

### 1. Lore Accuracy
- Does the script fit Fallout canon?
- Are faction relationships correct?
- Are location references accurate?
- Do events align with the timeline?

### 2. Character Consistency
- Does it match the DJ's personality?
- Is the voice authentic to the character?
- Are catchphrases used appropriately?
- Does it follow character guidelines (do/don't)?

### 3. Temporal Consistency
- Does it respect timeline constraints?
- No future knowledge (DJ can't know events after their year)
- No references to unknown factions/locations
- Proper use of past/present/future tense

### 4. Quality
- Is it well-written and engaging?
- Natural dialogue flow
- Appropriate length
- Good pacing and variety

### 5. Tone Appropriateness
- Matches expected mood (weather, time, context)
- Consistent with character tone
- Appropriate for script type (news vs gossip vs weather)

## Validation Strategies

### Strategy: "llm"
**Use When**: Quality and nuance matter most
- Slow (~10-30 seconds per validation)
- Context-aware assessment
- Evaluates all five aspects
- Best for final validation or review

**Example**:
```python
result = generator.validate_script_with_llm(
    script=script,
    character_card=character_card,
    strategy="llm"
)
```

### Strategy: "rules"
**Use When**: Speed matters, hard constraints only
- Fast (<1 second per validation)
- Checks temporal violations, forbidden topics
- Deterministic results
- Best for iteration loops

**Example**:
```python
result = generator.validate_script_with_llm(
    script=script,
    character_card=character_card,
    strategy="rules"
)
```

### Strategy: "hybrid" (Recommended)
**Use When**: You want comprehensive validation
- Medium speed (~10-30 seconds, rule checks are negligible)
- Combines hard constraints + quality assessment
- Best of both worlds
- Default for production use

**Example**:
```python
result = generator.validate_script_with_llm(
    script=script,
    character_card=character_card,
    strategy="hybrid"
)
```

## Validation Workflow

### Typical Workflow with Retries

```python
from generator import ScriptGenerator

generator = ScriptGenerator()

# This handles validation automatically with retries
result = generator.generate_and_validate(
    script_type="news",
    dj_name="Julie (2102, Appalachia)",
    context_query="Appalachia Responders settlement",
    validation_strategy="hybrid",
    max_validation_retries=3,  # Retry up to 3 times
    news_topic="settlement cooperation",
    faction="Responders"
)

# Result includes both script and validation
script = result["script"]
validation = result["validation"]
metadata = result["metadata"]
```

### Manual Validation Loop

```python
from generator import ScriptGenerator

generator = ScriptGenerator()

max_attempts = 3
for attempt in range(max_attempts):
    # Generate script
    result = generator.generate_script(
        script_type="weather",
        dj_name="Julie (2102, Appalachia)",
        context_query="Appalachia weather",
        weather_type="sunny"
    )
    
    script = result["script"]
    
    # Validate
    validation = generator.validate_script_with_llm(
        script=script,
        character_card=generator.personality_loader.load_personality(
            "Julie (2102, Appalachia)"
        ),
        strategy="hybrid"
    )
    
    # Check if valid
    if validation["is_valid"]:
        print(f"✅ Success on attempt {attempt + 1}")
        break
    
    # Show issues
    critical = validation["summary"]["critical"]
    if critical > 0:
        print(f"❌ Attempt {attempt + 1}: {critical} critical issues")
        for issue in validation["issues"]:
            if issue["severity"] == "critical":
                print(f"  - {issue['message']}")
    else:
        print(f"✅ No critical issues, accepting script")
        break
```

## Validation Prompt Structure

The LLM validator uses a structured prompt format:

```
<validation_task>
You are an expert validator for Fallout radio scripts.
Analyze the following script and identify any issues.
</validation_task>

<character_profile>
DJ Name: Julie (2102, Appalachia)
Tone: hopeful, earnest
DO Guidelines:
  - Use filler words like 'um' and 'you know'
  - Be authentic and vulnerable
DON'T Guidelines:
  - Don't be polished or slick
  - Don't be cynical

Temporal Constraint: DJ only knows events up to year 2102
Forbidden Factions: NCR, Institute
Forbidden Topics: synths, west coast
</character_profile>

<context>
weather: sunny
time_of_day: morning
</context>

<script_to_validate>
[Script text here]
</script_to_validate>

<validation_instructions>
Analyze the script for the following aspects:
  - Lore Accuracy - Does it fit Fallout canon?
  - Character Consistency - Does it match the DJ's personality?
  - Temporal Consistency - Does it respect timeline constraints?
  - Quality - Is it well-written and engaging?
  - Tone - Does it match the expected mood and context?

Respond in JSON format with:
{
  "overall_score": 0.0-1.0,
  "is_valid": true/false,
  "issues": [...],
  "feedback": "Brief overall feedback"
}
</validation_instructions>
```

## Response Parsing

The validator handles two response formats:

### JSON Response (Preferred)
```json
{
  "overall_score": 0.85,
  "is_valid": true,
  "issues": [
    {
      "severity": "warning",
      "category": "character",
      "message": "Could use more filler words",
      "suggestion": "Add 'um' or 'you know'",
      "confidence": 0.8
    }
  ],
  "feedback": "Good script with minor character voice improvement needed"
}
```

### Text Response (Fallback)
If LLM doesn't return JSON, the validator uses keyword detection:
- Looks for severity indicators: "critical", "warning", "issue"
- Detects categories: "temporal", "lore", "character", "quality"
- Determines validity from: "valid", "good", "acceptable", "pass"

## Integration with Existing Validators

The LLM validator integrates with existing rule-based validators:

```python
# Existing validators still work
from consistency_validator import ConsistencyValidator
from lore_validator import LoreValidator
from timeline_validator import TimelineValidator

# LLM validator can wrap them
from llm_validator import HybridValidator

hybrid = HybridValidator(
    use_llm=True,
    use_rules=True  # Uses ConsistencyValidator internally
)

# Or use them separately
consistency = ConsistencyValidator(character_card)
is_valid_rules = consistency.validate(script)

llm = LLMValidator()
result_llm = llm.validate(script, character_card)

# Combine results manually
all_issues = consistency.get_violations() + result_llm.issues
```

## Configuration

### LLM Validator Options

```python
validator = LLMValidator(
    ollama_client=None,  # Provide custom client or use default
    model="fluffy/l3-8b-stheno-v3.2",  # Model for validation
    temperature=0.1,  # Low = more consistent (0.0-1.0)
    templates_dir=None  # Custom template directory (future use)
)
```

### Validation Options

```python
result = validator.validate(
    script=script,
    character_card=character_card,
    context={  # Optional context
        "weather": "sunny",
        "time_of_day": "morning",
        "topic": "settlement news"
    },
    validation_aspects=[  # Specify which aspects to check
        "lore",
        "character",
        "temporal",
        "quality",
        "tone"
    ]
)
```

## Best Practices

### 1. Choose the Right Strategy
- **Development/Iteration**: Use "rules" for speed
- **Final Review**: Use "llm" for quality
- **Production**: Use "hybrid" for comprehensive validation

### 2. Set Appropriate Retries
```python
# Quick iteration
max_validation_retries=1

# Production quality
max_validation_retries=3

# Maximum quality (slow)
max_validation_retries=5
```

### 3. Log Validation Results
```python
import json

result = generator.generate_and_validate(...)

# Save validation logs
with open("validation_log.jsonl", "a") as f:
    log_entry = {
        "timestamp": result["metadata"]["timestamp"],
        "dj": result["metadata"]["dj_name"],
        "validation": result["validation"]
    }
    f.write(json.dumps(log_entry) + "\n")
```

### 4. Monitor Validation Metrics
```python
# Track validation pass rate
total = 0
passed = 0

for script_data in scripts:
    validation = validate_script(
        script_data["script"],
        script_data["character_card"],
        strategy="hybrid"
    )
    
    total += 1
    if validation.is_valid:
        passed += 1

pass_rate = (passed / total) * 100
print(f"Validation pass rate: {pass_rate:.1f}%")
```

### 5. Handle Validation Failures Gracefully
```python
result = generator.generate_and_validate(
    ...,
    max_validation_retries=3
)

validation = result["validation"]

if not validation["is_valid"]:
    # Log for review
    critical_issues = [
        i for i in validation["issues"]
        if i["severity"] == "critical"
    ]
    
    if critical_issues:
        # Manual review needed
        log_for_review(result)
    else:
        # Only warnings, can use script
        use_script_with_caution(result)
```

## Testing

Run the LLM validator tests:

```bash
cd tools/script-generator
python tests/test_llm_validator.py
```

Tests cover:
- ValidationIssue and ValidationResult creation
- LLMValidator initialization
- Prompt building
- JSON response parsing
- Text fallback parsing
- Hybrid validation
- Integration tests (requires Ollama)

## Performance

### Speed Comparison
| Strategy | Speed | Use Case |
|----------|-------|----------|
| rules    | <1s   | Iteration, development |
| llm      | 10-30s | Quality review, final check |
| hybrid   | 10-30s | Production (comprehensive) |

### Resource Usage
- **LLM Validation**: ~4.5GB VRAM (same model as generation)
- **Rule Validation**: Negligible (<10MB RAM)
- **Hybrid**: Same as LLM (rules are negligible)

### Optimization Tips
1. Use `quick_validate()` for faster LLM validation
2. Cache validation results for identical scripts
3. Run rule checks first, skip LLM if rules fail
4. Batch validate multiple scripts to amortize model load time

## Future Enhancements

Potential improvements to the validation system:

1. **Custom Validation Templates**: Allow users to provide custom validation prompts
2. **Validation Metrics Dashboard**: Track validation statistics over time
3. **A/B Testing**: Compare validation strategies empirically
4. **Fine-tuned Validation Model**: Train a specialized model for validation
5. **Confidence Calibration**: Improve confidence scoring accuracy
6. **Multi-Model Validation**: Use different models for different aspects
7. **Validation Caching**: Cache results for similar scripts

## Troubleshooting

### "LLM validation failed"
- Check Ollama is running: `ollama serve`
- Verify model is available: `ollama list`
- Check connectivity: Test with `ollama_client.py`

### "JSON parsing failed"
- Validation falls back to text parsing automatically
- If this happens frequently, adjust validation prompt
- Consider using a different model (some are better at JSON)

### Validation too slow
- Use "rules" strategy for faster iteration
- Reduce `validation_aspects` to only critical ones
- Use `quick_validate()` method

### Too many false positives
- Adjust validation prompt to be less strict
- Lower the threshold for critical issues
- Use confidence scores to filter low-confidence issues

### Too many false negatives
- Use "hybrid" strategy to catch more issues
- Increase LLM temperature slightly (0.2-0.3)
- Add more specific validation aspects

## Examples

See `/tools/script-generator/tests/test_llm_validator.py` for complete examples.
