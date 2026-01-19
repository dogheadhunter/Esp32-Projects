"""
LLM-Based Script Validator

Uses Ollama to validate LLM-generated scripts with intelligent, context-aware checks.
Provides both standalone LLM validation and hybrid (LLM + rule-based) validation.

Design Philosophy:
- LLMs are better at understanding context, nuance, and natural language quality
- Rule-based validators catch hard constraints (dates, factions, locations)
- Hybrid approach provides best of both worlds
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from ollama_client import OllamaClient


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    CRITICAL = "critical"  # Must fix - breaks lore/character
    WARNING = "warning"    # Should fix - quality/consistency issue
    SUGGESTION = "suggestion"  # Nice to have - minor improvement


@dataclass
class ValidationIssue:
    """A single validation issue found by LLM or rules."""
    severity: ValidationSeverity
    category: str  # "lore", "character", "tone", "quality", "temporal"
    message: str
    suggestion: Optional[str] = None
    source: str = "llm"  # "llm" or "rule"
    confidence: float = 1.0  # 0.0-1.0, LLM confidence in the issue


@dataclass
class ValidationResult:
    """Complete validation result for a script."""
    is_valid: bool
    script: str
    issues: List[ValidationIssue] = field(default_factory=list)
    llm_feedback: Optional[str] = None
    overall_score: Optional[float] = None  # 0.0-1.0
    
    def __post_init__(self):
        """Calculate validity based on critical issues."""
        self.is_valid = not any(
            issue.severity == ValidationSeverity.CRITICAL 
            for issue in self.issues
        )
    
    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Get all issues of a specific severity."""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_critical_issues(self) -> List[ValidationIssue]:
        """Get all critical issues."""
        return self.get_issues_by_severity(ValidationSeverity.CRITICAL)
    
    def get_warnings(self) -> List[ValidationIssue]:
        """Get all warnings."""
        return self.get_issues_by_severity(ValidationSeverity.WARNING)
    
    def get_suggestions(self) -> List[ValidationIssue]:
        """Get all suggestions."""
        return self.get_issues_by_severity(ValidationSeverity.SUGGESTION)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_valid": self.is_valid,
            "overall_score": self.overall_score,
            "issues": [
                {
                    "severity": issue.severity.value,
                    "category": issue.category,
                    "message": issue.message,
                    "suggestion": issue.suggestion,
                    "source": issue.source,
                    "confidence": issue.confidence
                }
                for issue in self.issues
            ],
            "llm_feedback": self.llm_feedback,
            "summary": {
                "critical": len(self.get_critical_issues()),
                "warnings": len(self.get_warnings()),
                "suggestions": len(self.get_suggestions())
            }
        }


