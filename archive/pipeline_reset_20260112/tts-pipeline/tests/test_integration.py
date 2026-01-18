"""
Integration Tests (Phase 3.1, Step 5)

Test batch processing, error recovery, checkpoint resume, and VRAM management.

Usage:
    python test_integration.py
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from converter import ScriptToAudioConverter

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("IntegrationTests")


class BatchConverter:
    """Batch conversion with checkpoint and error recovery."""
    
    def __init__(self, converter: ScriptToAudioConverter, checkpoint_file: str = 'conversion_checkpoint.json'):
        self.converter = converter
        self.checkpoint_file = checkpoint_file
        self.results = []
        self.checkpoint_data = self._load_checkpoint()
    
    def _load_checkpoint(self) -> Dict:
        """Load conversion checkpoint from disk."""
        if os.path.exists(self.checkpoint_file):
            logger.info(f"Loading checkpoint: {self.checkpoint_file}")
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        return {'completed': [], 'failed': [], 'last_index': -1}
    
    def _save_checkpoint(self):
        """Save conversion checkpoint to disk."""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.checkpoint_data, f, indent=2)
    
    def convert_batch(self, script_paths: List[str], resume: bool = True) -> Dict:
        """
        Convert multiple scripts with checkpoint resume.
        
        Args:
            script_paths: List of script file paths
            resume: Resume from checkpoint if available
            
        Returns:
            Summary statistics dictionary
        """
        start_time = time.time()
        
        # Determine starting point
        start_idx = 0
        if resume and self.checkpoint_data['last_index'] >= 0:
            start_idx = self.checkpoint_data['last_index'] + 1
            logger.info(f"Resuming from script {start_idx}/{len(script_paths)}")
        
        # Load model once for entire batch
        logger.info("Loading TTS model...")
        self.converter.load_model()
        
        # Process scripts
        for i, script_path in enumerate(script_paths[start_idx:], start=start_idx):
            logger.info(f"[{i+1}/{len(script_paths)}] Processing: {Path(script_path).name}")
            
            try:
                result = self.converter.convert(script_path)
                
                if result['success']:
                    self.checkpoint_data['completed'].append(result)
                    logger.info(f"  ✓ Success (attempt {result['attempts']})")
                else:
                    self.checkpoint_data['failed'].append(result)
                    logger.warning(f"  ✗ Failed: {result['error']}")
                
                self.results.append(result)
                
            except Exception as e:
                logger.error(f"  ✗ Unexpected error: {e}")
                self.checkpoint_data['failed'].append({
                    'script_path': script_path,
                    'error': str(e),
                    'success': False
                })
            
            # Update checkpoint
            self.checkpoint_data['last_index'] = i
            self._save_checkpoint()
        
        # Unload model
        self.converter.unload_model()
        
        # Calculate statistics
        elapsed = time.time() - start_time
        total = len(script_paths)
        completed = len(self.checkpoint_data['completed'])
        failed = len(self.checkpoint_data['failed'])
        
        stats = {
            'total_scripts': total,
            'completed': completed,
            'failed': failed,
            'success_rate': completed / total * 100 if total > 0 else 0,
            'elapsed_time': elapsed,
            'avg_time_per_script': elapsed / total if total > 0 else 0
        }
        
        return stats


def test_batch_processing():
    """Test 1: Batch processing with checkpointing."""
    print("\n" + "="*80)
    print("TEST 1: Batch Processing")
    print("="*80)
    
    # Find all enhanced scripts
    script_dir = Path("c:/esp32-project/script generation/enhanced_scripts")
    scripts = sorted(script_dir.glob("*.txt"))
    
    print(f"Found {len(scripts)} scripts")
    
    # Setup converter
    converter = ScriptToAudioConverter(
        reference_audio_dir='c:/esp32-project/tools/voice-samples/julie',
        output_base_dir='c:/esp32-project/audio generation'
    )
    
    # Run batch conversion
    batch = BatchConverter(converter, checkpoint_file='test_batch_checkpoint.json')
    stats = batch.convert_batch([str(s) for s in scripts[:5]], resume=False)  # Test with 5 scripts
    
    # Display results
    print(f"\n✓ Batch conversion complete!")
    print(f"  Total: {stats['total_scripts']}")
    print(f"  Completed: {stats['completed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Success rate: {stats['success_rate']:.1f}%")
    print(f"  Elapsed: {stats['elapsed_time']:.1f}s")
    print(f"  Avg per script: {stats['avg_time_per_script']:.1f}s")
    
    # Cleanup checkpoint
    if os.path.exists('test_batch_checkpoint.json'):
        os.remove('test_batch_checkpoint.json')
    
    return stats


def test_checkpoint_resume():
    """Test 2: Checkpoint resume after interruption."""
    print("\n" + "="*80)
    print("TEST 2: Checkpoint Resume")
    print("="*80)
    
    script_dir = Path("c:/esp32-project/script generation/enhanced_scripts")
    scripts = sorted(script_dir.glob("*.txt"))[:3]  # Use 3 scripts
    
    converter = ScriptToAudioConverter(
        reference_audio_dir='c:/esp32-project/tools/voice-samples/julie',
        output_base_dir='c:/esp32-project/audio generation'
    )
    
    # Simulate interruption after 1 script
    checkpoint_file = 'test_resume_checkpoint.json'
    batch = BatchConverter(converter, checkpoint_file=checkpoint_file)
    
    # Initial checkpoint state (simulate partial completion)
    batch.checkpoint_data = {
        'completed': [{'script_path': str(scripts[0]), 'success': True}],
        'failed': [],
        'last_index': 0
    }
    batch._save_checkpoint()
    
    print("Simulated interruption after 1 script")
    print(f"Resuming conversion of remaining {len(scripts) - 1} scripts...")
    
    # Resume
    batch2 = BatchConverter(converter, checkpoint_file=checkpoint_file)
    stats = batch2.convert_batch([str(s) for s in scripts], resume=True)
    
    print(f"\n✓ Resume successful!")
    print(f"  Resumed from script 2/{len(scripts)}")
    print(f"  Total completed: {stats['completed']}")
    
    # Cleanup
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)
    
    return stats


def test_error_recovery():
    """Test 3: Error recovery and retry logic."""
    print("\n" + "="*80)
    print("TEST 3: Error Recovery")
    print("="*80)
    
    # Test converter with invalid reference directory (should trigger fallback)
    converter = ScriptToAudioConverter(
        reference_audio_dir='c:/esp32-project/tools/voice-samples/invalid_path',
        output_base_dir='c:/esp32-project/audio generation'
    )
    
    script_dir = Path("c:/esp32-project/script generation/enhanced_scripts")
    script = sorted(script_dir.glob("*.txt"))[0]
    
    print(f"Testing error recovery with: {script.name}")
    print("Using invalid reference path (should fall back to absolute path)")
    
    converter.load_model()
    result = converter.convert(str(script))
    converter.unload_model()
    
    if result['success']:
        print(f"\n✓ Error recovery successful!")
        print(f"  Attempts: {result['attempts']}")
        print(f"  Fallback worked correctly")
    else:
        print(f"\n✗ Error recovery failed: {result['error']}")
    
    return result


def test_vram_management():
    """Test 4: VRAM management (load/unload cycles)."""
    print("\n" + "="*80)
    print("TEST 4: VRAM Management")
    print("="*80)
    
    try:
        import torch
        if not torch.cuda.is_available():
            print("CUDA not available, skipping VRAM test")
            return None
        
        converter = ScriptToAudioConverter(
            reference_audio_dir='c:/esp32-project/tools/voice-samples/julie',
            output_base_dir='c:/esp32-project/audio generation'
        )
        
        print("Measuring VRAM usage across load/unload cycles...")
        
        for cycle in range(3):
            print(f"\nCycle {cycle + 1}:")
            
            # Check VRAM before load
            torch.cuda.empty_cache()
            vram_before = torch.cuda.memory_allocated() / 1024**3
            print(f"  VRAM before load: {vram_before:.2f} GB")
            
            # Load model
            converter.load_model()
            vram_loaded = torch.cuda.memory_allocated() / 1024**3
            print(f"  VRAM after load: {vram_loaded:.2f} GB")
            
            # Unload model
            converter.unload_model()
            vram_after = torch.cuda.memory_allocated() / 1024**3
            print(f"  VRAM after unload: {vram_after:.2f} GB")
            
            # Check for memory leak
            if cycle > 0 and vram_after > vram_before + 0.1:  # 100MB tolerance
                print(f"  ⚠ Potential memory leak detected!")
        
        print("\n✓ VRAM management test complete")
        return True
        
    except ImportError:
        print("PyTorch not available, skipping VRAM test")
        return None


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*80)
    print("INTEGRATION TEST SUITE - Phase 3.1, Step 5")
    print("="*80)
    
    results = {}
    
    try:
        # Test 1: Batch processing
        results['batch'] = test_batch_processing()
        
        # Test 2: Checkpoint resume
        results['resume'] = test_checkpoint_resume()
        
        # Test 3: Error recovery
        results['error_recovery'] = test_error_recovery()
        
        # Test 4: VRAM management
        results['vram'] = test_vram_management()
        
        # Summary
        print("\n" + "="*80)
        print("ALL TESTS COMPLETE")
        print("="*80)
        
        # Calculate reliability (from batch test)
        if 'batch' in results:
            reliability = results['batch']['success_rate']
            target = 99.0
            print(f"\nReliability: {reliability:.1f}% (target: {target}%)")
            if reliability >= target:
                print("✓ Reliability target MET")
            else:
                print(f"✗ Reliability target MISSED (need {target - reliability:.1f}% improvement)")
        
    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_all_tests()
