# Migration Guide: Rule-Based to LLM-Based Validation

## Overview

This guide helps you transition from the existing rule-based validation system to the new LLM-based validation approach.

## What Changed?

### Before (Rule-Based Only)
```python
from consistency_validator import ConsistencyValidator

validator = ConsistencyValidator(character_card)
is_valid = validator.validate(script)

if not is_valid:
    print("Violations:", validator.get_violations())
    print("Warnings:", validator.get_warnings())
```

### After (LLM-Based or Hybrid)
```python
from llm_validator import HybridValidator

validator = HybridValidator()
result = validator.validate(script, character_card, context)

if not result.is_valid:
    for issue in result.get_critical_issues():
        print(f"Critical: {issue.message}")
```

## Migration Paths

### Option 1: Keep Using Rule-Based (No Migration Needed)
If you're happy with rule-based validation, **nothing changes**:

```python
# Still works exactly as before
from consistency_validator import ConsistencyValidator

validator = ConsistencyValidator(character_card)
is_valid = validator.validate(script)
```

**When to choose**: Speed matters, you only need hard constraints checked

### Option 2: Add LLM Validation (Recommended)
Add LLM validation alongside existing rules:

```python
from llm_validator import HybridValidator

# Uses both rule-based AND LLM validation
validator = HybridValidator(use_llm=True, use_rules=True)
result = validator.validate(script, character_card, context)
```

**When to choose**: Production use, comprehensive validation needed

### Option 3: LLM Only
Use only LLM validation:

```python
from llm_validator import LLMValidator

# Uses only LLM validation (slower but more nuanced)
validator = LLMValidator()
result = validator.validate(script, character_card, context)
```

**When to choose**: Quality matters most, willing to wait for LLM

## Step-by-Step Migration

### Step 1: Install/Update (No Additional Dependencies)
The LLM validator uses existing Ollama setup - no new dependencies needed!

```bash
# Verify Ollama is running
ollama serve

# Verify model is available
ollama list
```

### Step 2: Update Import Statements

**Old:**
```python
from consistency_validator import ConsistencyValidator
```

**New (Hybrid):**
```python
from llm_validator import HybridValidator
# or
from llm_validator import validate_script  # convenience function
```

### Step 3: Update Validation Calls

**Old:**
```python
validator = ConsistencyValidator(character_card)
is_valid = validator.validate(script)

if not is_valid:
    violations = validator.get_violations()
    warnings = validator.get_warnings()
```

**New:**
```python
# Option A: Using HybridValidator
validator = HybridValidator()
result = validator.validate(script, character_card)

if not result.is_valid:
    critical = result.get_critical_issues()
    warnings = result.get_warnings()

# Option B: Using convenience function
result = validate_script(script, character_card, strategy="hybrid")
result_dict = result.to_dict()
```

### Step 4: Update Error Handling

**Old:**
```python
try:
    is_valid = validator.validate(script)
    if not is_valid:
        # Handle violations
        for v in validator.get_violations():
            print(f"Error: {v}")
except Exception as e:
    print(f"Validation failed: {e}")
```

**New:**
```python
try:
    result = validator.validate(script, character_card)
    
    if not result.is_valid:
        # Handle by severity
        for issue in result.get_critical_issues():
            print(f"Critical: {issue.message}")
        
        for issue in result.get_warnings():
            print(f"Warning: {issue.message}")
        
        for issue in result.get_suggestions():
            print(f"Suggestion: {issue.message}")
            
except Exception as e:
    print(f"Validation failed: {e}")
```

### Step 5: Update Result Processing

**Old:**
```python
# Boolean result
is_valid = validator.validate(script)

# Get details
violations = validator.get_violations()  # List[str]
warnings = validator.get_warnings()      # List[str]
report = validator.get_report()          # str
```

**New:**
```python
# Rich result object
result = validator.validate(script, character_card)

# Access results
is_valid = result.is_valid              # bool
overall_score = result.overall_score    # Optional[float] (0.0-1.0)
issues = result.issues                  # List[ValidationIssue]
feedback = result.llm_feedback          # Optional[str]

# Get by severity
critical = result.get_critical_issues()  # List[ValidationIssue]
warnings = result.get_warnings()         # List[ValidationIssue]
suggestions = result.get_suggestions()   # List[ValidationIssue]

# Convert to dict for JSON/logging
result_dict = result.to_dict()
```

