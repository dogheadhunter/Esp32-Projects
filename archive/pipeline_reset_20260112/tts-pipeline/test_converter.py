"""
Test script for ScriptToAudioConverter (Phase 3.1, Step 5)

Quick validation of converter functionality with a single script.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from converter import ScriptToAudioConverter

def test_single_script():
    """Test conversion of a single script."""
    
    # Setup converter
    converter = ScriptToAudioConverter(
        reference_audio_dir='c:/esp32-project/tools/voice-samples/julie',
        output_base_dir='../../audio generation'
    )
    
    print("=" * 80)
    print("ScriptToAudioConverter Test")
    print("=" * 80)
    
    # Load model
    print("\nStep 1: Loading Chatterbox TTS model...")
    converter.load_model()
    
    # Test conversion
    script_path = Path("../../script generation/enhanced_scripts/time_0800_20260112_202417.txt")
    
    if not script_path.exists():
        print(f"\nERROR: Test script not found: {script_path}")
        print("Please specify a valid script path from enhanced_scripts/")
        return
    
    print(f"\nStep 2: Converting script: {script_path.name}")
    result = converter.convert(str(script_path))
    
    # Display results
    print("\n" + "=" * 80)
    print("CONVERSION RESULT")
    print("=" * 80)
    
    if result['success']:
        print(f"✓ SUCCESS!")
        print(f"  Output: {result['output_path']}")
        print(f"  Filename: {result['filename']}")
        print(f"  Attempts: {result['attempts']}")
        print(f"  Mood: {result['metadata'].get('mood', 'N/A')}")
        
        # Check file size
        output_file = Path(result['output_path'])
        if output_file.exists():
            size_kb = output_file.stat().st_size / 1024
            print(f"  File size: {size_kb:.1f} KB")
        
    else:
        print(f"✗ FAILED!")
        print(f"  Error: {result['error']}")
        print(f"  Attempts: {result['attempts']}")
    
    # Cleanup
    print("\nStep 3: Unloading model...")
    converter.unload_model()
    
    print("\n✓ Test complete!")

if __name__ == '__main__':
    test_single_script()
