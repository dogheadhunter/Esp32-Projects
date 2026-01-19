#!/usr/bin/env python3
"""
Example: LLM-Based Script Validation

Demonstrates the new LLM-based validation system with various strategies.
Shows how to use LLM, rule-based, and hybrid validation approaches.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator import ScriptGenerator
from llm_validator import (
    LLMValidator, HybridValidator, validate_script,
    ValidationSeverity
)
from personality_loader import load_personality


def example_1_basic_llm_validation():
    """Example 1: Basic LLM validation."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic LLM Validation")
    print("="*80)
    
    # Sample script with deliberate issues
    script = """
    Hey everyone! So I heard the Institute in Boston is doing some crazy 
    experiments with synths. Also, in the year 2200, things will be 
    totally different! Stay safe out there!
    """
    
    # Load character card
    character_card = load_personality("Julie (2102, Appalachia)")
    
    try:
        # Initialize LLM validator
        validator = LLMValidator(temperature=0.1)
        
        # Validate script
        print("\nValidating script with LLM...")
        result = validator.validate(
            script=script,
            character_card=character_card,
            context={"weather": "sunny", "time_of_day": "morning"}
        )
        
        # Display results
        print(f"\n✓ Valid: {result.is_valid}")
        print(f"✓ Overall Score: {result.overall_score}")
        
        if result.issues:
            print(f"\nIssues Found ({len(result.issues)}):")
            for issue in result.issues:
                severity_icon = {
                    ValidationSeverity.CRITICAL: "❌",
                    ValidationSeverity.WARNING: "⚠️",
                    ValidationSeverity.SUGGESTION: "💡"
                }
                icon = severity_icon.get(issue.severity, "•")
                print(f"{icon} [{issue.category}] {issue.message}")
                if issue.suggestion:
                    print(f"   Suggestion: {issue.suggestion}")
        
        if result.llm_feedback:
            print(f"\nLLM Feedback:")
            print(f"  {result.llm_feedback}")
        
    except Exception as e:
        print(f"⚠️ LLM validation skipped (Ollama not available): {e}")


def example_2_hybrid_validation():
    """Example 2: Hybrid validation (LLM + rules)."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Hybrid Validation (LLM + Rules)")
    print("="*80)
    
    # Script with temporal violation (2200 > 2102)
    script = """
    Happy to have you with us! The weather today is looking sunny. 
    Back in 2200, things were different, but now in 2102, we're 
    rebuilding Appalachia together!
    """
    
    character_card = load_personality("Julie (2102, Appalachia)")
    
    try:
        # Initialize hybrid validator
        validator = HybridValidator(use_llm=True, use_rules=True)
        
        print("\nValidating with hybrid approach...")
        result = validator.validate(
            script=script,
            character_card=character_card
        )
        
        # Display results
        result_dict = result.to_dict()
        print(f"\n✓ Valid: {result_dict['is_valid']}")
        print(f"✓ Score: {result_dict['overall_score']}")
        
        summary = result_dict['summary']
        print(f"\nSummary:")
        print(f"  Critical: {summary['critical']}")
        print(f"  Warnings: {summary['warnings']}")
        print(f"  Suggestions: {summary['suggestions']}")
        
        # Show issues by source
        llm_issues = [i for i in result.issues if i.source == "llm"]
        rule_issues = [i for i in result.issues if i.source == "rule"]
        
        if rule_issues:
            print(f"\nRule-Based Issues ({len(rule_issues)}):")
            for issue in rule_issues:
                print(f"  • {issue.message}")
        
        if llm_issues:
            print(f"\nLLM-Detected Issues ({len(llm_issues)}):")
            for issue in llm_issues:
                print(f"  • {issue.message}")
        
    except Exception as e:
        print(f"⚠️ Hybrid validation failed: {e}")


def example_3_strategy_comparison():
    """Example 3: Compare validation strategies."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Strategy Comparison")
    print("="*80)
    
    # Good script (should pass all strategies)
    script = """
    Um, happy to have you with us! The weather today is sunny and, you know, 
    it's a beautiful morning here in Appalachia. The Responders have been 
    doing great work helping folks rebuild. Stay safe out there!
    """
    
    character_card = load_personality("Julie (2102, Appalachia)")
    
    strategies = ["rules", "llm", "hybrid"]
    
    for strategy in strategies:
        print(f"\n--- {strategy.upper()} Strategy ---")
        
        try:
            result = validate_script(
                script=script,
                character_card=character_card,
                strategy=strategy
            )
            
            result_dict = result.to_dict()
            print(f"Valid: {result_dict['is_valid']}")
            print(f"Issues: {len(result_dict['issues'])}")
            
            if result_dict.get('overall_score'):
                print(f"Score: {result_dict['overall_score']:.2f}")
            
        except Exception as e:
            print(f"⚠️ Skipped ({strategy}): {e}")


def main():
    """Run all examples."""
    print("="*80)
    print("LLM-Based Script Validation Examples")
    print("="*80)
    print("\nThese examples demonstrate the new validation system.")
    print("Some examples require Ollama to be running.")
    
    # Run examples
    example_1_basic_llm_validation()
    example_2_hybrid_validation()
    example_3_strategy_comparison()
    
    print("\n" + "="*80)
    print("All examples completed!")
    print("="*80)
    print("\nFor more information:")
    print("  - See LLM_VALIDATION_GUIDE.md for detailed documentation")
    print("  - See VALIDATION_MIGRATION_GUIDE.md for migration help")
    print("  - Run tests: python tests/test_llm_validator.py")


if __name__ == "__main__":
    main()
