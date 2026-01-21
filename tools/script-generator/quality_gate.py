"""
Progressive Quality Gate Module

Implements tiered validation with configurable thresholds per severity category.
Critical violations veto immediately, quality issues affect score, warnings are logged.
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import logging

from consistency_validator import ValidationSeverity

logger = logging.getLogger(__name__)


class QualityGateDecision(Enum):
    """Quality gate decision outcomes."""
    PASS = "pass"           # All checks passed
    FAIL_CRITICAL = "fail_critical"  # Critical violations found
    FAIL_QUALITY = "fail_quality"    # Quality threshold exceeded
    WARN = "warn"          # Warnings only, can proceed


class ProgressiveQualityGate:
    """
    Progressive quality gate that enforces tiered validation.
    
    Hierarchy:
    - CRITICAL: Lore/temporal violations - immediate veto (threshold: 0)
    - QUALITY: LLM quality issues - affects score (configurable threshold)
    - WARNING: Format/style issues - non-blocking (logged only)
    
    Thresholds can be tightened over time for progressive improvement.
    """
    
    def __init__(
        self,
        critical_threshold: int = 0,      # Max critical violations (should be 0)
        quality_threshold: float = 0.05,   # Max 5% quality issues per total validations
        warning_threshold: Optional[float] = None,  # Warnings don't block
    ):
        """
        Initialize quality gate with thresholds.
        
        Args:
            critical_threshold: Maximum allowed critical violations (default: 0)
            quality_threshold: Maximum allowed quality issue rate (default: 5%)
            warning_threshold: Warning threshold (not enforced, for logging only)
        """
        self.critical_threshold = critical_threshold
        self.quality_threshold = quality_threshold
        self.warning_threshold = warning_threshold
        
        # Track statistics
        self.total_validations = 0
        self.critical_count = 0
        self.quality_count = 0
        self.warning_count = 0
    
    def evaluate(
        self,
        violations: List[Dict[str, Any]],
        segment_metadata: Optional[Dict[str, Any]] = None
    ) -> QualityGateDecision:
        """
        Evaluate validation results against quality gate thresholds.
        
        Args:
            violations: List of validation violations with severity
            segment_metadata: Optional metadata for logging context
        
        Returns:
            QualityGateDecision indicating pass/fail/warn
        """
        self.total_validations += 1
        
        # Count violations by severity
        critical = [v for v in violations if v.get("severity") == ValidationSeverity.CRITICAL]
        quality = [v for v in violations if v.get("severity") == ValidationSeverity.QUALITY]
        warnings = [v for v in violations if v.get("severity") == ValidationSeverity.WARNING]
        
        critical_count = len(critical)
        quality_count = len(quality)
        warning_count = len(warnings)
        
        # Update statistics
        self.critical_count += critical_count
        self.quality_count += quality_count
        self.warning_count += warning_count
        
        # Log violation breakdown
        if violations:
            logger.info(
                f"Validation breakdown: {critical_count} critical, "
                f"{quality_count} quality, {warning_count} warnings"
            )
        
        # Check critical threshold (should always be 0)
        if critical_count > self.critical_threshold:
            logger.error(
                f"CRITICAL THRESHOLD EXCEEDED: {critical_count} critical violations found "
                f"(threshold: {self.critical_threshold})"
            )
            for v in critical:
                logger.error(f"  - {v['message']}")
            return QualityGateDecision.FAIL_CRITICAL
        
        # Check quality threshold (as percentage)
        if self.total_validations > 0:
            quality_rate = self.quality_count / self.total_validations
            
            if quality_rate > self.quality_threshold:
                logger.warning(
                    f"QUALITY THRESHOLD EXCEEDED: {quality_rate:.1%} quality issues "
                    f"(threshold: {self.quality_threshold:.1%})"
                )
                # Note: For now, we log but don't fail on quality threshold
                # This can be made stricter in Phase 3
                # return QualityGateDecision.FAIL_QUALITY
        
        # Warnings don't block
        if warning_count > 0:
            logger.info(f"{warning_count} warnings logged (non-blocking)")
            for w in warnings:
                logger.info(f"  - {w['message']}")
        
        # All checks passed
        if violations:
            return QualityGateDecision.WARN  # Had warnings but can proceed
        else:
            return QualityGateDecision.PASS
    
    def should_abort(self, decision: QualityGateDecision) -> bool:
        """
        Determine if generation should abort based on decision.
        
        Args:
            decision: Quality gate decision
        
        Returns:
            True if generation should abort, False otherwise
        """
        return decision == QualityGateDecision.FAIL_CRITICAL
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get quality gate statistics.
        
        Returns:
            Dictionary with validation statistics
        """
        critical_rate = (
            self.critical_count / self.total_validations 
            if self.total_validations > 0 else 0
        )
        quality_rate = (
            self.quality_count / self.total_validations 
            if self.total_validations > 0 else 0
        )
        warning_rate = (
            self.warning_count / self.total_validations 
            if self.total_validations > 0 else 0
        )
        
        return {
            "total_validations": self.total_validations,
            "critical_count": self.critical_count,
            "quality_count": self.quality_count,
            "warning_count": self.warning_count,
            "critical_rate": critical_rate,
            "quality_rate": quality_rate,
            "warning_rate": warning_rate,
            "thresholds": {
                "critical": self.critical_threshold,
                "quality": self.quality_threshold,
                "warning": self.warning_threshold,
            }
        }
    
    def reset_statistics(self) -> None:
        """Reset statistics counters."""
        self.total_validations = 0
        self.critical_count = 0
        self.quality_count = 0
        self.warning_count = 0
    
    def get_report(self) -> str:
        """
        Generate human-readable quality gate report.
        
        Returns:
            Formatted report string
        """
        stats = self.get_statistics()
        
        lines = [
            "=== Quality Gate Report ===",
            f"Total Validations: {stats['total_validations']}",
            "",
            f"Critical Violations: {stats['critical_count']} ({stats['critical_rate']:.1%})",
            f"  Threshold: {self.critical_threshold} (0%)",
            f"  Status: {'✓ PASS' if stats['critical_count'] <= self.critical_threshold else '✗ FAIL'}",
            "",
            f"Quality Issues: {stats['quality_count']} ({stats['quality_rate']:.1%})",
            f"  Threshold: {self.quality_threshold:.1%}",
            f"  Status: {'✓ PASS' if stats['quality_rate'] <= self.quality_threshold else '⚠ WARN'}",
            "",
            f"Warnings: {stats['warning_count']} ({stats['warning_rate']:.1%})",
            f"  Status: ℹ NON-BLOCKING",
        ]
        
        return "\n".join(lines)
