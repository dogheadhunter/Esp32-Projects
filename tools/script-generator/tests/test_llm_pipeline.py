"""
Tests for Unified LLM Pipeline

Phase 3 Checkpoint 3.1: Validation-guided generation tests.

Tests cover:
- Constraint embedding in prompts
- Integration with RAG Cache (Phase 1)
- Integration with Scheduler (Phase 2)
- Metrics tracking
- Edge cases and error handling
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass
from typing import Dict, Any, List

# Import modules under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_pipeline import LLMPipeline, GenerationResult
from segment_plan import SegmentPlan, SegmentType, Priority, ValidationConstraints


class TestConstraintEmbedding(unittest.TestCase):
    """Test constraint conversion to prompt text"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_ollama = Mock()
        self.pipeline = LLMPipeline(self.mock_ollama)
    
    def test_constraint_embedding_in_prompt(self):
        """Test that constraints are properly embedded in system prompt"""
        constraints = ValidationConstraints(
            max_year=2287,
            forbidden_topics=["Institute", "Railroad"],
            forbidden_factions=["Enclave"],
            required_tone="informative",
            max_length=400
        )
        
        dj_context = {
            'name': 'Julie',
            'year': 2287,
            'region': 'Commonwealth',
            'personality': {'tone': 'casual'}
        }
        
        prompt = self.pipeline._build_constraint_embedded_prompt(
            dj_name='Julie',
            year=2287,
            region='Commonwealth',
            tone='casual',
            template='news',
            constraints=constraints,
            lore_chunks=["Test lore chunk"]
        )
        
        # Verify constraints are in prompt
        self.assertIn('2287', prompt)
        self.assertIn('Institute', prompt)
        self.assertIn('Railroad', prompt)
        self.assertIn('Enclave', prompt)
        self.assertIn('Julie', prompt)
    
    def test_empty_constraints_handling(self):
        """Test handling of None/empty constraints"""
        prompt = self.pipeline._build_constraint_embedded_prompt(
            dj_name='Julie',
            year=2287,
            region='Commonwealth',
            tone='casual',
            template='news',
            constraints=None,
            lore_chunks=[]
        )
        
        # Should still generate valid prompt
        self.assertIn('Julie', prompt)
        self.assertIn('news', prompt)
    
    def test_user_prompt_generation(self):
        """Test user prompt generation for different templates"""
        templates = ['news', 'weather', 'gossip', 'story', 'time_check']
        
        for template in templates:
            prompt = self.pipeline._build_user_prompt(template, {})
            self.assertIsInstance(prompt, str)
            self.assertGreater(len(prompt), 0)


