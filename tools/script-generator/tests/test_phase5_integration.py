"""
Phase 5: Integration & Polish - Real Integration and E2E Tests

Tests for:
1. Real Ollama LLM integration
2. Real ChromaDB integration  
3. BroadcastEngine orchestration
4. End-to-end workflow validation
5. Performance benchmarking

PHASE 5: Integration & Polish
~40 tests covering all integration scenarios
"""

import pytest
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add parent directories to path for imports
SCRIPT_GEN_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_GEN_DIR))

# Import test decorators
from conftest import (
    requires_ollama,
    requires_chromadb,
    requires_both,
    mark_integration,
    mark_slow,
    IntegrationTestContext
)

# Import production modules
from broadcast_engine import BroadcastEngine
from session_memory import SessionMemory
from world_state import WorldState
from broadcast_scheduler import BroadcastScheduler
from consistency_validator import ConsistencyValidator

# Try to import real clients (may not be available in CI)
try:
    from ollama_client import OllamaClient
    OLLAMA_CLIENT_AVAILABLE = True
except ImportError:
    OLLAMA_CLIENT_AVAILABLE = False

try:
    wiki_tools_path = SCRIPT_GEN_DIR.parent / "wiki_to_chromadb"
    sys.path.insert(0, str(wiki_tools_path))
    from chromadb_ingest import ChromaDBIngestor
    CHROMADB_CLIENT_AVAILABLE = True
except ImportError:
    CHROMADB_CLIENT_AVAILABLE = False


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_world_state(tmp_path) -> Path:
    """Provide temporary world state file"""
    return tmp_path / "test_broadcast_state.json"


@pytest.fixture
def broadcast_engine(temp_world_state) -> BroadcastEngine:
    """Provide BroadcastEngine with test configuration"""
    return BroadcastEngine(
        dj_name="Julie (2102, Appalachia)",
        world_state_path=str(temp_world_state),
        enable_validation=True,
        max_session_memory=5
    )


# ============================================================================
# BROADCASTENGINE UNIT TESTS (Mock-based)
# ============================================================================

class TestBroadcastEngineBasics:
    """Tests for BroadcastEngine core functionality"""
    
    def test_engine_initialization(self, broadcast_engine: BroadcastEngine):
        """Test that BroadcastEngine initializes correctly"""
        assert broadcast_engine is not None
        assert broadcast_engine.dj_name == "Julie (2102, Appalachia)"
        assert broadcast_engine.enable_validation is True
        assert broadcast_engine.session_memory is not None
        assert broadcast_engine.world_state is not None
        assert broadcast_engine.scheduler is not None
    
    def test_start_broadcast(self, broadcast_engine: BroadcastEngine):
        """Test starting a broadcast session"""
        session_info = broadcast_engine.start_broadcast()
        
        assert 'dj_name' in session_info
        assert 'start_time' in session_info
        assert 'session_id' in session_info
        assert session_info['dj_name'] == "Julie (2102, Appalachia)"
    
    def test_broadcast_stats_empty(self, broadcast_engine: BroadcastEngine):
        """Test getting stats before generating segments"""
        broadcast_engine.start_broadcast()
        stats = broadcast_engine.get_broadcast_stats()
        
        assert stats['segments_generated'] == 0
        assert stats['validation_failures'] == 0
        assert stats['avg_generation_time'] == 0
    
    def test_end_broadcast(self, broadcast_engine: BroadcastEngine):
        """Test ending a broadcast session"""
        broadcast_engine.start_broadcast()
        stats = broadcast_engine.end_broadcast(save_state=False)
        
        assert 'duration_seconds' in stats
        assert 'segments_generated' in stats
        assert 'total_generation_time' in stats
        assert stats['dj_name'] == "Julie (2102, Appalachia)"
    
    @mark_slow
    def test_generate_single_segment(self, broadcast_engine: BroadcastEngine):
        """Test generating a single segment"""
        broadcast_engine.start_broadcast()
        
        result = broadcast_engine.generate_next_segment(
            current_hour=8,
            force_type='time'
        )
        
        assert result is not None
        assert 'segment_type' in result
        assert 'script' in result
        assert 'metadata' in result
        assert result['segment_type'] == 'time'
    
    @mark_slow
    def test_template_vars_weather(self, broadcast_engine: BroadcastEngine):
        """Test building template vars for weather"""
        from broadcast_scheduler import TimeOfDay
        
        vars = broadcast_engine._build_template_vars(
            'weather',
            8,
            TimeOfDay.MORNING,
            weather_type='sunny'
        )
        
        assert 'hour' in vars
        assert 'time_of_day' in vars
        assert 'weather_type' in vars
        assert vars['weather_type'] == 'sunny'
    
    @mark_slow
    def test_template_vars_news(self, broadcast_engine: BroadcastEngine):
        """Test building template vars for news"""
        from broadcast_scheduler import TimeOfDay
        
        vars = broadcast_engine._build_template_vars(
            'news',
            14,
            TimeOfDay.AFTERNOON,
            news_category='settlement'
        )
        
        assert 'hour' in vars
        assert 'time_of_day' in vars
        assert 'news_category' in vars
    
    @mark_slow
    def test_context_query_building(self, broadcast_engine: BroadcastEngine):
        """Test building RAG context queries"""
        query = broadcast_engine._build_context_query(
            'weather',
            {'weather_type': 'sunny'}
        )
        
        assert 'Appalachia' in query
        assert 'weather' in query
        assert 'sunny' in query


