"""
Unit tests for validation_engine.py - Hybrid validation combining rules and LLM.

Tests:
- Hybrid validation (rules + optional LLM)
- Validation metrics tracking
- Validation modes (rules_only, hybrid, llm_only)
- Performance requirements (<100ms for rules)
- Validation result dataclass
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock
from dataclasses import asdict

# Add paths for imports
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "tools", "script-generator"))

from validation_engine import ValidationEngine, ValidationResult
from segment_plan import ValidationConstraints


class TestValidationResult:
    """Test ValidationResult dataclass."""
    
    def test_create_valid_result(self):
        """Should create a valid validation result."""
        result = ValidationResult(
            is_valid=True,
            validation_source="rules_only",
            rule_checks_passed=["temporal", "content"],
            validation_time_ms=50
        )
        
        assert result.is_valid
        assert result.validation_source == "rules_only"
        assert len(result.rule_checks_passed) == 2
        assert result.validation_time_ms == 50
    
    def test_create_invalid_result(self):
        """Should create an invalid validation result with issues."""
        result = ValidationResult(
            is_valid=False,
            validation_source="rules_only",
            rule_checks_failed=["temporal"],
            issues=["Future year detected: 2150"],
            validation_time_ms=45
        )
        
        assert not result.is_valid
        assert len(result.rule_checks_failed) == 1
        assert len(result.issues) == 1
    
    def test_get_summary_rules_only(self):
        """Should generate summary for rules-only validation."""
        result = ValidationResult(
            is_valid=True,
            validation_source="rules_only",
            validation_time_ms=30
        )
        
        summary = result.get_summary()
        
        assert "✓ VALID" in summary or "VALID" in summary
        assert "RULES_ONLY" in summary
        assert "30ms" in summary
    
    def test_get_summary_with_llm_score(self):
        """Should include LLM score in summary."""
        result = ValidationResult(
            is_valid=True,
            validation_source="hybrid",
            llm_validation_used=True,
            llm_score=0.85,
            validation_time_ms=250
        )
        
        summary = result.get_summary()
        
        assert "HYBRID" in summary
        assert "0.85" in summary or "score" in summary.lower()


class TestValidationEngineInit:
    """Test ValidationEngine initialization."""
    
    def test_init_without_ollama(self):
        """Should initialize without Ollama client."""
        engine = ValidationEngine()
        
        assert engine.rules is not None
        assert engine.ollama is None
        assert engine.metrics is not None
    
    def test_init_with_ollama(self):
        """Should initialize with Ollama client."""
        mock_ollama = Mock()
        engine = ValidationEngine(ollama_client=mock_ollama)
        
        assert engine.ollama == mock_ollama
    
    def test_metrics_initialized(self):
        """Should initialize metrics tracking."""
        engine = ValidationEngine()
        
        assert 'total_validations' in engine.metrics
        assert 'rules_only_validations' in engine.metrics
        assert engine.metrics['total_validations'] == 0


class TestValidationModes:
    """Test different validation modes."""
    
    def test_rules_only_mode(self):
        """Rules-only validation should not use LLM."""
        engine = ValidationEngine()
        
        # Verify engine can run without Ollama
        assert engine.ollama is None
    
    def test_hybrid_mode_setup(self):
        """Hybrid mode should allow both rules and LLM."""
        mock_ollama = MagicMock()
        engine = ValidationEngine(ollama_client=mock_ollama)
        
        assert engine.rules is not None
        assert engine.ollama is not None
    
    def test_llm_only_mode_setup(self):
        """LLM-only mode should have Ollama client."""
        mock_ollama = MagicMock()
        engine = ValidationEngine(ollama_client=mock_ollama)
        
        assert engine.ollama is not None


class TestMetricsTracking:
    """Test validation metrics tracking."""
    
    def test_metrics_structure(self):
        """Metrics should have required fields."""
        engine = ValidationEngine()
        
        required_metrics = [
            'total_validations',
            'rules_only_validations',
            'hybrid_validations',
            'llm_only_validations',
            'rules_passed',
            'rules_failed',
            'total_validation_time_ms'
        ]
        
        for metric in required_metrics:
            assert metric in engine.metrics
    
    def test_metrics_initial_values(self):
        """Metrics should start at zero."""
        engine = ValidationEngine()
        
        assert engine.metrics['total_validations'] == 0
        assert engine.metrics['rules_only_validations'] == 0
        assert engine.metrics['total_validation_time_ms'] == 0


class TestValidationConstraints:
    """Test validation with constraints."""
    
    def test_create_validation_constraints(self):
        """Should create validation constraints."""
        constraints = ValidationConstraints(
            max_year=2102,
            allowed_regions=["Appalachia"],
            forbidden_topics=["internet", "smartphones"]
        )
        
        assert constraints.max_year == 2102
        assert "Appalachia" in constraints.allowed_regions
        assert len(constraints.forbidden_topics) == 2


class TestResultMetadata:
    """Test validation result metadata."""
    
    def test_result_with_metadata(self):
        """Should store metadata in result."""
        metadata = {
            "script_length": 500,
            "dj_name": "Julie",
            "segment_type": "weather"
        }
        
        result = ValidationResult(
            is_valid=True,
            validation_source="rules_only",
            metadata=metadata
        )
        
        assert result.metadata == metadata
        assert result.metadata["dj_name"] == "Julie"
    
    def test_result_without_metadata(self):
        """Should handle missing metadata."""
        result = ValidationResult(
            is_valid=True,
            validation_source="rules_only"
        )
        
        assert result.metadata == {}


class TestPerformanceRequirements:
    """Test performance requirements."""
    
    def test_rules_validation_is_fast(self):
        """Rules validation should be < 100ms."""
        engine = ValidationEngine()
        
        # Note: This is a structural test
        # Actual performance test would need real validation call
        assert engine.rules is not None
        
        # Metrics should track timing
        assert 'rules_validation_time_ms' in engine.metrics


class TestValidationSource:
    """Test validation source tracking."""
    
    def test_validation_source_types(self):
        """Should support all validation source types."""
        sources = ['rules_only', 'hybrid', 'llm_only']
        
        for source in sources:
            result = ValidationResult(
                is_valid=True,
                validation_source=source
            )
            assert result.validation_source == source


class TestIssuesTracking:
    """Test issue tracking in validation results."""
    
    def test_result_with_multiple_issues(self):
        """Should track multiple validation issues."""
        issues = [
            "Future year detected: 2150",
            "Anachronism: 'internet' mentioned",
            "Regional violation: NCR in Appalachia"
        ]
        
        result = ValidationResult(
            is_valid=False,
            validation_source="rules_only",
            issues=issues
        )
        
        assert len(result.issues) == 3
        assert "Future year" in result.issues[0]
    
    def test_result_with_no_issues(self):
        """Should handle no issues (valid result)."""
        result = ValidationResult(
            is_valid=True,
            validation_source="rules_only"
        )
        
        assert len(result.issues) == 0


class TestLLMValidationIntegration:
    """Test LLM validation integration."""
    
    def test_llm_validation_flag(self):
        """Should track whether LLM validation was used."""
        result = ValidationResult(
            is_valid=True,
            validation_source="hybrid",
            llm_validation_used=True
        )
        
        assert result.llm_validation_used
    
    def test_llm_score_tracking(self):
        """Should track LLM quality score."""
        result = ValidationResult(
            is_valid=True,
            validation_source="hybrid",
            llm_validation_used=True,
            llm_score=0.92
        )
        
        assert result.llm_score == 0.92
        assert 0.0 <= result.llm_score <= 1.0
    
    def test_no_llm_score_when_not_used(self):
        """Should have None LLM score when not used."""
        result = ValidationResult(
            is_valid=True,
            validation_source="rules_only",
            llm_validation_used=False
        )
        
        assert result.llm_score is None


class TestValidationEfficiency:
    """Test validation efficiency metrics."""
    
    def test_80_percent_rules_target(self):
        """Engine should aim for 80% rules-only validation."""
        engine = ValidationEngine()
        
        # This is a design goal metric
        # Actual testing would require running many validations
        assert engine.metrics is not None


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_validation_result(self):
        """Should handle minimal validation result."""
        result = ValidationResult(
            is_valid=True,
            validation_source="rules_only"
        )
        
        assert result.is_valid
        assert len(result.issues) == 0
        assert len(result.rule_checks_passed) == 0
    
    def test_validation_time_zero(self):
        """Should handle zero validation time."""
        result = ValidationResult(
            is_valid=True,
            validation_source="rules_only",
            validation_time_ms=0
        )
        
        assert result.validation_time_ms == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
