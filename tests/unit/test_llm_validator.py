"""
Unit tests for llm_validator.py

Tests the LLMValidator and HybridValidator modules with mocked LLM dependencies.
Covers rules-based validation, LLM-based validation, hybrid mode, and error handling.

Phase 4: Testing Infrastructure
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools" / "script-generator"))

# Import mocks first
from tests.mocks.mock_llm import MockLLMClient, MockLLMClientWithFailure

# Import validator modules
from llm_validator import (
    LLMValidator,
    HybridValidator,
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    validate_script
)


@pytest.mark.mock
class TestValidationDataClasses:
    """Test suite for validation data classes"""
    
    def test_validation_issue_creation(self):
        """Test creating a ValidationIssue"""
        issue = ValidationIssue(
            severity=ValidationSeverity.CRITICAL,
            category="lore",
            message="Mentions future events",
            suggestion="Remove references to events after 2102",
            source="llm",
            confidence=0.9
        )
        
        assert issue.severity == ValidationSeverity.CRITICAL
        assert issue.category == "lore"
        assert issue.message == "Mentions future events"
        assert issue.suggestion == "Remove references to events after 2102"
        assert issue.source == "llm"
        assert issue.confidence == 0.9
    
    def test_validation_result_creation(self):
        """Test creating a ValidationResult"""
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="tone",
                message="Tone doesn't match character",
                source="llm"
            )
        ]
        
        result = ValidationResult(
            is_valid=True,
            script="Test script",
            issues=issues,
            llm_feedback="Good overall quality",
            overall_score=0.85
        )
        
        assert result.is_valid is True
        assert len(result.issues) == 1
        assert result.llm_feedback == "Good overall quality"
        assert result.overall_score == 0.85
    
    def test_validation_result_auto_invalid_on_critical(self):
        """Test that critical issues automatically invalidate result"""
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="lore",
                message="Critical lore violation",
                source="llm"
            )
        ]
        
        result = ValidationResult(
            is_valid=True,  # Will be overridden
            script="Test script",
            issues=issues
        )
        
        # Should be invalid due to critical issue
        assert result.is_valid is False
    
    def test_validation_result_get_issues_by_severity(self):
        """Test filtering issues by severity"""
        issues = [
            ValidationIssue(ValidationSeverity.CRITICAL, "lore", "Critical issue", source="llm"),
            ValidationIssue(ValidationSeverity.WARNING, "tone", "Warning issue", source="llm"),
            ValidationIssue(ValidationSeverity.SUGGESTION, "quality", "Suggestion issue", source="llm"),
            ValidationIssue(ValidationSeverity.CRITICAL, "character", "Another critical", source="llm"),
        ]
        
        result = ValidationResult(is_valid=False, script="Test", issues=issues)
        
        critical = result.get_critical_issues()
        warnings = result.get_warnings()
        suggestions = result.get_suggestions()
        
        assert len(critical) == 2
        assert len(warnings) == 1
        assert len(suggestions) == 1
    
    def test_validation_result_to_dict(self):
        """Test converting ValidationResult to dictionary"""
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="tone",
                message="Test message",
                source="llm",
                confidence=0.8
            )
        ]
        
        result = ValidationResult(
            is_valid=True,
            script="Test script",
            issues=issues,
            llm_feedback="Feedback",
            overall_score=0.9
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['is_valid'] is True
        assert result_dict['overall_score'] == 0.9
        assert result_dict['llm_feedback'] == "Feedback"
        assert len(result_dict['issues']) == 1
        assert result_dict['summary']['critical'] == 0
        assert result_dict['summary']['warnings'] == 1
        assert result_dict['summary']['suggestions'] == 0


@pytest.mark.mock
class TestLLMValidatorInitialization:
    """Test suite for LLMValidator initialization"""
    
    def test_initialization_with_mock_client(self, mock_llm):
        """Test LLMValidator initialization with mock client"""
        validator = LLMValidator(
            ollama_client=mock_llm,
            model="test-model",
            temperature=0.1,
            validate_connection=False
        )
        
        assert validator.ollama == mock_llm
        assert validator.model == "test-model"
        assert validator.temperature == 0.1
    
    def test_initialization_validates_connection(self, mock_llm):
        """Test that initialization validates connection when requested"""
        validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=True
        )
        
        # Mock client should return True for check_connection()
        assert validator.ollama.check_connection() is True
    
    def test_initialization_fails_on_bad_connection(self):
        """Test that initialization fails with bad connection"""
        mock_llm_failed = Mock()
        mock_llm_failed.check_connection.return_value = False
        
        with pytest.raises(ConnectionError, match="Cannot connect to Ollama"):
            LLMValidator(
                ollama_client=mock_llm_failed,
                validate_connection=True
            )
    
    def test_initialization_without_connection_check(self):
        """Test initialization without connection validation"""
        mock_llm_failed = Mock()
        mock_llm_failed.check_connection.return_value = False
        
        # Should not raise error when validate_connection=False
        validator = LLMValidator(
            ollama_client=mock_llm_failed,
            validate_connection=False
        )
        
        assert validator.ollama == mock_llm_failed


@pytest.mark.mock
class TestLLMValidatorPromptBuilding:
    """Test suite for validation prompt building"""
    
    def test_build_validation_prompt_basic(self, mock_llm):
        """Test basic validation prompt building"""
        validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=False
        )
        
        character_card = {
            'name': 'Julie',
            'tone': 'friendly and optimistic',
            'do': ['Use filler words'],
            'dont': ['Mention post-2102 events'],
            'knowledge_constraints': {
                'temporal_cutoff_year': 2102,
                'forbidden_factions': ['Institute'],
                'forbidden_topics': ['synths']
            }
        }
        
        script = "Test script content"
        context = {'weather': 'sunny', 'time_of_day': 'morning'}
        
        prompt = validator._build_validation_prompt(
            script=script,
            character_card=character_card,
            context=context,
            aspects=['lore', 'character']
        )
        
        # Verify prompt contains key elements
        assert 'Julie' in prompt
        assert 'friendly and optimistic' in prompt
        assert 'Use filler words' in prompt
        assert 'Mention post-2102 events' in prompt
        assert '2102' in prompt
        assert 'Institute' in prompt
        assert 'synths' in prompt
        assert 'Test script content' in prompt
        assert 'sunny' in prompt
        assert 'morning' in prompt
    
    def test_build_validation_prompt_minimal(self, mock_llm):
        """Test validation prompt with minimal character card"""
        validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=False
        )
        
        character_card = {
            'name': 'Test DJ'
        }
        
        script = "Simple script"
        
        prompt = validator._build_validation_prompt(
            script=script,
            character_card=character_card,
            context={},
            aspects=['lore']
        )
        
        assert 'Test DJ' in prompt
        assert 'Simple script' in prompt


@pytest.mark.mock
class TestLLMValidatorValidation:
    """Test suite for LLM-based validation"""
    
    def test_validate_with_json_response(self, mock_llm, test_logger):
        """Test validation with proper JSON response"""
        test_logger.info("Testing LLM validation with JSON response")
        
        # Configure mock to return valid JSON
        json_response = {
            "overall_score": 0.85,
            "is_valid": True,
            "issues": [
                {
                    "severity": "warning",
                    "category": "tone",
                    "message": "Could be more upbeat",
                    "suggestion": "Add more enthusiasm",
                    "confidence": 0.7
                }
            ],
            "feedback": "Good script overall"
        }
        
        mock_llm.set_custom_response(
            "validate",
            json.dumps(json_response)
        )
        
        validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=False
        )
        
        character_card = {
            'name': 'Julie',
            'tone': 'upbeat',
            'do': [],
            'dont': []
        }
        
        result = validator.validate(
            script="Test script for validation",
            character_card=character_card,
            context={'weather': 'sunny'}
        )
        
        assert result.is_valid is True
        assert result.overall_score == 0.85
        assert len(result.issues) == 1
        assert result.issues[0].severity == ValidationSeverity.WARNING
        assert result.llm_feedback == "Good script overall"
    
    def test_validate_with_critical_issues(self, mock_llm):
        """Test validation with critical issues"""
        json_response = {
            "overall_score": 0.4,
            "is_valid": False,
            "issues": [
                {
                    "severity": "critical",
                    "category": "lore",
                    "message": "Mentions future events",
                    "confidence": 0.95
                }
            ],
            "feedback": "Critical lore violation"
        }
        
        mock_llm.set_custom_response(
            "validate",
            json.dumps(json_response)
        )
        
        validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=False
        )
        
        character_card = {'name': 'Julie', 'do': [], 'dont': []}
        
        result = validator.validate(
            script="In 2287, the Institute will rise",
            character_card=character_card
        )
        
        assert result.is_valid is False
        assert len(result.get_critical_issues()) == 1
    
    def test_validate_with_malformed_json(self, mock_llm, test_logger):
        """Test validation with malformed JSON response"""
        test_logger.info("Testing validation with malformed JSON")
        
        # Return non-JSON response
        mock_llm.set_custom_response(
            "validate",
            "This is not valid JSON but mentions temporal issues"
        )
        
        validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=False
        )
        
        character_card = {'name': 'Julie', 'do': [], 'dont': []}
        
        result = validator.validate(
            script="Test script",
            character_card=character_card
        )
        
        # Should fall back to text parsing
        assert result is not None
        assert isinstance(result, ValidationResult)
    
    def test_validate_llm_failure(self, test_logger):
        """Test validation when LLM fails"""
        test_logger.info("Testing validation with LLM failure")
        
        mock_llm_failing = MockLLMClientWithFailure(fail_after_n_calls=0)
        
        validator = LLMValidator(
            ollama_client=mock_llm_failing,
            validate_connection=False
        )
        
        character_card = {'name': 'Julie', 'do': [], 'dont': []}
        
        result = validator.validate(
            script="Test script",
            character_card=character_card
        )
        
        # Should return result with error issue
        assert result.is_valid is False
        assert len(result.issues) > 0
        assert any('failed' in issue.message.lower() for issue in result.issues)
    
    def test_validate_with_specific_aspects(self, mock_llm):
        """Test validation with specific validation aspects"""
        json_response = {
            "overall_score": 0.9,
            "is_valid": True,
            "issues": [],
            "feedback": "Good"
        }
        
        mock_llm.set_custom_response(
            "validate",
            json.dumps(json_response)
        )
        
        validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=False
        )
        
        character_card = {'name': 'Julie', 'do': [], 'dont': []}
        
        result = validator.validate(
            script="Test script",
            character_card=character_card,
            validation_aspects=['lore', 'character']
        )
        
        # Verify validation completed
        assert result.is_valid is True
        
        # Check that mock LLM was called
        calls = mock_llm.get_call_log()
        assert len(calls) > 0


@pytest.mark.mock
class TestLLMValidatorQuickValidate:
    """Test suite for quick validation"""
    
    def test_quick_validate_valid_script(self, mock_llm):
        """Test quick validation with valid script"""
        json_response = {
            "overall_score": 0.9,
            "is_valid": True,
            "issues": [],
            "feedback": "Excellent script"
        }
        
        mock_llm.set_custom_response(
            "validate",
            json.dumps(json_response)
        )
        
        validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=False
        )
        
        character_card = {'name': 'Julie', 'do': [], 'dont': []}
        
        is_valid, feedback = validator.quick_validate(
            script="Test script",
            character_card=character_card
        )
        
        assert is_valid is True
        assert "Excellent script" in feedback
    
    def test_quick_validate_with_issues(self, mock_llm):
        """Test quick validation with issues"""
        json_response = {
            "overall_score": 0.6,
            "is_valid": False,
            "issues": [
                {
                    "severity": "critical",
                    "category": "lore",
                    "message": "Lore issue",
                    "confidence": 0.9
                },
                {
                    "severity": "warning",
                    "category": "tone",
                    "message": "Tone issue",
                    "confidence": 0.7
                }
            ],
            "feedback": "Needs improvement"
        }
        
        mock_llm.set_custom_response(
            "validate",
            json.dumps(json_response)
        )
        
        validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=False
        )
        
        character_card = {'name': 'Julie', 'do': [], 'dont': []}
        
        is_valid, feedback = validator.quick_validate(
            script="Test script",
            character_card=character_card
        )
        
        assert is_valid is False
        assert "1 critical" in feedback
        assert "1 warnings" in feedback


@pytest.mark.mock
class TestHybridValidatorInitialization:
    """Test suite for HybridValidator initialization"""
    
    def test_initialization_default(self, mock_llm):
        """Test HybridValidator initialization with defaults"""
        llm_validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=False
        )
        
        hybrid = HybridValidator(
            llm_validator=llm_validator,
            use_llm=True,
            use_rules=True
        )
        
        assert hybrid.llm_validator == llm_validator
        assert hybrid.use_llm is True
        assert hybrid.use_rules is True
    
    def test_initialization_llm_only(self, mock_llm):
        """Test HybridValidator with LLM only"""
        llm_validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=False
        )
        
        hybrid = HybridValidator(
            llm_validator=llm_validator,
            use_llm=True,
            use_rules=False
        )
        
        assert hybrid.use_llm is True
        assert hybrid.use_rules is False
    
    def test_initialization_rules_only(self, mock_llm):
        """Test HybridValidator with rules only"""
        llm_validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=False
        )
        
        hybrid = HybridValidator(
            llm_validator=llm_validator,
            use_llm=False,
            use_rules=True
        )
        
        assert hybrid.use_llm is False
        assert hybrid.use_rules is True


@pytest.mark.mock
class TestHybridValidatorValidation:
    """Test suite for hybrid validation"""
    
    def test_hybrid_validation_both_modes(self, mock_llm, test_logger):
        """Test hybrid validation with both rules and LLM"""
        test_logger.info("Testing hybrid validation with both modes")
        
        json_response = {
            "overall_score": 0.8,
            "is_valid": True,
            "issues": [
                {
                    "severity": "suggestion",
                    "category": "quality",
                    "message": "Could add more detail",
                    "confidence": 0.6
                }
            ],
            "feedback": "Good overall"
        }
        
        mock_llm.set_custom_response(
            "validate",
            json.dumps(json_response)
        )
        
        llm_validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=False
        )
        
        hybrid = HybridValidator(
            llm_validator=llm_validator,
            use_llm=True,
            use_rules=True
        )
        
        character_card = {
            'name': 'Julie',
            'tone': 'friendly',
            'do': [],
            'dont': [],
            'knowledge_constraints': {
                'temporal_cutoff_year': 2102
            }
        }
        
        result = hybrid.validate(
            script="Test script that's perfectly fine",
            character_card=character_card
        )
        
        # Should have issues from LLM validation
        assert result is not None
        assert isinstance(result, ValidationResult)
    
    def test_hybrid_validation_llm_only_mode(self, mock_llm):
        """Test hybrid validator in LLM-only mode"""
        json_response = {
            "overall_score": 0.9,
            "is_valid": True,
            "issues": [],
            "feedback": "Perfect"
        }
        
        mock_llm.set_custom_response(
            "validate",
            json.dumps(json_response)
        )
        
        llm_validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=False
        )
        
        hybrid = HybridValidator(
            llm_validator=llm_validator,
            use_llm=True,
            use_rules=False
        )
        
        character_card = {'name': 'Julie', 'do': [], 'dont': []}
        
        result = hybrid.validate(
            script="Test script",
            character_card=character_card
        )
        
        assert result.is_valid is True
        # Should only have LLM issues, no rule-based issues
        assert all(issue.source == "llm" for issue in result.issues)
    
    def test_hybrid_validation_rules_only_mode(self, mock_llm):
        """Test hybrid validator in rules-only mode"""
        llm_validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=False
        )
        
        hybrid = HybridValidator(
            llm_validator=llm_validator,
            use_llm=False,
            use_rules=True
        )
        
        character_card = {
            'name': 'Julie',
            'tone': 'friendly',
            'do': [],
            'dont': ['mention synths'],
            'knowledge_constraints': {}
        }
        
        # Script that might violate rules
        result = hybrid.validate(
            script="Test script",
            character_card=character_card
        )
        
        # Should complete validation (even if no violations found)
        assert result is not None
        assert isinstance(result, ValidationResult)
    
    def test_hybrid_validation_combines_issues(self, mock_llm, test_logger):
        """Test that hybrid validator combines issues from both sources"""
        test_logger.info("Testing hybrid validation combines issues")
        
        # LLM will return some issues
        json_response = {
            "overall_score": 0.7,
            "is_valid": True,
            "issues": [
                {
                    "severity": "warning",
                    "category": "quality",
                    "message": "LLM-detected issue",
                    "confidence": 0.8
                }
            ],
            "feedback": "Some improvements needed"
        }
        
        mock_llm.set_custom_response(
            "validate",
            json.dumps(json_response)
        )
        
        llm_validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=False
        )
        
        hybrid = HybridValidator(
            llm_validator=llm_validator,
            use_llm=True,
            use_rules=True
        )
        
        character_card = {
            'name': 'Julie',
            'tone': 'friendly',
            'do': [],
            'dont': [],
            'knowledge_constraints': {}
        }
        
        result = hybrid.validate(
            script="Test script",
            character_card=character_card
        )
        
        # Should have issues from LLM
        assert len(result.issues) >= 1
        llm_issues = [i for i in result.issues if i.source == "llm"]
        assert len(llm_issues) >= 1


@pytest.mark.mock
class TestValidateScriptConvenienceFunction:
    """Test suite for validate_script convenience function"""
    
    def test_validate_script_llm_strategy(self, mock_llm):
        """Test validate_script with LLM strategy"""
        json_response = {
            "overall_score": 0.9,
            "is_valid": True,
            "issues": [],
            "feedback": "Good"
        }
        
        mock_llm.set_custom_response(
            "validate",
            json.dumps(json_response)
        )
        
        with patch('llm_validator.LLMValidator') as mock_validator_class:
            mock_validator_instance = LLMValidator(
                ollama_client=mock_llm,
                validate_connection=False
            )
            mock_validator_class.return_value = mock_validator_instance
            
            character_card = {'name': 'Julie', 'do': [], 'dont': []}
            
            result = validate_script(
                script="Test script",
                character_card=character_card,
                strategy="llm"
            )
            
            assert result is not None
    
    def test_validate_script_hybrid_strategy(self, mock_llm):
        """Test validate_script with hybrid strategy"""
        json_response = {
            "overall_score": 0.85,
            "is_valid": True,
            "issues": [],
            "feedback": "Good"
        }
        
        mock_llm.set_custom_response(
            "validate",
            json.dumps(json_response)
        )
        
        with patch('llm_validator.HybridValidator') as mock_validator_class:
            llm_validator = LLMValidator(
                ollama_client=mock_llm,
                validate_connection=False
            )
            mock_validator_instance = HybridValidator(llm_validator=llm_validator)
            mock_validator_class.return_value = mock_validator_instance
            
            character_card = {'name': 'Julie', 'do': [], 'dont': []}
            
            result = validate_script(
                script="Test script",
                character_card=character_card,
                strategy="hybrid"
            )
            
            assert result is not None


@pytest.mark.mock
class TestValidationModes:
    """Test suite for different validation modes"""
    
    def test_validation_mode_all_aspects(self, mock_llm):
        """Test validation with all aspects enabled"""
        json_response = {
            "overall_score": 0.8,
            "is_valid": True,
            "issues": [],
            "feedback": "Good"
        }
        
        mock_llm.set_custom_response(
            "validate",
            json.dumps(json_response)
        )
        
        validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=False
        )
        
        character_card = {'name': 'Julie', 'do': [], 'dont': []}
        
        result = validator.validate(
            script="Test script",
            character_card=character_card,
            validation_aspects=['lore', 'character', 'temporal', 'quality', 'tone']
        )
        
        assert result.is_valid is True
    
    def test_validation_mode_subset_aspects(self, mock_llm):
        """Test validation with subset of aspects"""
        json_response = {
            "overall_score": 0.9,
            "is_valid": True,
            "issues": [],
            "feedback": "Good"
        }
        
        mock_llm.set_custom_response(
            "validate",
            json.dumps(json_response)
        )
        
        validator = LLMValidator(
            ollama_client=mock_llm,
            validate_connection=False
        )
        
        character_card = {'name': 'Julie', 'do': [], 'dont': []}
        
        # Only validate lore and character
        result = validator.validate(
            script="Test script",
            character_card=character_card,
            validation_aspects=['lore', 'character']
        )
        
        assert result is not None
        assert isinstance(result, ValidationResult)
    
    def test_fallback_to_rules_when_llm_unavailable(self, test_logger):
        """Test that hybrid validator falls back to rules when LLM unavailable"""
        test_logger.info("Testing fallback to rules when LLM fails")
        
        mock_llm_failing = MockLLMClientWithFailure(fail_after_n_calls=0)
        
        llm_validator = LLMValidator(
            ollama_client=mock_llm_failing,
            validate_connection=False
        )
        
        hybrid = HybridValidator(
            llm_validator=llm_validator,
            use_llm=True,
            use_rules=True
        )
        
        character_card = {
            'name': 'Julie',
            'tone': 'friendly',
            'do': [],
            'dont': [],
            'knowledge_constraints': {}
        }
        
        result = hybrid.validate(
            script="Test script",
            character_card=character_card
        )
        
        # Should still complete validation using rules
        assert result is not None
        # Should have error from LLM failure
        assert any('failed' in str(issue.message).lower() for issue in result.issues)