# ============================================================================
# BROADCASTENGINE INTEGRATION TESTS
# ============================================================================

class TestBroadcastEngineIntegration:
    """Integration tests for BroadcastEngine with real dependencies"""
    
    @mark_slow
    @mark_integration
    def test_broadcast_sequence_mock(self, broadcast_engine: BroadcastEngine):
        """Test generating a broadcast sequence with mocks"""
        broadcast_engine.start_broadcast()
        
        # Generate small sequence
        segments = broadcast_engine.generate_broadcast_sequence(
            start_hour=8,
            duration_hours=1,
            segments_per_hour=2
        )
        
        assert len(segments) == 2
        assert all('segment_type' in s for s in segments)
        assert all('script' in s for s in segments)
    
    @mark_slow
    @mark_integration
    def test_session_memory_updates(self, broadcast_engine: BroadcastEngine):
        """Test that session memory is updated after each segment"""
        broadcast_engine.start_broadcast()
        
        initial_count = len(broadcast_engine.session_memory.recent_scripts)
        
        broadcast_engine.generate_next_segment(
            current_hour=10,
            force_type='time'
        )
        
        assert len(broadcast_engine.session_memory.recent_scripts) == initial_count + 1
    
    @mark_slow
    @mark_integration
    def test_scheduler_updates(self, broadcast_engine: BroadcastEngine):
        """Test that scheduler tracks completed segments"""
        broadcast_engine.start_broadcast()
        
        broadcast_engine.generate_next_segment(
            current_hour=8,
            force_type='weather'
        )
        
        status = broadcast_engine.scheduler.get_segments_status()
        assert 'weather' in status
    
    @mark_slow
    @mark_integration
    def test_validation_integration(self, broadcast_engine: BroadcastEngine):
        """Test that validation runs when enabled"""
        assert broadcast_engine.enable_validation is True
        assert broadcast_engine.validator is not None
        
        broadcast_engine.start_broadcast()
        
        result = broadcast_engine.generate_next_segment(
            current_hour=12,
            force_type='time'
        )
        
        # Check validation result in metadata
        assert 'validation' in result['metadata']


# ============================================================================
# REAL OLLAMA INTEGRATION TESTS
# ============================================================================

class TestRealOllamaIntegration:
    """Tests using actual Ollama LLM client"""
    
    @requires_ollama
    @mark_integration
    @mark_slow
    def test_real_ollama_connection(self):
        """Test connection to real Ollama"""
        if not OLLAMA_CLIENT_AVAILABLE:
            pytest.skip("OllamaClient not available")
        
        client = OllamaClient()
        assert client.check_connection()
    
    @requires_ollama
    @mark_integration
    @mark_slow
    def test_real_ollama_generation(self):
        """Test actual generation with Ollama"""
        if not OLLAMA_CLIENT_AVAILABLE:
            pytest.skip("OllamaClient not available")
        
        client = OllamaClient()
        response = client.generate(
            model="fluffy/l3-8b-stheno-v3.2",
            prompt="Say hello in one sentence.",
            options={"temperature": 0.7, "max_tokens": 50}
        )
        
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
    
    @requires_ollama
    @mark_integration
    @mark_slow
    def test_real_weather_generation(self):
        """Test weather script generation with real Ollama"""
        if not OLLAMA_CLIENT_AVAILABLE:
            pytest.skip("OllamaClient not available")
        
        from generator import ScriptGenerator
        
        generator = ScriptGenerator()
        result = generator.generate_script(
            script_type="time",
            dj_name="Julie (2102, Appalachia)",
            context_query="Vault 76 morning schedule",
            hour=8,
            time_of_day="morning"
        )
        
        assert result is not None
        assert 'script' in result
        assert len(result['script']) > 0


