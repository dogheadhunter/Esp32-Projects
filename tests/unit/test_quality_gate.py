"""
Unit tests for ProgressiveQualityGate.

Tests the Phase 2A quality gate that enforces tiered validation thresholds.
"""

import pytest
import sys
from pathlib import Path

# Add tools/script-generator to path
script_gen_path = Path(__file__).parent.parent.parent / "tools" / "script-generator"
sys.path.insert(0, str(script_gen_path))

from quality_gate import ProgressiveQualityGate, QualityGateDecision
from consistency_validator import ValidationSeverity


class TestQualityGate:
    """Test suite for ProgressiveQualityGate."""
    
    def test_abort_on_critical_threshold(self):
        """Test that quality gate aborts when critical violations exceed threshold (0)."""
        gate = ProgressiveQualityGate(
            critical_threshold=0,
            quality_threshold=0.05,
            warning_threshold=None
        )
        
        # Create violations with 1 critical error
        violations = [
            {
                "message": "Temporal violation: References year 2281 but cutoff is 2102",
                "severity": ValidationSeverity.CRITICAL,
                "category": "temporal"
            }
        ]
        
        # Evaluate
        decision = gate.evaluate(violations)
        
        # Should fail with FAIL_CRITICAL
        assert decision == QualityGateDecision.FAIL_CRITICAL, "Should fail on critical violation"
        
        # Should abort
        assert gate.should_abort(decision), "should_abort() should return True for FAIL_CRITICAL"
        
        # Check statistics
        stats = gate.get_statistics()
        assert stats['critical_count'] == 1, "Should track 1 critical violation"
        assert stats['critical_rate'] == 1.0, "Critical rate should be 100% (1/1)"
    
    def test_continue_on_minor_threshold(self):
        """Test that quality gate continues when only minor issues present (< 5% threshold)."""
        gate = ProgressiveQualityGate(
            critical_threshold=0,
            quality_threshold=0.05,
            warning_threshold=None
        )
        
        # Create violations with only warnings
        violations = [
            {
                "message": "Voice pattern: Missing filler words",
                "severity": ValidationSeverity.WARNING,
                "category": "voice"
            }
        ]
        
        # Evaluate
        decision = gate.evaluate(violations)
        
        # Should pass with WARN (warnings don't block)
        assert decision == QualityGateDecision.WARN, "Should warn on warnings only"
        
        # Should NOT abort
        assert not gate.should_abort(decision), "should_abort() should return False for WARN"
        
        # Check statistics
        stats = gate.get_statistics()
        assert stats['warning_count'] == 1, "Should track 1 warning"
        assert stats['critical_count'] == 0, "Should have no critical violations"
    
    def test_quality_threshold_tracking(self):
        """Test that quality issues are tracked but don't currently block."""
        gate = ProgressiveQualityGate(
            critical_threshold=0,
            quality_threshold=0.05,
            warning_threshold=None
        )
        
        # Simulate 10 validations with 1 quality issue (10% rate)
        for i in range(10):
            if i == 0:
                # One quality issue
                violations = [
                    {
                        "message": "Tone concern: Missing expected hopeful tone",
                        "severity": ValidationSeverity.QUALITY,
                        "category": "tone"
                    }
                ]
            else:
                # No violations
                violations = []
            
            decision = gate.evaluate(violations)
            
            # None should abort (quality issues don't block in Phase 2A)
            assert not gate.should_abort(decision), f"Validation {i+1} should not abort"
        
        # Check statistics
        stats = gate.get_statistics()
        assert stats['total_validations'] == 10, "Should track 10 validations"
        assert stats['quality_count'] == 1, "Should track 1 quality issue"
        assert stats['quality_rate'] == 0.1, "Quality rate should be 10% (1/10)"
        
        # Quality rate exceeds threshold (5%) but doesn't block yet
        assert stats['quality_rate'] > gate.quality_threshold, "Quality rate above threshold"
    
    def test_pass_on_no_violations(self):
        """Test that quality gate passes when no violations present."""
        gate = ProgressiveQualityGate()
        
        # No violations
        violations = []
        
        decision = gate.evaluate(violations)
        
        # Should pass
        assert decision == QualityGateDecision.PASS, "Should pass with no violations"
        assert not gate.should_abort(decision), "Should not abort on PASS"
    
    def test_statistics_reporting(self):
        """Test that quality gate accurately reports statistics."""
        gate = ProgressiveQualityGate(
            critical_threshold=0,
            quality_threshold=0.05
        )
        
        # Run multiple evaluations
        test_cases = [
            # Critical violation
            [{"message": "Lore error", "severity": ValidationSeverity.CRITICAL, "category": "lore"}],
            # Quality issue
            [{"message": "Tone issue", "severity": ValidationSeverity.QUALITY, "category": "tone"}],
            # Warning
            [{"message": "Voice warning", "severity": ValidationSeverity.WARNING, "category": "voice"}],
            # No violations
            [],
            # Multiple issues
            [
                {"message": "Another quality", "severity": ValidationSeverity.QUALITY, "category": "tone"},
                {"message": "Another warning", "severity": ValidationSeverity.WARNING, "category": "voice"}
            ]
        ]
        
        for violations in test_cases:
            gate.evaluate(violations)
        
        stats = gate.get_statistics()
        
        # Verify counts
        assert stats['total_validations'] == 5, "Should have 5 total validations"
        assert stats['critical_count'] == 1, "Should have 1 critical"
        assert stats['quality_count'] == 2, "Should have 2 quality issues"
        assert stats['warning_count'] == 2, "Should have 2 warnings"
        
        # Verify rates
        assert stats['critical_rate'] == 0.2, "Critical rate should be 20% (1/5)"
        assert stats['quality_rate'] == 0.4, "Quality rate should be 40% (2/5)"
        assert stats['warning_rate'] == 0.4, "Warning rate should be 40% (2/5)"
        
        # Verify thresholds in stats
        assert stats['thresholds']['critical'] == 0
        assert stats['thresholds']['quality'] == 0.05
    
    def test_reset_statistics(self):
        """Test that statistics can be reset."""
        gate = ProgressiveQualityGate()
        
        # Run some evaluations
        gate.evaluate([{"message": "Test", "severity": ValidationSeverity.WARNING, "category": "voice"}])
        gate.evaluate([])
        
        stats_before = gate.get_statistics()
        assert stats_before['total_validations'] == 2, "Should have 2 validations before reset"
        
        # Reset
        gate.reset_statistics()
        
        stats_after = gate.get_statistics()
        assert stats_after['total_validations'] == 0, "Should have 0 validations after reset"
        assert stats_after['critical_count'] == 0, "Should have 0 critical after reset"
        assert stats_after['quality_count'] == 0, "Should have 0 quality after reset"
        assert stats_after['warning_count'] == 0, "Should have 0 warnings after reset"
    
    def test_get_report(self):
        """Test that quality gate report is generated correctly."""
        gate = ProgressiveQualityGate(
            critical_threshold=0,
            quality_threshold=0.05
        )
        
        # Run evaluations
        gate.evaluate([{"message": "Critical", "severity": ValidationSeverity.CRITICAL, "category": "lore"}])
        gate.evaluate([])
        gate.evaluate([{"message": "Quality", "severity": ValidationSeverity.QUALITY, "category": "tone"}])
        
        report = gate.get_report()
        
        # Verify report contains expected sections
        assert "Quality Gate Report" in report
        assert "Total Validations: 3" in report
        assert "Critical Violations: 1" in report
        assert "Quality Issues: 1" in report
        assert "Threshold:" in report
