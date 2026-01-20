"""
Unit tests for llm_pipeline.py

Tests the LLMPipeline module with mocked dependencies.
Covers pipeline initialization, single-call generation with validation,
embedded constraint validation, retry logic, and error handling.

Phase 4: Testing Infrastructure
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools" / "script-generator"))

# Import mocks first
from tests.mocks.mock_llm import MockLLMClient, MockLLMClientWithFailure

# Import pipeline modules
from llm_pipeline import LLMPipeline, GenerationResult


@pytest.mark.mock
class TestGenerationResultDataClass:
    """Test suite for GenerationResult dataclass"""
    
    def test_generation_result_creation(self):
        """Test creating a GenerationResult"""
        result = GenerationResult(
            script="Generated script content",
            is_valid=True,
            validation_source="embedded_constraints",
            generation_time_ms=250,
            cache_hit=True,
            llm_calls=1,
            metadata={
                'template': 'weather',
                'dj': 'Julie',
                'year': 2102
            }
        )
        
        assert result.script == "Generated script content"
        assert result.is_valid is True
        assert result.validation_source == "embedded_constraints"
        assert result.generation_time_ms == 250
        assert result.cache_hit is True
        assert result.llm_calls == 1
        assert result.metadata['template'] == 'weather'
    
    def test_generation_result_to_dict(self):
        """Test converting GenerationResult to dictionary"""
        result = GenerationResult(
            script="Test script",
            is_valid=True,
            validation_source="post_validation",
            generation_time_ms=300,
            cache_hit=False,
            llm_calls=2,
            metadata={'test': 'value'}
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['script'] == "Test script"
        assert result_dict['is_valid'] is True
        assert result_dict['validation_source'] == "post_validation"
        assert result_dict['generation_time_ms'] == 300
        assert result_dict['cache_hit'] is False
        assert result_dict['llm_calls'] == 2
        assert result_dict['metadata']['test'] == 'value'


@pytest.mark.mock
class TestLLMPipelineInitialization:
    """Test suite for LLMPipeline initialization"""
    
    def test_initialization_with_ollama_client(self, mock_llm):
        """Test LLMPipeline initialization with Ollama client"""
        pipeline = LLMPipeline(ollama_client=mock_llm)
        
        assert pipeline.ollama == mock_llm
        assert pipeline.rag_cache is None
        assert pipeline.total_generations == 0
        assert pipeline.total_llm_calls == 0
        assert pipeline.total_generation_time_ms == 0
        assert pipeline.cache_hits == 0
        assert pipeline.validation_guided_generations == 0
    
    def test_initialization_with_rag_cache(self, mock_llm):
        """Test LLMPipeline initialization with RAG cache"""
        mock_rag_cache = Mock()
        mock_rag_cache.get_statistics.return_value = {
            'hit_rate': 0.5,
            'cache_hits': 5,
            'cache_misses': 5
        }
        
        pipeline = LLMPipeline(
            ollama_client=mock_llm,
            rag_cache=mock_rag_cache
        )
        
        assert pipeline.ollama == mock_llm
        assert pipeline.rag_cache == mock_rag_cache
    
    def test_initialization_metrics_start_at_zero(self, mock_llm):
        """Test that metrics start at zero"""
        pipeline = LLMPipeline(ollama_client=mock_llm)
        
        metrics = pipeline.get_metrics()
        
        assert metrics['total_generations'] == 0
        assert metrics['total_llm_calls'] == 0
        assert metrics['avg_llm_calls_per_segment'] == 0
        assert metrics['validation_guided_generations'] == 0
        assert metrics['avg_generation_time_ms'] == 0
        assert metrics['cache_hits'] == 0


@pytest.mark.mock
class TestLLMPipelineConstraintEmbedding:
    """Test suite for constraint embedding in prompts"""
    
    def test_build_constraint_embedded_prompt(self, mock_llm):
        """Test building prompt with embedded constraints"""
        from segment_plan import ValidationConstraints
        
        pipeline = LLMPipeline(ollama_client=mock_llm)
        
        constraints = ValidationConstraints(
            max_length=200,
            forbidden_topics=['synths', 'Institute'],
            required_tone='friendly',
            max_year=2102
        )
        
        prompt = pipeline._build_constraint_embedded_prompt(
            dj_name="Julie",
            year=2102,
            region="Appalachia",
            tone="friendly and optimistic",
            template="weather",
            constraints=constraints,
            lore_chunks=["Weather in Appalachia is harsh", "Rad storms are common"]
        )
        
        # Verify constraint elements in prompt
        assert "Julie" in prompt
        assert "2102" in prompt
        assert "Appalachia" in prompt
        assert "friendly" in prompt
        assert "weather" in prompt
        assert "Weather in Appalachia is harsh" in prompt
        assert "Rad storms are common" in prompt
    
    def test_build_constraint_embedded_prompt_no_constraints(self, mock_llm):
        """Test building prompt without constraints"""
        pipeline = LLMPipeline(ollama_client=mock_llm)
        
        prompt = pipeline._build_constraint_embedded_prompt(
            dj_name="Julie",
            year=2102,
            region="Appalachia",
            tone="friendly",
            template="news",
            constraints=None,
            lore_chunks=[]
        )
        
        # Should still build valid prompt
        assert "Julie" in prompt
        assert "news" in prompt
    
    def test_build_user_prompt(self, mock_llm):
        """Test building user prompt for different templates"""
        pipeline = LLMPipeline(ollama_client=mock_llm)
        
        templates = ['news', 'weather', 'gossip', 'story', 'time_check', 'music_intro']
        
        for template in templates:
            prompt = pipeline._build_user_prompt(template, {'name': 'Julie'})
            assert isinstance(prompt, str)
            assert len(prompt) > 0


@pytest.mark.mock
class TestLLMPipelineGeneration:
    """Test suite for script generation"""
    
    def setup_method(self):
        """Setup for each test"""
        self.mock_llm = MockLLMClient()
        self.pipeline = LLMPipeline(ollama_client=self.mock_llm)
    
    def test_generate_with_validation_basic(self, test_logger):
        """Test basic generation with validation"""
        from segment_plan import ValidationConstraints
        
        test_logger.info("Testing basic generation with validation")
        
        constraints = ValidationConstraints(
            max_length=200,
            required_tone='friendly'
        )
        
        dj_context = {
            'name': 'Julie',
            'year': 2102,
            'region': 'Appalachia',
            'personality': {'tone': 'friendly'}
        }
        
        # Mock chat response
        with patch.object(self.mock_llm, 'chat') as mock_chat:
            mock_chat.return_value = {
                'message': {
                    'content': 'Generated weather script content'
                }
            }
            
            result = self.pipeline.generate_with_validation(
                template='weather',
                lore_chunks=['Appalachia weather'],
                constraints=constraints,
                dj_context=dj_context
            )
        
        assert result is not None
        assert result.script == 'Generated weather script content'
        assert result.is_valid is True
        assert result.validation_source == 'embedded_constraints'
        assert result.llm_calls == 1
        assert result.metadata['template'] == 'weather'
    
    def test_generate_with_validation_updates_metrics(self, test_logger):
        """Test that generation updates pipeline metrics"""
        from segment_plan import ValidationConstraints
        
        test_logger.info("Testing metrics tracking")
        
        constraints = ValidationConstraints(max_length=200)
        dj_context = {
            'name': 'Julie',
            'year': 2102,
            'region': 'Appalachia',
            'personality': {}
        }
        
        with patch.object(self.mock_llm, 'chat') as mock_chat:
            mock_chat.return_value = {
                'message': {'content': 'Script content'}
            }
            
            # Generate once
            self.pipeline.generate_with_validation(
                template='news',
                lore_chunks=[],
                constraints=constraints,
                dj_context=dj_context
            )
        
        metrics = self.pipeline.get_metrics()
        
        assert metrics['total_generations'] == 1
        assert metrics['total_llm_calls'] == 1
        assert metrics['validation_guided_generations'] == 1
        assert metrics['avg_generation_time_ms'] >= 0  # Mock execution is very fast
    
    def test_generate_with_validation_error_handling(self, test_logger):
        """Test error handling during generation"""
        from segment_plan import ValidationConstraints
        
        test_logger.info("Testing error handling")
        
        constraints = ValidationConstraints(max_length=200)
        dj_context = {
            'name': 'Julie',
            'year': 2102,
            'region': 'Appalachia',
            'personality': {}
        }
        
        with patch.object(self.mock_llm, 'chat') as mock_chat:
            mock_chat.side_effect = Exception("LLM error")
            
            result = self.pipeline.generate_with_validation(
                template='weather',
                lore_chunks=[],
                constraints=constraints,
                dj_context=dj_context
            )
        
        # Should return error result
        assert result.is_valid is False
        assert result.validation_source == 'generation_error'
        assert 'error' in result.metadata
    
    def test_generate_with_validation_with_topic(self, test_logger):
        """Test generation with topic for cache optimization"""
        from segment_plan import ValidationConstraints
        
        test_logger.info("Testing generation with topic")
        
        mock_rag_cache = Mock()
        mock_rag_cache.get_statistics.return_value = {
            'hit_rate': 0.6,
            'cache_hits': 6,
            'cache_misses': 4
        }
        
        pipeline = LLMPipeline(
            ollama_client=self.mock_llm,
            rag_cache=mock_rag_cache
        )
        
        constraints = ValidationConstraints(max_length=200)
        dj_context = {
            'name': 'Julie',
            'year': 2102,
            'region': 'Appalachia',
            'personality': {}
        }
        
        with patch.object(self.mock_llm, 'chat') as mock_chat:
            mock_chat.return_value = {
                'message': {'content': 'Script with cache'}
            }
            
            result = pipeline.generate_with_validation(
                template='weather',
                lore_chunks=['weather lore'],
                constraints=constraints,
                dj_context=dj_context,
                topic='regional_climate'
            )
        
        assert result.metadata['topic'] == 'regional_climate'
        # Cache hit is approximated from hit rate
        assert isinstance(result.cache_hit, bool)


@pytest.mark.mock
class TestLLMPipelineSegmentPlanIntegration:
    """Test suite for SegmentPlan integration"""
    
    def test_generate_from_plan(self, mock_llm, test_logger):
        """Test generating from SegmentPlan"""
        from segment_plan import SegmentPlan, SegmentType, ValidationConstraints
        
        test_logger.info("Testing generation from SegmentPlan")
        
        constraints = ValidationConstraints(
            max_length=200,
            required_tone='friendly'
        )
        
        # Create mock segment plan
        plan = Mock(spec=SegmentPlan)
        plan.segment_type = Mock()
        plan.segment_type.value = 'weather'
        plan.constraints = constraints
        plan.metadata = {'lore_chunks': ['Weather is harsh']}
        
        # Mock get_rag_topic if it exists
        plan.get_rag_topic = Mock(return_value='regional_climate')
        
        pipeline = LLMPipeline(ollama_client=mock_llm)
        
        dj_context = {
            'name': 'Julie',
            'year': 2102,
            'region': 'Appalachia',
            'personality': {}
        }
        
        with patch.object(mock_llm, 'chat') as mock_chat:
            mock_chat.return_value = {
                'message': {'content': 'Generated from plan'}
            }
            
            result = pipeline.generate_from_plan(
                plan=plan,
                dj_context=dj_context
            )
        
        assert result.script == 'Generated from plan'
        assert result.metadata['template'] == 'weather'
    
    def test_generate_from_plan_with_custom_lore(self, mock_llm):
        """Test generating from plan with custom lore chunks"""
        from segment_plan import SegmentPlan, SegmentType, ValidationConstraints
        
        constraints = ValidationConstraints(max_length=200)
        
        plan = Mock(spec=SegmentPlan)
        plan.segment_type = Mock()
        plan.segment_type.value = 'news'
        plan.constraints = constraints
        plan.metadata = {}
        plan.get_rag_topic = Mock(return_value=None)
        
        pipeline = LLMPipeline(ollama_client=mock_llm)
        
        dj_context = {
            'name': 'Julie',
            'year': 2102,
            'region': 'Appalachia',
            'personality': {}
        }
        
        custom_lore = ['Custom lore chunk 1', 'Custom lore chunk 2']
        
        with patch.object(mock_llm, 'chat') as mock_chat:
            mock_chat.return_value = {
                'message': {'content': 'Generated with custom lore'}
            }
            
            result = pipeline.generate_from_plan(
                plan=plan,
                dj_context=dj_context,
                lore_chunks=custom_lore
            )
        
        assert result.script == 'Generated with custom lore'


@pytest.mark.mock
class TestLLMPipelineMetrics:
    """Test suite for pipeline metrics"""
    
    def test_metrics_tracking(self, mock_llm, test_logger):
        """Test comprehensive metrics tracking"""
        from segment_plan import ValidationConstraints
        
        test_logger.info("Testing comprehensive metrics tracking")
        
        pipeline = LLMPipeline(ollama_client=mock_llm)
        
        constraints = ValidationConstraints(max_length=200)
        dj_context = {
            'name': 'Julie',
            'year': 2102,
            'region': 'Appalachia',
            'personality': {}
        }
        
        with patch.object(mock_llm, 'chat') as mock_chat:
            mock_chat.return_value = {
                'message': {'content': 'Script'}
            }
            
            # Generate multiple scripts
            for _ in range(3):
                pipeline.generate_with_validation(
                    template='weather',
                    lore_chunks=[],
                    constraints=constraints,
                    dj_context=dj_context
                )
        
        metrics = pipeline.get_metrics()
        
        assert metrics['total_generations'] == 3
        assert metrics['total_llm_calls'] == 3
        assert metrics['avg_llm_calls_per_segment'] == 1.0
        assert metrics['validation_guided_generations'] == 3
        assert metrics['validation_guided_percentage'] == 100.0
        assert metrics['avg_generation_time_ms'] >= 0  # Mock execution is very fast
    
    def test_metrics_reset(self, mock_llm):
        """Test resetting metrics"""
        from segment_plan import ValidationConstraints
        
        pipeline = LLMPipeline(ollama_client=mock_llm)
        
        constraints = ValidationConstraints(max_length=200)
        dj_context = {
            'name': 'Julie',
            'year': 2102,
            'region': 'Appalachia',
            'personality': {}
        }
        
        with patch.object(mock_llm, 'chat') as mock_chat:
            mock_chat.return_value = {
                'message': {'content': 'Script'}
            }
            
            pipeline.generate_with_validation(
                template='weather',
                lore_chunks=[],
                constraints=constraints,
                dj_context=dj_context
            )
        
        # Metrics should be non-zero
        assert pipeline.total_generations > 0
        
        # Reset metrics
        pipeline.reset_metrics()
        
        # Metrics should be zero
        assert pipeline.total_generations == 0
        assert pipeline.total_llm_calls == 0
        assert pipeline.total_generation_time_ms == 0
        assert pipeline.cache_hits == 0
        assert pipeline.validation_guided_generations == 0
    
    def test_get_metrics_expected_improvements(self, mock_llm):
        """Test that metrics include expected improvements"""
        pipeline = LLMPipeline(ollama_client=mock_llm)
        
        metrics = pipeline.get_metrics()
        
        assert 'expected_improvement' in metrics
        assert 'llm_calls_reduction' in metrics['expected_improvement']
        assert 'generation_speed_improvement' in metrics['expected_improvement']
        assert 'validation_failure_reduction' in metrics['expected_improvement']
        
        # Verify improvement claims
        assert '50%' in metrics['expected_improvement']['llm_calls_reduction']
        assert '33%' in metrics['expected_improvement']['generation_speed_improvement']
        assert '80%' in metrics['expected_improvement']['validation_failure_reduction']
    
    def test_print_metrics_report(self, mock_llm, capsys):
        """Test printing metrics report"""
        from segment_plan import ValidationConstraints
        
        pipeline = LLMPipeline(ollama_client=mock_llm)
        
        constraints = ValidationConstraints(max_length=200)
        dj_context = {
            'name': 'Julie',
            'year': 2102,
            'region': 'Appalachia',
            'personality': {}
        }
        
        with patch.object(mock_llm, 'chat') as mock_chat:
            mock_chat.return_value = {
                'message': {'content': 'Script'}
            }
            
            pipeline.generate_with_validation(
                template='weather',
                lore_chunks=[],
                constraints=constraints,
                dj_context=dj_context
            )
        
        # Print report
        pipeline.print_metrics_report()
        
        # Capture output
        captured = capsys.readouterr()
        
        assert "LLM Pipeline Performance Metrics" in captured.out
        assert "Total Generations" in captured.out
        assert "Total LLM Calls" in captured.out
        assert "Expected Improvements" in captured.out


@pytest.mark.mock
class TestLLMPipelineRetryLogic:
    """Test suite for retry logic and error handling"""
    
    def test_single_call_success(self, mock_llm, test_logger):
        """Test successful generation on first call"""
        from segment_plan import ValidationConstraints
        
        test_logger.info("Testing single-call success")
        
        pipeline = LLMPipeline(ollama_client=mock_llm)
        
        constraints = ValidationConstraints(max_length=200)
        dj_context = {
            'name': 'Julie',
            'year': 2102,
            'region': 'Appalachia',
            'personality': {}
        }
        
        with patch.object(mock_llm, 'chat') as mock_chat:
            mock_chat.return_value = {
                'message': {'content': 'Success on first call'}
            }
            
            result = pipeline.generate_with_validation(
                template='weather',
                lore_chunks=[],
                constraints=constraints,
                dj_context=dj_context
            )
        
        assert result.is_valid is True
        assert result.llm_calls == 1
        assert mock_chat.call_count == 1
    
    def test_generation_failure_returns_error_result(self, test_logger):
        """Test that generation failure returns proper error result"""
        from segment_plan import ValidationConstraints
        
        test_logger.info("Testing generation failure")
        
        mock_llm_failing = MockLLMClientWithFailure(fail_after_n_calls=0)
        pipeline = LLMPipeline(ollama_client=mock_llm_failing)
        
        constraints = ValidationConstraints(max_length=200)
        dj_context = {
            'name': 'Julie',
            'year': 2102,
            'region': 'Appalachia',
            'personality': {}
        }
        
        with patch.object(mock_llm_failing, 'chat') as mock_chat:
            mock_chat.side_effect = Exception("LLM failed")
            
            result = pipeline.generate_with_validation(
                template='weather',
                lore_chunks=[],
                constraints=constraints,
                dj_context=dj_context
            )
        
        assert result.is_valid is False
        assert result.validation_source == 'generation_error'
        assert result.script == ''
        assert 'error' in result.metadata


@pytest.mark.mock
class TestLLMPipelineCacheIntegration:
    """Test suite for RAG cache integration"""
    
    def test_cache_hit_tracking(self, mock_llm, test_logger):
        """Test cache hit tracking"""
        from segment_plan import ValidationConstraints
        
        test_logger.info("Testing cache hit tracking")
        
        mock_rag_cache = Mock()
        mock_rag_cache.get_statistics.return_value = {
            'hit_rate': 0.8,
            'cache_hits': 8,
            'cache_misses': 2
        }
        
        pipeline = LLMPipeline(
            ollama_client=mock_llm,
            rag_cache=mock_rag_cache
        )
        
        constraints = ValidationConstraints(max_length=200)
        dj_context = {
            'name': 'Julie',
            'year': 2102,
            'region': 'Appalachia',
            'personality': {}
        }
        
        with patch.object(mock_llm, 'chat') as mock_chat:
            mock_chat.return_value = {
                'message': {'content': 'Script'}
            }
            
            result = pipeline.generate_with_validation(
                template='weather',
                lore_chunks=[],
                constraints=constraints,
                dj_context=dj_context,
                topic='regional_climate'
            )
        
        # Should track cache hit based on hit rate > 0.5
        assert result.cache_hit is True
        assert pipeline.cache_hits > 0
    
    def test_cache_miss_tracking(self, mock_llm):
        """Test cache miss tracking"""
        from segment_plan import ValidationConstraints
        
        mock_rag_cache = Mock()
        mock_rag_cache.get_statistics.return_value = {
            'hit_rate': 0.2,
            'cache_hits': 2,
            'cache_misses': 8
        }
        
        pipeline = LLMPipeline(
            ollama_client=mock_llm,
            rag_cache=mock_rag_cache
        )
        
        constraints = ValidationConstraints(max_length=200)
        dj_context = {
            'name': 'Julie',
            'year': 2102,
            'region': 'Appalachia',
            'personality': {}
        }
        
        with patch.object(mock_llm, 'chat') as mock_chat:
            mock_chat.return_value = {
                'message': {'content': 'Script'}
            }
            
            result = pipeline.generate_with_validation(
                template='weather',
                lore_chunks=[],
                constraints=constraints,
                dj_context=dj_context,
                topic='regional_climate'
            )
        
        # Should track cache miss based on hit rate < 0.5
        assert result.cache_hit is False
    
    def test_no_cache_tracking_without_cache(self, mock_llm):
        """Test that cache tracking works without RAG cache"""
        from segment_plan import ValidationConstraints
        
        pipeline = LLMPipeline(ollama_client=mock_llm)
        
        constraints = ValidationConstraints(max_length=200)
        dj_context = {
            'name': 'Julie',
            'year': 2102,
            'region': 'Appalachia',
            'personality': {}
        }
        
        with patch.object(mock_llm, 'chat') as mock_chat:
            mock_chat.return_value = {
                'message': {'content': 'Script'}
            }
            
            result = pipeline.generate_with_validation(
                template='weather',
                lore_chunks=[],
                constraints=constraints,
                dj_context=dj_context
            )
        
        # Cache hit should be False without cache
        assert result.cache_hit is False


@pytest.mark.mock
class TestLLMPipelineValidationGuided:
    """Test suite for validation-guided generation"""
    
    def test_validation_guided_percentage(self, mock_llm):
        """Test validation-guided percentage tracking"""
        from segment_plan import ValidationConstraints
        
        pipeline = LLMPipeline(ollama_client=mock_llm)
        
        constraints = ValidationConstraints(max_length=200)
        dj_context = {
            'name': 'Julie',
            'year': 2102,
            'region': 'Appalachia',
            'personality': {}
        }
        
        with patch.object(mock_llm, 'chat') as mock_chat:
            mock_chat.return_value = {
                'message': {'content': 'Script'}
            }
            
            # Generate 5 scripts with validation
            for _ in range(5):
                pipeline.generate_with_validation(
                    template='weather',
                    lore_chunks=[],
                    constraints=constraints,
                    dj_context=dj_context
                )
        
        metrics = pipeline.get_metrics()
        
        # All generations should be validation-guided
        assert metrics['validation_guided_generations'] == 5
        assert metrics['validation_guided_percentage'] == 100.0
    
    def test_embedded_constraints_in_prompt(self, mock_llm, test_logger):
        """Test that constraints are embedded in the prompt"""
        from segment_plan import ValidationConstraints
        
        test_logger.info("Testing embedded constraints in prompt")
        
        pipeline = LLMPipeline(ollama_client=mock_llm)
        
        constraints = ValidationConstraints(
            max_length=200,
            forbidden_topics=['synths', 'Institute'],
            required_tone='friendly'
        )
        
        dj_context = {
            'name': 'Julie',
            'year': 2102,
            'region': 'Appalachia',
            'personality': {'tone': 'friendly'}
        }
        
        with patch.object(mock_llm, 'chat') as mock_chat:
            mock_chat.return_value = {
                'message': {'content': 'Script'}
            }
            
            pipeline.generate_with_validation(
                template='weather',
                lore_chunks=['Weather lore'],
                constraints=constraints,
                dj_context=dj_context
            )
            
            # Verify chat was called
            assert mock_chat.call_count == 1
            
            # Get the call arguments
            call_args = mock_chat.call_args
            messages = call_args[1]['messages'] if 'messages' in call_args[1] else call_args[0][0]
            
            # System prompt should contain constraint info
            system_prompt = messages[0]['content']
            assert 'STRICT CONSTRAINTS' in system_prompt or 'constraint' in system_prompt.lower()