class LLMValidator:
    """
    LLM-powered script validator using Ollama.
    
    Validates scripts for:
    1. Lore accuracy - Does it fit Fallout canon?
    2. Character consistency - Does it match the DJ's personality?
    3. Temporal consistency - Does it respect timeline constraints?
    4. Quality - Is it well-written and engaging?
    5. Tone appropriateness - Does it match expected mood/context?
    """
    
    def __init__(
        self, 
        ollama_client: Optional[OllamaClient] = None,
        model: str = "fluffy/l3-8b-stheno-v3.2",
        temperature: float = 0.1,  # Low temp for consistent validation
        templates_dir: Optional[Path] = None,
        validate_connection: bool = True
    ):
        """
        Initialize LLM validator.
        
        Args:
            ollama_client: Ollama client instance (creates new if None)
            model: Model to use for validation
            temperature: Temperature for validation (low = more consistent)
            templates_dir: Directory containing validation prompt templates
            validate_connection: Whether to validate Ollama connection on init
        
        Raises:
            ConnectionError: If validate_connection=True and Ollama unavailable
        """
        try:
            self.ollama = ollama_client or OllamaClient()
            
            # Optionally verify Ollama is accessible
            if validate_connection:
                if not self.ollama.check_connection():
                    raise ConnectionError(
                        "Cannot connect to Ollama server. "
                        "Make sure Ollama is running with: ollama serve"
                    )
        except Exception as e:
            if validate_connection:
                raise ConnectionError(
                    f"Failed to initialize Ollama client: {e}. "
                    "Make sure Ollama is running with: ollama serve"
                ) from e
            # If not validating, store client anyway for later use
            self.ollama = ollama_client or OllamaClient()
        
        self.model = model
        self.temperature = temperature
        
        # Load validation prompt templates
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates" / "validation"
        self.templates_dir = Path(templates_dir)
    
    def validate(
        self,
        script: str,
        character_card: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        validation_aspects: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Validate a script using LLM.
        
        Args:
            script: Generated script to validate
            character_card: Character card with personality and constraints
            context: Additional context (weather, time, topic, etc.)
            validation_aspects: Specific aspects to validate 
                               (default: all aspects)
        
        Returns:
            ValidationResult with issues and feedback
        """
        context = context or {}
        validation_aspects = validation_aspects or [
            "lore", "character", "temporal", "quality", "tone"
        ]
        
        # Build validation prompt
        prompt = self._build_validation_prompt(
            script, character_card, context, validation_aspects
        )
        
        try:
            # Get LLM validation response
            response = self.ollama.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": self.temperature,
                    "top_p": 0.9
                },
                timeout=120  # Validation can take longer
            )
            
            # Parse LLM response into validation result
            result = self._parse_validation_response(response, script)
            
            return result
            
        except Exception as e:
            # If LLM validation fails, return empty result with error
            return ValidationResult(
                is_valid=False,
                script=script,
                issues=[
                    ValidationIssue(
                        severity=ValidationSeverity.CRITICAL,
                        category="system",
                        message=f"LLM validation failed: {str(e)}",
                        source="llm"
                    )
                ]
            )
    
    def _build_validation_prompt(
        self,
        script: str,
        character_card: Dict[str, Any],
        context: Dict[str, Any],
        aspects: List[str]
    ) -> str:
        """
        Build comprehensive validation prompt.
        
        Uses structured format with clear sections for the LLM to analyze.
        """
        # Extract character info
        dj_name = character_card.get("name", "Unknown DJ")
        tone = character_card.get("tone", "")
        do_guidelines = character_card.get("do", [])
        dont_guidelines = character_card.get("dont", [])
        knowledge_constraints = character_card.get("knowledge_constraints", {})
        
        # Build prompt sections
        prompt_parts = [
            "<validation_task>",
            "You are an expert validator for Fallout radio scripts.",
            "Analyze the following script and identify any issues.",
            "</validation_task>",
            "",
            "<character_profile>",
            f"DJ Name: {dj_name}",
            f"Tone: {tone}",
        ]
        
        if do_guidelines:
            prompt_parts.append("\nDO Guidelines:")
            for guideline in do_guidelines:
                prompt_parts.append(f"  - {guideline}")
        
        if dont_guidelines:
            prompt_parts.append("\nDON'T Guidelines:")
            for guideline in dont_guidelines:
                prompt_parts.append(f"  - {guideline}")
        
        # Add temporal constraints
        temporal_cutoff = knowledge_constraints.get("temporal_cutoff_year")
        if temporal_cutoff:
            prompt_parts.append(
                f"\nTemporal Constraint: DJ only knows events up to year {temporal_cutoff}"
            )
        
        # Add forbidden knowledge
        forbidden_factions = knowledge_constraints.get("forbidden_factions", [])
        if forbidden_factions:
            prompt_parts.append(
                f"\nForbidden Factions (DJ shouldn't know): {', '.join(forbidden_factions)}"
            )
        
        forbidden_topics = knowledge_constraints.get("forbidden_topics", [])
        if forbidden_topics:
            prompt_parts.append(
                f"\nForbidden Topics (DJ shouldn't reference): {', '.join(forbidden_topics)}"
            )
        
        prompt_parts.append("</character_profile>")
        prompt_parts.append("")
        
        # Add context if provided
        if context:
            prompt_parts.append("<context>")
            for key, value in context.items():
                prompt_parts.append(f"{key}: {value}")
            prompt_parts.append("</context>")
            prompt_parts.append("")
        
        # Add script to validate
        prompt_parts.extend([
            "<script_to_validate>",
            script,
            "</script_to_validate>",
            "",
            "<validation_instructions>",
            "Analyze the script for the following aspects:",
        ])
        
        # Add specific validation aspects
        aspect_descriptions = {
            "lore": "Lore Accuracy - Does it fit Fallout canon and world rules?",
            "character": "Character Consistency - Does it match the DJ's personality and voice?",
            "temporal": "Temporal Consistency - Does it respect timeline and knowledge constraints?",
            "quality": "Quality - Is it well-written, engaging, and natural?",
            "tone": "Tone - Does it match the expected mood and context?"
        }
        
        for aspect in aspects:
            desc = aspect_descriptions.get(aspect, aspect)
            prompt_parts.append(f"  - {desc}")
        
        prompt_parts.extend([
            "",
            "Respond in JSON format with the following structure:",
            "{",
            '  "overall_score": 0.85,  // 0.0-1.0, overall script quality',
            '  "is_valid": true,  // false if critical issues found',
            '  "issues": [',
            '    {',
            '      "severity": "warning",  // "critical", "warning", or "suggestion"',
            '      "category": "character",  // "lore", "character", "temporal", "quality", "tone"',
            '      "message": "Script lacks characteristic filler words",',
            '      "suggestion": "Add filler words like \'um\' or \'you know\'",',
            '      "confidence": 0.8  // 0.0-1.0, your confidence in this issue',
            '    }',
            '  ],',
            '  "feedback": "Brief overall feedback on the script"',
            "}",
            "",
            "Only include issues you actually found. Empty issues array is fine if script is perfect.",
            "Be constructive and specific in your feedback.",
            "</validation_instructions>"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_validation_response(
        self, 
        response: str, 
        script: str
    ) -> ValidationResult:
        """
        Parse LLM JSON response into ValidationResult.
        
        Handles malformed JSON with fallback parsing.
        """
        try:
            # Try to extract JSON from response
            # LLM might add extra text before/after JSON
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            # Parse issues
            issues = []
            for issue_data in data.get("issues", []):
                try:
                    severity = ValidationSeverity(issue_data.get("severity", "warning"))
                except ValueError:
                    severity = ValidationSeverity.WARNING
                
                issue = ValidationIssue(
                    severity=severity,
                    category=issue_data.get("category", "unknown"),
                    message=issue_data.get("message", ""),
                    suggestion=issue_data.get("suggestion"),
                    source="llm",
                    confidence=issue_data.get("confidence", 1.0)
                )
                issues.append(issue)
            
            # Create result
            result = ValidationResult(
                is_valid=data.get("is_valid", True),
                script=script,
                issues=issues,
                llm_feedback=data.get("feedback"),
                overall_score=data.get("overall_score")
            )
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            # Log JSON parsing failure for debugging
            import logging
            logging.warning(
                f"Failed to parse LLM validation response as JSON: {e}. "
                f"Falling back to text parsing. Response preview: {response[:100]}..."
            )
            # Fallback: parse text response
            return self._parse_text_response(response, script)
    
    def _parse_text_response(self, response: str, script: str) -> ValidationResult:
        """
        Fallback parser for non-JSON responses.
        
        Extracts issues from natural language text.
        """
        issues = []
        
        # Look for common issue indicators
        issue_patterns = [
            ("temporal", ["year", "timeline", "future", "past"]),
            ("character", ["personality", "tone", "voice", "catchphrase"]),
            ("lore", ["canon", "faction", "lore", "fallout"]),
            ("quality", ["quality", "poorly", "awkward", "unclear"]),
        ]
        
        response_lower = response.lower()
        
        for category, keywords in issue_patterns:
            if any(kw in response_lower for kw in keywords):
                # Found potential issue
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category=category,
                        message=f"LLM indicated {category} concern (see feedback)",
                        source="llm",
                        confidence=0.5  # Low confidence from text parsing
                    )
                )
        
        # If response contains "valid" or "good", assume valid
        is_valid = any(
            word in response_lower 
            for word in ["valid", "good", "acceptable", "pass"]
        )
        
        return ValidationResult(
            is_valid=is_valid,
            script=script,
            issues=issues,
            llm_feedback=response
        )
    
    def quick_validate(
        self,
        script: str,
        character_card: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Quick validation - returns (is_valid, brief_feedback).
        
        Faster than full validation, good for iteration loops.
        """
        result = self.validate(
            script,
            character_card,
            validation_aspects=["character", "lore"]  # Focus on key aspects
        )
        
        feedback = result.llm_feedback or "No feedback"
        if result.issues:
            critical = len(result.get_critical_issues())
            warnings = len(result.get_warnings())
            feedback += f" ({critical} critical, {warnings} warnings)"
        
        return result.is_valid, feedback


class HybridValidator:
    """
    Hybrid validator combining LLM and rule-based validation.
    
    Strategy:
    1. Run fast rule-based checks first (hard constraints)
    2. If rules pass, run LLM validation (soft constraints + quality)
    3. Combine results for comprehensive validation
    """
    
    def __init__(
        self,
        llm_validator: Optional[LLMValidator] = None,
        use_llm: bool = True,
        use_rules: bool = True
    ):
        """
        Initialize hybrid validator.
        
        Args:
            llm_validator: LLM validator instance
            use_llm: Enable LLM validation
            use_rules: Enable rule-based validation
        """
        self.llm_validator = llm_validator or LLMValidator()
        self.use_llm = use_llm
        self.use_rules = use_rules
    
    def validate(
        self,
        script: str,
        character_card: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Run hybrid validation (rules + LLM).
        
        Args:
            script: Script to validate
            character_card: Character constraints
            context: Additional context
        
        Returns:
            Combined validation result
        """
        all_issues: List[ValidationIssue] = []
        
        # 1. Rule-based validation (fast, hard constraints)
        if self.use_rules:
            rule_issues = self._run_rule_based_validation(
                script, character_card
            )
            all_issues.extend(rule_issues)
        
        # 2. LLM validation (slower, soft constraints + quality)
        llm_result = None
        if self.use_llm:
            llm_result = self.llm_validator.validate(
                script, character_card, context
            )
            all_issues.extend(llm_result.issues)
        
        # 3. Combine results
        return ValidationResult(
            is_valid=not any(
                issue.severity == ValidationSeverity.CRITICAL 
                for issue in all_issues
            ),
            script=script,
            issues=all_issues,
            llm_feedback=llm_result.llm_feedback if llm_result else None,
            overall_score=llm_result.overall_score if llm_result else None
        )
    
    def _run_rule_based_validation(
        self,
        script: str,
        character_card: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """
        Run rule-based validation checks.
        
        Imports existing validators and converts their results.
        """
        issues: List[ValidationIssue] = []
        
        try:
            from consistency_validator import ConsistencyValidator
            
            validator = ConsistencyValidator(character_card)
            is_valid = validator.validate(script)
            
            # Convert violations to issues
            for violation in validator.get_violations():
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.CRITICAL,
                        category="rule",
                        message=violation,
                        source="rule",
                        confidence=1.0
                    )
                )
            
            # Convert warnings to issues
            for warning in validator.get_warnings():
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="rule",
                        message=warning,
                        source="rule",
                        confidence=1.0
                    )
                )
        
        except ImportError:
            # ConsistencyValidator not available, skip rule-based checks
            pass
        
        return issues


def validate_script(
    script: str,
    character_card: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    strategy: str = "hybrid"
) -> ValidationResult:
    """
    Convenience function to validate a script.
    
    Args:
        script: Script text to validate
        character_card: Character card with constraints
        context: Optional context (weather, time, etc.)
        strategy: Validation strategy ("llm", "rules", "hybrid")
    
    Returns:
        ValidationResult with issues and feedback
    """
    if strategy == "llm":
        validator = LLMValidator()
        return validator.validate(script, character_card, context)
    
    elif strategy == "rules":
        from consistency_validator import ConsistencyValidator
        validator = ConsistencyValidator(character_card)
        is_valid = validator.validate(script)
        
        issues = []
        for violation in validator.get_violations():
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    category="rule",
                    message=violation,
                    source="rule"
                )
            )
        
        for warning in validator.get_warnings():
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="rule",
                    message=warning,
                    source="rule"
                )
            )
        
        return ValidationResult(
            is_valid=is_valid,
            script=script,
            issues=issues
        )
    
    else:  # hybrid (default)
        validator = HybridValidator()
        return validator.validate(script, character_card, context)