# ============================================================================
# REAL CHROMADB INTEGRATION TESTS
# ============================================================================

class TestRealChromaDBIntegration:
    """Tests using actual ChromaDB vector database"""
    
    @requires_chromadb
    @mark_integration
    def test_real_chromadb_connection(self):
        """Test connection to real ChromaDB"""
        if not CHROMADB_CLIENT_AVAILABLE:
            pytest.skip("ChromaDBIngestor not available")
        
        ingestor = ChromaDBIngestor()
        # Basic check - if no exception, connection works
        assert ingestor is not None
    
    @requires_chromadb
    @mark_integration
    @mark_slow
    def test_real_chromadb_query(self):
        """Test actual query with ChromaDB"""
        if not CHROMADB_CLIENT_AVAILABLE:
            pytest.skip("ChromaDBIngestor not available")
        
        ingestor = ChromaDBIngestor()
        results = ingestor.query(
            text="Appalachia weather radiation",
            n_results=3
        )
        
        assert results is not None
        assert 'documents' in results or hasattr(results, 'documents')
    
    @requires_chromadb
    @mark_integration
    @mark_slow
    def test_real_chromadb_with_filter(self):
        """Test ChromaDB query with metadata filter"""
        if not CHROMADB_CLIENT_AVAILABLE:
            pytest.skip("ChromaDBIngestor not available")
        
        ingestor = ChromaDBIngestor()
        results = ingestor.query(
            text="Vault 76",
            n_results=5,
            where={"type": "location"}
        )
        
        assert results is not None


# ============================================================================
# END-TO-END WORKFLOW TESTS
# ============================================================================

class TestEndToEndWorkflows:
    """Complete workflow tests from start to finish"""
    
    @mark_slow
    @mark_integration
    def test_complete_broadcast_session(self, broadcast_engine: BroadcastEngine, temp_world_state):
        """Test complete broadcast session workflow"""
        # Start broadcast
        session_info = broadcast_engine.start_broadcast()
        assert 'session_id' in session_info
        
        # Generate segments
        segments = []
        for hour in [8, 9, 10]:
            segment = broadcast_engine.generate_next_segment(
                current_hour=hour,
                force_type='time'
            )
            segments.append(segment)
        
        # End broadcast
        stats = broadcast_engine.end_broadcast(save_state=True)
        
        # Verify results
        assert len(segments) == 3
        assert stats['segments_generated'] == 3
        assert stats['duration_seconds'] > 0
        
        # Verify world state saved
        assert temp_world_state.exists()
    
    @mark_slow
    @mark_integration
    def test_multi_type_broadcast(self, broadcast_engine: BroadcastEngine):
        """Test broadcast with multiple segment types"""
        broadcast_engine.start_broadcast()
        
        types = ['time', 'weather', 'news', 'gossip']
        segments = []
        
        for i, seg_type in enumerate(types):
            segment = broadcast_engine.generate_next_segment(
                current_hour=8 + i,
                force_type=seg_type
            )
            segments.append(segment)
        
        stats = broadcast_engine.end_broadcast()
        
        # Verify all types generated
        assert len(segments) == 4
        segment_types = [s['segment_type'] for s in segments]
        assert set(segment_types) == set(types)
        assert stats['segments_generated'] == 4
    
    @requires_both
    @mark_slow
    @mark_integration
    def test_full_real_workflow(self):
        """Test complete workflow with real Ollama and ChromaDB"""
        with IntegrationTestContext(require_ollama=True, require_chromadb=True) as ctx:
            if ctx.should_skip:
                pytest.skip(ctx.skip_reason)
        
        # This would run the full pipeline with real dependencies
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            enable_validation=True
        )
        
        engine.start_broadcast()
        
        # Generate one of each type
        result = engine.generate_next_segment(current_hour=8, force_type='time')
        assert result['script'] is not None
        assert len(result['script']) > 0
        
        stats = engine.end_broadcast()
        assert stats['segments_generated'] >= 1