class TestValidationGuidedGeneration(unittest.TestCase):
    """Test end-to-end validation-guided generation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_ollama = Mock()
        self.pipeline = LLMPipeline(self.mock_ollama)
        
        # Mock successful LLM response
        self.mock_ollama.chat.return_value = {
            'message': {
                'content': 'This is a generated news script about the Commonwealth.'
            }
        }
    
    def test_single_llm_call_generation(self):
        """Test that only one LLM call is made (key innovation)"""
        constraints = ValidationConstraints(
            max_year=2287,
            forbidden_topics=["Institute"],
            required_tone="casual"
        )
        
        dj_context = {
            'name': 'Julie',
            'year': 2287,
            'region': 'Commonwealth'
        }
        
        result = self.pipeline.generate_with_validation(
            template='news',
            lore_chunks=["Test chunk"],
            constraints=constraints,
            dj_context=dj_context
        )
        
        # Verify single LLM call
        self.assertEqual(self.mock_ollama.chat.call_count, 1)
        self.assertEqual(result.llm_calls, 1)
        self.assertEqual(result.validation_source, 'embedded_constraints')
    
    def test_generation_result_structure(self):
        """Test that GenerationResult has all required fields"""
        constraints = ValidationConstraints(max_year=2287)
        dj_context = {'name': 'Julie', 'year': 2287}
        
        result = self.pipeline.generate_with_validation(
            template='news',
            lore_chunks=[],
            constraints=constraints,
            dj_context=dj_context
        )
        
        # Verify result structure
        self.assertIsInstance(result, GenerationResult)
        self.assertIsInstance(result.script, str)
        self.assertIsInstance(result.is_valid, bool)
        self.assertIsInstance(result.generation_time_ms, int)
        self.assertIsInstance(result.llm_calls, int)
        self.assertIsInstance(result.metadata, dict)
    
    def test_error_handling(self):
        """Test error handling when LLM call fails"""
        self.mock_ollama.chat.side_effect = Exception("LLM connection error")
        
        constraints = ValidationConstraints(max_year=2287)
        dj_context = {'name': 'Julie', 'year': 2287}
        
        result = self.pipeline.generate_with_validation(
            template='news',
            lore_chunks=[],
            constraints=constraints,
            dj_context=dj_context
        )
        
        # Should handle error gracefully
        self.assertFalse(result.is_valid)
        self.assertEqual(result.validation_source, 'generation_error')
        self.assertIn('error', result.metadata)


class TestRAGCacheIntegration(unittest.TestCase):
    """Test integration with RAG Cache (Phase 1)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_ollama = Mock()
        self.mock_rag_cache = Mock()
        self.pipeline = LLMPipeline(self.mock_ollama, self.mock_rag_cache)
        
        self.mock_ollama.chat.return_value = {
            'message': {'content': 'Generated script'}
        }
    
    def test_topic_parameter_for_cache(self):
        """Test that topic parameter is used for cache optimization"""
        constraints = ValidationConstraints(max_year=2287)
        dj_context = {'name': 'Julie', 'year': 2287}
        
        # Mock cache statistics
        self.mock_rag_cache.get_statistics.return_value = {
            'hit_rate': 0.75
        }
        
        result = self.pipeline.generate_with_validation(
            template='news',
            lore_chunks=[],
            constraints=constraints,
            dj_context=dj_context,
            topic='current_events'  # Phase 1 integration
        )
        
        # Verify topic was tracked
        self.assertIn('topic', result.metadata)
        self.assertEqual(result.metadata['topic'], 'current_events')
    
    def test_cache_hit_tracking(self):
        """Test that cache hits are tracked in metrics"""
        self.mock_rag_cache.get_statistics.return_value = {
            'hit_rate': 0.80  # High cache hit rate
        }
        
        constraints = ValidationConstraints(max_year=2287)
        dj_context = {'name': 'Julie', 'year': 2287}
        
        # Generate multiple times
        for _ in range(5):
            self.pipeline.generate_with_validation(
                template='news',
                lore_chunks=[],
                constraints=constraints,
                dj_context=dj_context,
                topic='current_events'
            )
        
        metrics = self.pipeline.get_metrics()
        self.assertGreater(metrics['cache_hits'], 0)