## Common Migration Scenarios

### Scenario 1: Script Generation with Validation

**Before:**
```python
from generator import ScriptGenerator
from consistency_validator import ConsistencyValidator

generator = ScriptGenerator()
result = generator.generate_script(
    script_type="weather",
    dj_name="Julie (2102, Appalachia)",
    context_query="Appalachia weather",
    enable_consistency_validation=True  # Uses rules internally
)

# Manual validation
script = result["script"]
validator = ConsistencyValidator(character_card)
is_valid = validator.validate(script)
```

**After:**
```python
from generator import ScriptGenerator

generator = ScriptGenerator()

# Automatic LLM validation with retry
result = generator.generate_and_validate(
    script_type="weather",
    dj_name="Julie (2102, Appalachia)",
    context_query="Appalachia weather",
    validation_strategy="hybrid",  # LLM + rules
    max_validation_retries=3
)

# Validation results included
validation = result["validation"]
```

### Scenario 2: Batch Validation

**Before:**
```python
validator = ConsistencyValidator(character_card)

for script in scripts:
    is_valid = validator.validate(script)
    if not is_valid:
        print(f"Invalid: {validator.get_violations()}")
```

**After:**
```python
from llm_validator import validate_script

for script in scripts:
    result = validate_script(
        script, 
        character_card,
        strategy="hybrid"  # or "rules" for speed
    )
    
    if not result.is_valid:
        critical = result.get_critical_issues()
        print(f"Invalid: {len(critical)} critical issues")
```

### Scenario 3: Custom Validation Loop

**Before:**
```python
validator = ConsistencyValidator(character_card)

max_retries = 3
for attempt in range(max_retries):
    script = generate_script()
    
    if validator.validate(script):
        break
    
    print(f"Retry {attempt + 1}: {validator.get_violations()}")
```

**After:**
```python
from llm_validator import LLMValidator

validator = LLMValidator()

max_retries = 3
for attempt in range(max_retries):
    script = generate_script()
    
    result = validator.validate(script, character_card)
    
    if result.is_valid:
        print(f"Success! Score: {result.overall_score}")
        break
    
    critical = len(result.get_critical_issues())
    print(f"Retry {attempt + 1}: {critical} critical issues")
```

## Backward Compatibility

### All Old Code Still Works
The existing validators are **not deprecated**:

```python
# These still work unchanged
from consistency_validator import ConsistencyValidator
from lore_validator import LoreValidator
from timeline_validator import TimelineValidator

# Use them as before
validator = ConsistencyValidator(character_card)
is_valid = validator.validate(script)
```

### Hybrid Validator Uses Old Validators
The hybrid validator actually **uses** the old validators internally:

```python
from llm_validator import HybridValidator

hybrid = HybridValidator(
    use_llm=True,
    use_rules=True  # Uses ConsistencyValidator internally
)

# Gets both rule-based AND LLM issues
result = hybrid.validate(script, character_card)

# Check which source found each issue
for issue in result.issues:
    print(f"[{issue.source}] {issue.message}")
    # issue.source is either "llm" or "rule"
```

## Testing Your Migration

### 1. Test with Rules Only
Start by testing with rule-based strategy to verify nothing broke:

```python
from llm_validator import validate_script

result = validate_script(
    script,
    character_card,
    strategy="rules"  # Same as old ConsistencyValidator
)

# Should produce same results as before
assert result.is_valid == old_is_valid
```

### 2. Add LLM Validation Gradually
Once rules work, enable LLM:

```python
# Start with LLM only
result_llm = validate_script(script, character_card, strategy="llm")

# Then try hybrid
result_hybrid = validate_script(script, character_card, strategy="hybrid")

# Compare results
print(f"LLM only: {result_llm.is_valid}")
print(f"Hybrid: {result_hybrid.is_valid}")
```

### 3. Run Tests
```bash
# Test old validators (should still pass)
python tests/test_phase2_consistency_validator.py

# Test new LLM validator
python tests/test_llm_validator.py
```

## Performance Considerations

### Speed Comparison

| Approach | Speed | Use Case |
|----------|-------|----------|
| Old (rules only) | <1s | Development, iteration |
| New (rules only) | <1s | Same as old, new interface |
| New (LLM only) | 10-30s | Quality review |
| New (hybrid) | 10-30s | Production |

### Memory Usage