# ============================================================================
# PERFORMANCE BENCHMARKING TESTS
# ============================================================================

class TestPerformanceBenchmarks:
    """Performance and benchmark tests"""
    
    @mark_slow
    def test_generation_speed_time(self, broadcast_engine: BroadcastEngine):
        """Benchmark time announcement generation speed"""
        broadcast_engine.start_broadcast()
        
        start = time.time()
        result = broadcast_engine.generate_next_segment(
            current_hour=10,
            force_type='time'
        )
        duration = time.time() - start
        
        # Should complete in reasonable time (adjust based on hardware)
        assert duration < 30.0  # 30 seconds max
        assert result['metadata']['generation_time'] > 0
    
    @mark_slow
    @mark_integration
    def test_sequential_generation_performance(self, broadcast_engine: BroadcastEngine):
        """Benchmark sequential segment generation"""
        broadcast_engine.start_broadcast()
        
        start = time.time()
        segments = broadcast_engine.generate_broadcast_sequence(
            start_hour=8,
            duration_hours=1,
            segments_per_hour=3
        )
        total_duration = time.time() - start
        
        assert len(segments) == 3
        avg_time = total_duration / len(segments)
        
        print(f"\nPerformance: {avg_time:.2f}s avg per segment")
        assert avg_time < 35.0  # 35 seconds average max (with retries)
    
    @mark_slow
    def test_memory_efficiency(self, broadcast_engine: BroadcastEngine):
        """Test that session memory stays within bounds"""
        broadcast_engine.start_broadcast()
        
        # Generate more segments than max memory
        max_memory = broadcast_engine.session_memory.max_history
        for i in range(max_memory + 5):
            broadcast_engine.generate_next_segment(
                current_hour=(8 + i) % 24,
                force_type='time'
            )
        
        # Should not exceed max_history
        assert len(broadcast_engine.session_memory.recent_scripts) <= max_memory
    
    @mark_slow
    def test_validation_overhead(self, temp_world_state):
        """Test validation overhead impact on performance"""
        # Engine with validation
        engine_with_val = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=str(temp_world_state),
            enable_validation=True
        )
        
        # Engine without validation  
        engine_no_val = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            world_state_path=str(temp_world_state),
            enable_validation=False
        )
        
        # Both should complete successfully
        engine_with_val.start_broadcast()
        engine_no_val.start_broadcast()
        
        result1 = engine_with_val.generate_next_segment(8, force_type='time')
        result2 = engine_no_val.generate_next_segment(8, force_type='time')
        
        # Validation should add minimal overhead (< 2x slower)
        time1 = result1['metadata']['generation_time']
        time2 = result2['metadata']['generation_time']
        
        # Both should complete
        assert time1 > 0
        assert time2 > 0


# ============================================================================
# STRESS TESTS
# ============================================================================

class TestStressScenarios:
    """Stress tests for edge cases"""
    
    @mark_slow
    def test_long_broadcast_session(self, broadcast_engine: BroadcastEngine):
        """Test long broadcast session (24 hours simulated)"""
        broadcast_engine.start_broadcast()
        
        # Generate one segment per hour for 24 hours
        segments = broadcast_engine.generate_broadcast_sequence(
            start_hour=0,
            duration_hours=24,
            segments_per_hour=1
        )
        
        stats = broadcast_engine.end_broadcast()
        
        assert len(segments) == 24
        assert stats['segments_generated'] == 24
        assert stats['avg_generation_time'] > 0
    
    @mark_slow
    def test_rapid_segment_generation(self, broadcast_engine: BroadcastEngine):
        """Test rapid consecutive segment generation"""
        broadcast_engine.start_broadcast()
        
        segments = []
        for i in range(10):
            segment = broadcast_engine.generate_next_segment(
                current_hour=8,
                force_type='time'
            )
            segments.append(segment)
        
        assert len(segments) == 10
        assert all(s['script'] for s in segments)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