class TestSchedulerIntegration(unittest.TestCase):
    """Test integration with Enhanced BroadcastScheduler (Phase 2)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_ollama = Mock()
        self.pipeline = LLMPipeline(self.mock_ollama)
        
        self.mock_ollama.chat.return_value = {
            'message': {'content': 'Generated script'}
        }
    
    def test_generate_from_segment_plan(self):
        """Test generation from SegmentPlan (Phase 2 integration)"""
        constraints = ValidationConstraints(
            max_year=2287,
            forbidden_topics=["Institute"],
            required_tone="casual"
        )
        
        # Create mock SegmentPlan
        plan = Mock(spec=SegmentPlan)
        plan.segment_type = Mock()
        plan.segment_type.value = 'news'
        plan.constraints = constraints
        plan.metadata = {'lore_chunks': ["Test chunk"]}
        plan.get_rag_topic = Mock(return_value='current_events')
        
        dj_context = {'name': 'Julie', 'year': 2287}
        
        result = self.pipeline.generate_from_plan(plan, dj_context)
        
        # Verify integration
        self.assertIsInstance(result, GenerationResult)
        self.assertEqual(result.llm_calls, 1)
        self.assertTrue(plan.get_rag_topic.called)
    
    def test_plan_constraint_extraction(self):
        """Test that constraints are properly extracted from plan"""
        constraints = ValidationConstraints(
            max_year=2102,
            forbidden_factions=["Brotherhood of Steel"]
        )
        
        plan = Mock(spec=SegmentPlan)
        plan.segment_type = Mock()
        plan.segment_type.value = 'gossip'
        plan.constraints = constraints
        plan.metadata = {}
        plan.get_rag_topic = Mock(return_value='character_relationships')
        
        dj_context = {'name': 'Travis', 'year': 2102}
        
        result = self.pipeline.generate_from_plan(plan, dj_context)
        
        # Verify constraints were used
        self.assertEqual(result.metadata['dj'], 'Travis')
        self.assertEqual(result.metadata['year'], 2102)


class TestMetricsTracking(unittest.TestCase):
    """Test performance metrics tracking"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_ollama = Mock()
        self.pipeline = LLMPipeline(self.mock_ollama)
        
        self.mock_ollama.chat.return_value = {
            'message': {'content': 'Generated script'}
        }
    
    def test_metrics_initialization(self):
        """Test that metrics start at zero"""
        metrics = self.pipeline.get_metrics()
        
        self.assertEqual(metrics['total_generations'], 0)
        self.assertEqual(metrics['total_llm_calls'], 0)
        self.assertEqual(metrics['validation_guided_generations'], 0)
    
    def test_metrics_incrementation(self):
        """Test that metrics increment correctly"""
        constraints = ValidationConstraints(max_year=2287)
        dj_context = {'name': 'Julie', 'year': 2287}
        
        # Generate 3 times
        for _ in range(3):
            self.pipeline.generate_with_validation(
                template='news',
                lore_chunks=[],
                constraints=constraints,
                dj_context=dj_context
            )
        
        metrics = self.pipeline.get_metrics()
        
        self.assertEqual(metrics['total_generations'], 3)
        self.assertEqual(metrics['total_llm_calls'], 3)
        self.assertEqual(metrics['validation_guided_generations'], 3)
        self.assertEqual(metrics['avg_llm_calls_per_segment'], 1.0)  # Key metric!
    
    def test_metrics_reset(self):
        """Test metrics reset functionality"""
        constraints = ValidationConstraints(max_year=2287)
        dj_context = {'name': 'Julie', 'year': 2287}
        
        # Generate some
        self.pipeline.generate_with_validation(
            template='news',
            lore_chunks=[],
            constraints=constraints,
            dj_context=dj_context
        )
        
        # Reset
        self.pipeline.reset_metrics()
        
        metrics = self.pipeline.get_metrics()
        self.assertEqual(metrics['total_generations'], 0)
    
    def test_average_calculations(self):
        """Test that averages are calculated correctly"""
        constraints = ValidationConstraints(max_year=2287)
        dj_context = {'name': 'Julie', 'year': 2287}
        
        for _ in range(10):
            self.pipeline.generate_with_validation(
                template='news',
                lore_chunks=[],
                constraints=constraints,
                dj_context=dj_context
            )
        
        metrics = self.pipeline.get_metrics()
        
        # Verify calculations
        self.assertGreater(metrics['avg_generation_time_ms'], 0)
        self.assertEqual(metrics['avg_llm_calls_per_segment'], 1.0)
        self.assertGreater(metrics['validation_guided_percentage'], 99.0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_ollama = Mock()
        self.pipeline = LLMPipeline(self.mock_ollama)
    
    def test_empty_lore_chunks(self):
        """Test generation with no lore chunks"""
        self.mock_ollama.chat.return_value = {
            'message': {'content': 'Generated script'}
        }
        
        constraints = ValidationConstraints(max_year=2287)
        dj_context = {'name': 'Julie', 'year': 2287}
        
        result = self.pipeline.generate_with_validation(
            template='news',
            lore_chunks=[],  # Empty
            constraints=constraints,
            dj_context=dj_context
        )
        
        self.assertTrue(result.is_valid)
    
    def test_missing_dj_context_fields(self):
        """Test generation with incomplete DJ context"""
        self.mock_ollama.chat.return_value = {
            'message': {'content': 'Generated script'}
        }
        
        constraints = ValidationConstraints(max_year=2287)
        dj_context = {}  # Empty context
        
        result = self.pipeline.generate_with_validation(
            template='news',
            lore_chunks=[],
            constraints=constraints,
            dj_context=dj_context
        )
        
        # Should use defaults
        self.assertTrue(result.is_valid)
        self.assertIn('dj', result.metadata)
    
    def test_result_to_dict_conversion(self):
        """Test GenerationResult to_dict() method"""
        self.mock_ollama.chat.return_value = {
            'message': {'content': 'Test script'}
        }
        
        constraints = ValidationConstraints(max_year=2287)
        dj_context = {'name': 'Julie', 'year': 2287}
        
        result = self.pipeline.generate_with_validation(
            template='news',
            lore_chunks=[],
            constraints=constraints,
            dj_context=dj_context
        )
        
        result_dict = result.to_dict()
        
        # Verify dictionary structure
        self.assertIn('script', result_dict)
        self.assertIn('is_valid', result_dict)
        self.assertIn('llm_calls', result_dict)
        self.assertIn('metadata', result_dict)


if __name__ == '__main__':
    unittest.main()
