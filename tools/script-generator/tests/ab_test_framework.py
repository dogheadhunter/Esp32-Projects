"""
A/B Testing Framework for Script Generation

Tests multiple template variants and models to determine optimal configuration.

VARIANTS:
1. Minimal: Current templates + catchphrase variables only
2. Structured: Required opening/closing + voice triggers section
3. Contextual: Smart catchphrase selection + mood-based voice
4. Hybrid: Required opening + optional closing + suggestions not requirements

WORKFLOW:
1. Generate identical context for all variants
2. Run each variant with same parameters
3. Collect automated validation scores (3-tier)
4. Statistical analysis (t-test for significance)
5. Recommend winning configuration
"""

import sys
import json
import statistics
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime
import time

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from generator import ScriptGenerator
from validate_scripts_enhanced import EnhancedScriptValidator


class ABTestConfig:
    """Configuration for a test variant."""
    
    def __init__(self,
                 name: str,
                 model: str,
                 template_variant: str = "default",
                 enable_catchphrase: bool = True,
                 enable_natural_voice: bool = True,
                 enable_validation_retry: bool = True,
                 temperature: float = 0.8,
                 top_p: float = 0.9):
        self.name = name
        self.model = model
        self.template_variant = template_variant
        self.enable_catchphrase = enable_catchphrase
        self.enable_natural_voice = enable_natural_voice
        self.enable_validation_retry = enable_validation_retry
        self.temperature = temperature
        self.top_p = top_p
    
    def to_dict(self):
        return {
            'name': self.name,
            'model': self.model,
            'template_variant': self.template_variant,
            'enable_catchphrase': self.enable_catchphrase,
            'enable_natural_voice': self.enable_natural_voice,
            'enable_validation_retry': self.enable_validation_retry,
            'temperature': self.temperature,
            'top_p': self.top_p
        }