| Approach | VRAM | RAM |
|----------|------|-----|
| Old (rules) | 0 | <10MB |
| New (rules) | 0 | <10MB |
| New (LLM) | 4.5GB | <100MB |
| New (hybrid) | 4.5GB | <100MB |

### When to Use Each

**Use rules-only when:**
- Iterating quickly during development
- Running batch validations (thousands of scripts)
- VRAM is constrained (other processes using GPU)
- Ollama is not available

**Use LLM when:**
- Doing final quality review
- Need nuanced quality assessment
- Have time for slower validation
- Want natural language feedback

**Use hybrid when:**
- Production validation
- Want comprehensive checks
- Can afford 10-30s per validation
- Need both hard constraints and quality

## Troubleshooting Migration

### "ImportError: No module named llm_validator"
Make sure you're running from the correct directory:
```bash
cd tools/script-generator
python your_script.py
```

### "Ollama connection failed"
LLM validation requires Ollama. Options:
1. Start Ollama: `ollama serve`
2. Use rules-only: `strategy="rules"`
3. Disable LLM in hybrid: `HybridValidator(use_llm=False)`

### "Validation is too slow"
LLM validation takes 10-30 seconds. Options:
1. Use rules-only for iteration: `strategy="rules"`
2. Reduce validation aspects: Only check critical aspects
3. Use quick_validate(): Faster LLM method

### "Different results from old validator"
This is expected! LLM validation is more nuanced:
- May catch issues rules missed (quality, tone, context)
- May miss hard constraint violations (prefer hybrid)
- Provides confidence scores and suggestions

Use hybrid strategy to get benefits of both.

### "How do I log validation results?"
New format is more structured:

```python
import json

result = validate_script(script, character_card, strategy="hybrid")

# Convert to dict for logging
log_entry = {
    "timestamp": datetime.now().isoformat(),
    "script": script,
    "validation": result.to_dict()
}

# Save to file
with open("validation_log.jsonl", "a") as f:
    f.write(json.dumps(log_entry) + "\n")
```

## Best Practices for Migration

### 1. Start with Hybrid Strategy
The hybrid approach is usually the best default:
```python
validate_script(script, character_card, strategy="hybrid")
```

### 2. Keep Old Code During Transition
Run both validators in parallel during migration:
```python
# Old
old_validator = ConsistencyValidator(character_card)
old_valid = old_validator.validate(script)

# New
new_result = validate_script(script, character_card, strategy="rules")

# Compare
assert old_valid == new_result.is_valid
```

### 3. Log Validation Differences
Track when LLM finds issues that rules didn't:
```python
rule_result = validate_script(script, character_card, strategy="rules")
llm_result = validate_script(script, character_card, strategy="llm")

if rule_result.is_valid and not llm_result.is_valid:
    print("LLM found issues rules missed:")
    for issue in llm_result.get_critical_issues():
        print(f"  - {issue.message}")
```

### 4. Use Appropriate Retries
Adjust retries based on strategy:
```python
# Rules: No need for many retries (deterministic)
generate_and_validate(..., validation_strategy="rules", max_validation_retries=1)

# LLM: More retries can help (non-deterministic)
generate_and_validate(..., validation_strategy="llm", max_validation_retries=3)

# Hybrid: Balance speed and quality
generate_and_validate(..., validation_strategy="hybrid", max_validation_retries=2)
```

## Migration Checklist

- [ ] Read this migration guide
- [ ] Review LLM_VALIDATION_GUIDE.md
- [ ] Test rule-based validation still works
- [ ] Run old validator tests (verify no regression)
- [ ] Try LLM validation on sample scripts
- [ ] Run new LLM validator tests
- [ ] Update code to use new validators (gradually)
- [ ] Test hybrid validation
- [ ] Update logging/monitoring for new result format
- [ ] Update documentation/comments
- [ ] Train team on new validation options
- [ ] Monitor validation performance in production

## Getting Help

- **Documentation**: See `LLM_VALIDATION_GUIDE.md`
- **Examples**: Check `tests/test_llm_validator.py`
- **Old validators**: See `consistency_validator.py`, `lore_validator.py`
- **Issues**: File GitHub issue with validation logs

## Summary

The migration is **optional** and **backward compatible**:
- Old rule-based validators still work
- New LLM validators provide additional capabilities
- Hybrid approach combines both for best results
- Choose the strategy that fits your use case
