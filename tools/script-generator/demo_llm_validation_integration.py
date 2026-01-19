#!/usr/bin/env python3
"""
Demo: BroadcastEngine with LLM Validation

Shows the three validation modes in action.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from broadcast_engine import BroadcastEngine


def demo_rules_validation():
    """Demo 1: Rules-based validation (fast, backward compatible)."""
    print("\n" + "="*70)
    print("DEMO 1: Rules-Based Validation (Default - Fast & Backward Compatible)")
    print("="*70)
    
    engine = BroadcastEngine(
        dj_name="Julie (2102, Appalachia)",
        enable_validation=True
        # No validation_mode = defaults to 'rules'
    )
    
    print(f"\n✓ Validation Mode: {engine.validation_mode}")
    print(f"✓ Validator Type: {type(engine.validator).__name__}")
    print("\nThis is the DEFAULT mode - existing code works unchanged!")


def demo_hybrid_validation():
    """Demo 2: Hybrid validation (LLM + rules for comprehensive checks)."""
    print("\n" + "="*70)
    print("DEMO 2: Hybrid Validation (LLM + Rules - Comprehensive Quality)")
    print("="*70)
    
    engine = BroadcastEngine(
        dj_name="Julie (2102, Appalachia)",
        enable_validation=True,
        validation_mode='hybrid'
    )
    
    print(f"\n✓ Validation Mode: {engine.validation_mode}")
    print(f"✓ Validator Type: {type(engine.validator).__name__}")
    print("\nThis mode uses BOTH rule-based AND LLM validation:")
    print("  - Fast rule checks catch hard constraint violations")
    print("  - LLM checks assess quality, tone, and context")
    print("  - Recommended for production use!")


def demo_llm_validation():
    """Demo 3: LLM-only validation (pure quality assessment)."""
    print("\n" + "="*70)
    print("DEMO 3: LLM-Only Validation (Quality-Focused)")
    print("="*70)
    
    engine = BroadcastEngine(
        dj_name="Julie (2102, Appalachia)",
        enable_validation=True,
        validation_mode='llm'
    )
    
    print(f"\n✓ Validation Mode: {engine.validation_mode}")
    print(f"✓ Validator Type: {type(engine.validator).__name__}")
    print("\nThis mode uses ONLY LLM validation:")
    print("  - Slower but more nuanced quality assessment")
    print("  - Best for final review and quality assurance")


def demo_custom_config():
    """Demo 4: Custom LLM configuration."""
    print("\n" + "="*70)
    print("DEMO 4: Custom LLM Configuration")
    print("="*70)
    
    engine = BroadcastEngine(
        dj_name="Julie (2102, Appalachia)",
        enable_validation=True,
        validation_mode='hybrid',
        llm_validation_config={
            'model': 'fluffy/l3-8b-stheno-v3.2',
            'temperature': 0.05,  # Very consistent validation
            'use_llm': True,
            'use_rules': True
        }
    )
    
    print(f"\n✓ Validation Mode: {engine.validation_mode}")
    print(f"✓ Validator Type: {type(engine.validator).__name__}")
    if hasattr(engine.validator, 'llm_validator'):
        print(f"✓ LLM Model: {engine.validator.llm_validator.model}")
        print(f"✓ LLM Temperature: {engine.validator.llm_validator.temperature}")
    print("\nCustom configuration allows fine-tuning:")
    print("  - Choose specific LLM model")
    print("  - Adjust temperature for consistency")
    print("  - Enable/disable LLM and rule components")


def main():
    """Run all demos."""
    print("="*70)
    print("BroadcastEngine LLM Validation Integration Demo")
    print("="*70)
    print("\nThis demonstrates the NEW validation modes added to BroadcastEngine.")
    print("The system is fully backward compatible - existing code works unchanged!")
    
    try:
        demo_rules_validation()
        demo_hybrid_validation()
        demo_llm_validation()
        demo_custom_config()
        
        print("\n" + "="*70)
        print("Summary")
        print("="*70)
        print("\n✓ THREE validation strategies available:")
        print("  1. 'rules'  - Fast, deterministic (DEFAULT)")
        print("  2. 'hybrid' - Comprehensive LLM + rules (RECOMMENDED)")
        print("  3. 'llm'    - Quality-focused LLM only")
        print("\n✓ Fully backward compatible:")
        print("  - Old code works without changes")
        print("  - Defaults to rules-based validation")
        print("\n✓ Graceful degradation:")
        print("  - Falls back to rules if Ollama unavailable")
        print("  - Clear error messages and warnings")
        print("\n✓ Rich context for LLM:")
        print("  - Weather, time, session history")
        print("  - Story context, region, topics")
        print("  - All template vars available")
        
        print("\n" + "="*70)
        print("✓ Integration Complete!")
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