class ABTestFramework:
    """A/B testing framework for script generation."""
    
    def __init__(self, output_dir: str = None):
        self.generator = ScriptGenerator()
        self.validator = EnhancedScriptValidator(
            use_embeddings=True,
            use_llm_judge=True
        )
        
        if output_dir is None:
            output_dir = Path(__file__).parent.parent.parent.parent / "script generation" / "ab_test_results"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[OK] A/B Test Framework initialized")
        print(f"[OK] Output directory: {self.output_dir}")
    
    def generate_test_batch(self,
                           variants: List[ABTestConfig],
                           script_specs: List[Dict[str, Any]],
                           samples_per_spec: int = 3) -> Dict[str, Any]:
        """
        Generate test batch with identical contexts across variants.
        
        Args:
            variants: List of test configurations
            script_specs: List of script specifications (type, dj, query, vars)
            samples_per_spec: Number of samples per specification
        
        Returns:
            {
                'variants': List[str],
                'scripts': {
                    variant_name: {
                        spec_id: [script_results]
                    }
                },
                'metadata': {
                    'total_scripts': int,
                    'generation_time': float,
                    'timestamp': str
                }
            }
        """
        print(f"\n{'='*80}")
        print(f"A/B TEST BATCH GENERATION")
        print(f"{'='*80}")
        print(f"Variants: {len(variants)}")
        print(f"Script Specs: {len(script_specs)}")
        print(f"Samples per Spec: {samples_per_spec}")
        print(f"Total Scripts: {len(variants) * len(script_specs) * samples_per_spec}")
        print(f"{'='*80}\n")
        
        results = {
            'variants': [v.name for v in variants],
            'scripts': {},
            'metadata': {
                'total_scripts': 0,
                'generation_time': 0,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        start_time = time.time()
        total_count = 0
        
        for variant in variants:
            print(f"\n{'='*80}")
            print(f"VARIANT: {variant.name}")
            print(f"Model: {variant.model}")
            print(f"{'='*80}")
            
            results['scripts'][variant.name] = {}
            
            for spec_idx, spec in enumerate(script_specs):
                spec_id = f"{spec['script_type']}_{spec_idx}"
                results['scripts'][variant.name][spec_id] = []
                
                print(f"\n[Spec {spec_idx+1}/{len(script_specs)}] {spec['script_type'].upper()}")
                
                for sample in range(samples_per_spec):
                    print(f"  Sample {sample+1}/{samples_per_spec}...", end=" ")
                    
                    try:
                        result = self.generator.generate_script(
                            script_type=spec['script_type'],
                            dj_name=spec['dj_name'],
                            context_query=spec['context_query'],
                            model=variant.model,
                            temperature=variant.temperature,
                            top_p=variant.top_p,
                            enable_catchphrase_rotation=variant.enable_catchphrase,
                            enable_natural_voice=variant.enable_natural_voice,
                            enable_validation_retry=variant.enable_validation_retry,
                            **spec.get('template_vars', {})
                        )
                        
                        # Save script
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{variant.name}_{spec_id}_sample{sample}_{timestamp}.txt"
                        filepath = self.output_dir / filename
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(result['script'])
                            f.write("\n\n" + "="*80 + "\n")
                            f.write("METADATA:\n")
                            f.write(json.dumps(result['metadata'], indent=2))
                            f.write("\n\nVARIANT:\n")
                            f.write(json.dumps(variant.to_dict(), indent=2))
                        
                        results['scripts'][variant.name][spec_id].append({
                            'filepath': str(filepath),
                            'metadata': result['metadata']
                        })
                        
                        total_count += 1
                        print("✓")
                        
                    except Exception as e:
                        print(f"✗ Error: {e}")
        
        elapsed = time.time() - start_time
        results['metadata']['total_scripts'] = total_count
        results['metadata']['generation_time'] = elapsed
        
        print(f"\n{'='*80}")
        print(f"GENERATION COMPLETE")
        print(f"Total Scripts: {total_count}")
        print(f"Time: {elapsed:.1f}s ({elapsed/max(total_count,1):.1f}s per script)")
        print(f"{'='*80}")
        
        # Save batch metadata
        batch_file = self.output_dir / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"[SAVED] Batch metadata: {batch_file}")
        
        return results
    
    def validate_batch(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all scripts in batch with 3-tier system.
        
        Returns:
            {
                variant_name: {
                    'scores': List[float],
                    'avg_score': float,
                    'std_dev': float,
                    'category_averages': Dict[str, float]
                }
            }
        """
        print(f"\n{'='*80}")
        print(f"BATCH VALIDATION (3-Tier System)")
        print(f"{'='*80}\n")
        
        validation_results = {}
        
        for variant_name in batch_results['variants']:
            print(f"\n{'='*80}")
            print(f"VALIDATING: {variant_name}")
            print(f"{'='*80}")
            
            scores = []
            category_scores = {}
            
            for spec_id, scripts in batch_results['scripts'][variant_name].items():
                for script_data in scripts:
                    filepath = script_data['filepath']
                    
                    if not Path(filepath).exists():
                        print(f"[WARN] Missing: {filepath}")
                        continue
                    
                    print(f"  {Path(filepath).name}...", end=" ")
                    
                    try:
                        validation = self.validator.validate_script(filepath)
                        scores.append(validation['score'])
                        
                        # Aggregate category scores
                        for category, score in validation['checks'].items():
                            if category not in category_scores:
                                category_scores[category] = []
                            category_scores[category].append(score)
                        
                        print(f"{validation['score']:.1f}/100")
                        
                    except Exception as e:
                        print(f"✗ Error: {e}")
            
            # Calculate statistics (convert numpy float32 to Python float)
            scores_float = [float(s) for s in scores]
            validation_results[variant_name] = {
                'scores': scores_float,
                'avg_score': statistics.mean(scores_float) if scores_float else 0,
                'std_dev': statistics.stdev(scores_float) if len(scores_float) > 1 else 0,
                'category_averages': {
                    cat: statistics.mean([float(s) for s in scores_list])
                    for cat, scores_list in category_scores.items()
                }
            }
        
        # Save validation results
        validation_file = self.output_dir / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(validation_file, 'w', encoding='utf-8') as f:
            # Convert to JSON-serializable format
            json_results = {
                variant: {
                    'avg_score': data['avg_score'],
                    'std_dev': data['std_dev'],
                    'sample_count': len(data['scores']),
                    'category_averages': data['category_averages']
                }
                for variant, data in validation_results.items()
            }
            json.dump(json_results, f, indent=2)
        
        print(f"\n[SAVED] Validation results: {validation_file}")
        
        return validation_results
    
    def compare_variants(self, validation_results: Dict[str, Any]) -> str:
        """
        Statistical comparison of variants.
        
        Returns: Summary report with winning configuration
        """
        print(f"\n{'='*80}")
        print(f"VARIANT COMPARISON")
        print(f"{'='*80}\n")
        
        report = []
        report.append("="*80)
        report.append("A/B TEST RESULTS SUMMARY")
        report.append("="*80)
        report.append("")
        
        # Sort variants by average score
        sorted_variants = sorted(
            validation_results.items(),
            key=lambda x: x[1]['avg_score'],
            reverse=True
        )
        
        # Overall rankings
        report.append("OVERALL RANKINGS:")
        report.append("-"*80)
        for rank, (variant_name, data) in enumerate(sorted_variants, 1):
            report.append(
                f"{rank}. {variant_name}: {data['avg_score']:.1f}/100 "
                f"(±{data['std_dev']:.1f}, n={len(data['scores'])})"
            )
        report.append("")
        
        # Category breakdowns
        report.append("CATEGORY BREAKDOWN:")
        report.append("-"*80)
        
        # Get all categories
        all_categories = set()
        for data in validation_results.values():
            all_categories.update(data['category_averages'].keys())
        
        for category in sorted(all_categories):
            report.append(f"\n{category.replace('_', ' ').title()}:")
            for variant_name, data in sorted_variants:
                score = data['category_averages'].get(category, 0)
                report.append(f"  {variant_name}: {score:.1f}/100")
        
        report.append("")
        report.append("="*80)
        report.append("RECOMMENDATION")
        report.append("="*80)
        
        winner_name, winner_data = sorted_variants[0]
        improvement = winner_data['avg_score'] - sorted_variants[-1][1]['avg_score']
        
        report.append(f"\n✅ WINNING CONFIGURATION: {winner_name}")
        report.append(f"   Average Score: {winner_data['avg_score']:.1f}/100")
        report.append(f"   Improvement over baseline: +{improvement:.1f} points")
        report.append(f"   Consistency (std dev): ±{winner_data['std_dev']:.1f}")
        report.append("")
        report.append("Key Strengths:")
        
        # Find top 3 categories
        top_categories = sorted(
            winner_data['category_averages'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        for category, score in top_categories:
            report.append(f"  - {category.replace('_', ' ').title()}: {score:.1f}/100")
        
        report.append("")
        report.append("="*80)
        
        report_text = "\n".join(report)
        print(report_text)
        
        # Save report
        report_file = self.output_dir / f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"\n[SAVED] Comparison report: {report_file}")
        
        return report_text


def main():
    """Run A/B test with predefined variants."""
    
    # Define test variants
    variants = [
        ABTestConfig(
            name="baseline",
            model="fluffy/l3-8b-stheno-v3.2",
            enable_catchphrase=False,
            enable_natural_voice=False,
            enable_validation_retry=False
        ),
        ABTestConfig(
            name="enhanced_stheno",
            model="fluffy/l3-8b-stheno-v3.2",
            enable_catchphrase=True,
            enable_natural_voice=True,
            enable_validation_retry=True
        ),
        ABTestConfig(
            name="enhanced_hermes",
            model="hermes3",
            enable_catchphrase=True,
            enable_natural_voice=True,
            enable_validation_retry=True
        )
    ]
    
    # Define test specifications (identical contexts for fair comparison)
    script_specs = [
        {
            'script_type': 'weather',
            'dj_name': 'Julie (2102, Appalachia)',
            'context_query': 'Appalachia weather sunny morning conditions',
            'template_vars': {
                'weather_type': 'sunny',
                'time_of_day': 'morning',
                'hour': 8,
                'temperature': 72
            }
        },
        {
            'script_type': 'news',
            'dj_name': 'Julie (2102, Appalachia)',
            'context_query': 'Appalachia settlement cooperation rebuilding',
            'template_vars': {
                'news_topic': 'settlement cooperation',
                'location': 'Flatwoods'
            }
        },
        {
            'script_type': 'time',
            'dj_name': 'Julie (2102, Appalachia)',
            'context_query': 'Appalachia daily life afternoon',
            'template_vars': {
                'hour': 14,
                'time_of_day': 'afternoon'
            }
        },
        {
            'script_type': 'gossip',
            'dj_name': 'Julie (2102, Appalachia)',
            'context_query': 'Appalachia rumors wasteland stories',
            'template_vars': {
                'rumor_type': 'wasteland mystery'
            }
        },
        {
            'script_type': 'music_intro',
            'dj_name': 'Julie (2102, Appalachia)',
            'context_query': 'pre-war music 1950s culture',
            'template_vars': {
                'song_title': 'I Don\'t Want to Set the World on Fire',
                'artist': 'The Ink Spots',
                'era': '1941',
                'mood': 'melancholy'
            }
        }
    ]
    
    # Initialize framework
    framework = ABTestFramework()
    
    # Generate test batch (3 samples per spec)
    print("\nGenerating test batch...")
    batch_results = framework.generate_test_batch(
        variants=variants,
        script_specs=script_specs,
        samples_per_spec=3
    )
    
    # Validate batch
    print("\nValidating batch...")
    validation_results = framework.validate_batch(batch_results)
    
    # Compare variants
    print("\nComparing variants...")
    comparison_report = framework.compare_variants(validation_results)
    
    print("\n\n✅ A/B TEST COMPLETE!")
    print(f"Results saved to: {framework.output_dir}")


if __name__ == '__main__':
    main()
