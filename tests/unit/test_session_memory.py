"""
Unit tests for session_memory.py

Tests the SessionMemory module with mocked dependencies.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools" / "script-generator"))

from session_memory import SessionMemory, ScriptEntry


@pytest.mark.mock
class TestScriptEntry:
    """Test suite for ScriptEntry dataclass"""
    
    def test_script_entry_creation(self):
        """Test creating a ScriptEntry"""
        entry = ScriptEntry(
            script_type="weather",
            content="Sunny day in the wasteland",
            timestamp="2102-08-15T08:00:00",
            metadata={"weather_type": "sunny"},
            catchphrases_used=["Stay safe out there!"]
        )
        
        assert entry.script_type == "weather"
        assert entry.content == "Sunny day in the wasteland"
        assert entry.timestamp == "2102-08-15T08:00:00"
        assert entry.metadata["weather_type"] == "sunny"
        assert len(entry.catchphrases_used) == 1


@pytest.mark.mock
class TestSessionMemoryInitialization:
    """Test suite for SessionMemory initialization"""
    
    def test_initialization_defaults(self):
        """Test SessionMemory initialization with defaults"""
        memory = SessionMemory()
        
        assert memory.max_history == 10
        assert memory.dj_name is None
        assert len(memory.recent_scripts) == 0
        assert len(memory.catchphrase_history) == 0
        assert len(memory.mentioned_topics) == 0
        assert memory.segment_count == 0
        assert len(memory.recent_story_beats) == 0
    
    def test_initialization_with_params(self):
        """Test SessionMemory initialization with custom parameters"""
        memory = SessionMemory(max_history=20, dj_name="Julie")
        
        assert memory.max_history == 20
        assert memory.dj_name == "Julie"
        assert memory.session_start is not None
    
    def test_session_start_timestamp(self):
        """Test that session_start is set on initialization"""
        memory = SessionMemory()
        
        assert isinstance(memory.session_start, datetime)
        # Should be recent (within last minute)
        time_diff = datetime.now() - memory.session_start
        assert time_diff.total_seconds() < 60


@pytest.mark.mock
class TestSessionMemoryAddScript:
    """Test suite for adding scripts to memory"""
    
    def test_add_simple_script(self):
        """Test adding a simple script"""
        memory = SessionMemory()
        
        memory.add_script(
            script_type="weather",
            content="Clear skies today"
        )
        
        assert len(memory.recent_scripts) == 1
        assert memory.recent_scripts[0].script_type == "weather"
        assert memory.recent_scripts[0].content == "Clear skies today"
        assert memory.segment_count == 1
    
    def test_add_script_with_metadata(self):
        """Test adding script with metadata"""
        memory = SessionMemory()
        
        metadata = {
            "weather_type": "sunny",
            "temperature": 75
        }
        
        memory.add_script(
            script_type="weather",
            content="Sunny weather",
            metadata=metadata
        )
        
        assert memory.recent_scripts[0].metadata == metadata
    
    def test_add_script_with_catchphrases(self):
        """Test adding script with catchphrases"""
        memory = SessionMemory()
        
        catchphrases = ["Stay safe!", "You are not alone"]
        
        memory.add_script(
            script_type="news",
            content="News update",
            catchphrases_used=catchphrases
        )
        
        assert memory.recent_scripts[0].catchphrases_used == catchphrases
        assert len(memory.catchphrase_history) == 2
    
    def test_add_multiple_scripts(self):
        """Test adding multiple scripts"""
        memory = SessionMemory()
        
        for i in range(5):
            memory.add_script(
                script_type=f"type_{i}",
                content=f"Content {i}"
            )
        
        assert len(memory.recent_scripts) == 5
        assert memory.segment_count == 5
    
    def test_max_history_enforcement(self):
        """Test that max_history limit is enforced"""
        memory = SessionMemory(max_history=3)
        
        # Add 5 scripts (more than max)
        for i in range(5):
            memory.add_script(
                script_type="weather",
                content=f"Script {i}"
            )
        
        # Should only keep last 3
        assert len(memory.recent_scripts) == 3
        assert memory.recent_scripts[0].content == "Script 2"
        assert memory.recent_scripts[-1].content == "Script 4"
    
    def test_catchphrase_history_limit(self):
        """Test catchphrase history is limited"""
        memory = SessionMemory(max_history=2)
        
        # Add many scripts with catchphrases
        for i in range(10):
            memory.add_script(
                script_type="weather",
                content=f"Script {i}",
                catchphrases_used=[f"Phrase {i}"]
            )
        
        # Catchphrase history should be limited to max_history * 3
        assert len(memory.catchphrase_history) <= 2 * 3
    
    def test_timestamp_auto_generated(self):
        """Test that timestamp is auto-generated"""
        memory = SessionMemory()
        
        memory.add_script(
            script_type="weather",
            content="Test"
        )
        
        timestamp = memory.recent_scripts[0].timestamp
        assert timestamp is not None
        # Should be ISO format
        datetime.fromisoformat(timestamp)  # Will raise if invalid


@pytest.mark.mock
class TestSessionMemoryTopicExtraction:
    """Test suite for topic extraction and tracking"""
    
    def test_extract_raiders_topic(self):
        """Test extracting raiders topic"""
        memory = SessionMemory()
        
        memory.add_script(
            script_type="news",
            content="The raiders attacked the settlement today"
        )
        
        assert "raiders" in memory.mentioned_topics
        assert memory.mentioned_topics["raiders"] == 1
    
    def test_extract_vault_topic(self):
        """Test extracting vault topic"""
        memory = SessionMemory()
        
        memory.add_script(
            script_type="news",
            content="A new Vault-Tec vault was discovered underground"
        )
        
        assert "vault" in memory.mentioned_topics
    
    def test_topic_count_increments(self):
        """Test that topic counts increment"""
        memory = SessionMemory()
        
        # Mention raiders multiple times
        memory.add_script(
            script_type="news",
            content="Raiders are attacking"
        )
        memory.add_script(
            script_type="gossip",
            content="More raider activity reported"
        )
        
        assert memory.mentioned_topics["raiders"] == 2
    
    def test_multiple_topics_in_one_script(self):
        """Test extracting multiple topics from one script"""
        memory = SessionMemory()
        
        memory.add_script(
            script_type="news",
            content="Raiders attacked near the vault. Brotherhood responded."
        )
        
        # Should extract both raiders and factions
        assert "raiders" in memory.mentioned_topics
        assert "factions" in memory.mentioned_topics
    
    def test_get_mentioned_topics(self):
        """Test getting list of mentioned topics"""
        memory = SessionMemory()
        
        memory.add_script(
            script_type="news",
            content="Raiders and vault dwellers trading"
        )
        
        topics = memory.get_mentioned_topics()
        assert isinstance(topics, list)
        assert "raiders" in topics
        assert "vault" in topics or "trading" in topics


@pytest.mark.mock
class TestSessionMemoryContextGeneration:
    """Test suite for context generation"""
    
    def test_get_context_empty_memory(self):
        """Test getting context with no scripts"""
        memory = SessionMemory()
        
        context = memory.get_context_for_prompt()
        
        assert context == ""
    
    def test_get_context_with_scripts(self):
        """Test getting context with scripts"""
        memory = SessionMemory()
        
        memory.add_script(
            script_type="weather",
            content="Sunny day in Appalachia"
        )
        memory.add_script(
            script_type="news",
            content="Settlement news update"
        )
        
        context = memory.get_context_for_prompt(include_recent=2)
        
        assert "RECENT BROADCAST CONTEXT" in context
        assert "weather" in context.lower()
        assert "news" in context.lower()
        assert "CONTINUITY REQUIREMENTS" in context
    
    def test_get_context_limits_recent(self):
        """Test that context limits recent scripts"""
        memory = SessionMemory()
        
        # Add 5 scripts
        for i in range(5):
            memory.add_script(
                script_type="weather",
                content=f"Script {i} with unique content number {i}"
            )
        
        # Request only 2 recent
        context = memory.get_context_for_prompt(include_recent=2)
        
        # Should only include last 2
        assert "Script 3" in context or "Script 4" in context
        assert "Script 0" not in context
        assert "Script 1" not in context
    
    def test_get_context_includes_segment_count(self):
        """Test that context includes segment count"""
        memory = SessionMemory()
        
        for i in range(3):
            memory.add_script(
                script_type="weather",
                content=f"Script {i}"
            )
        
        context = memory.get_context_for_prompt()
        
        assert "3" in context  # Should mention 3 segments
    
    def test_get_context_truncates_long_content(self):
        """Test that long script content is truncated"""
        memory = SessionMemory()
        
        long_content = "A" * 300  # 300 characters
        memory.add_script(
            script_type="weather",
            content=long_content
        )
        
        context = memory.get_context_for_prompt()
        
        # Should include ellipsis for truncation
        assert "..." in context


@pytest.mark.mock
class TestSessionMemoryCatchphrases:
    """Test suite for catchphrase tracking"""
    
    def test_get_recent_catchphrases_empty(self):
        """Test getting catchphrases with empty history"""
        memory = SessionMemory()
        
        recent = memory.get_recent_catchphrases()
        
        assert recent == []
    
    def test_get_recent_catchphrases(self):
        """Test getting recent catchphrases"""
        memory = SessionMemory()
        
        memory.add_script(
            script_type="weather",
            content="Test",
            catchphrases_used=["Stay safe!", "Keep listening"]
        )
        
        recent = memory.get_recent_catchphrases(count=5)
        
        assert len(recent) == 2
        assert "Stay safe!" in recent
        assert "Keep listening" in recent
    
    def test_get_recent_catchphrases_limits_count(self):
        """Test that catchphrase retrieval limits count"""
        memory = SessionMemory()
        
        # Add 10 catchphrases
        for i in range(10):
            memory.add_script(
                script_type="weather",
                content="Test",
                catchphrases_used=[f"Phrase {i}"]
            )
        
        recent = memory.get_recent_catchphrases(count=3)
        
        assert len(recent) == 3
        # Should be the most recent ones
        assert "Phrase 9" in recent
        assert "Phrase 8" in recent
        assert "Phrase 7" in recent


@pytest.mark.mock
class TestSessionMemoryWeatherContinuity:
    """Test suite for weather continuity methods"""
    
    def test_get_weather_continuity_no_history(self):
        """Test weather continuity with no history"""
        memory = SessionMemory()
        
        current_weather = {"weather_type": "sunny"}
        context = memory.get_weather_continuity_context("Appalachia", current_weather)
        
        assert context["weather_changed"] is False
        assert context["last_weather_type"] is None
        assert context["continuity_phrase"] is None
        assert context["has_notable_history"] is False
    
    def test_get_weather_continuity_same_weather(self):
        """Test weather continuity when weather hasn't changed"""
        memory = SessionMemory()
        
        # Add weather script
        memory.add_script(
            script_type="weather",
            content="Sunny day",
            metadata={"weather_type": "sunny"}
        )
        
        current_weather = {"weather_type": "sunny"}
        context = memory.get_weather_continuity_context("Appalachia", current_weather)
        
        assert context["weather_changed"] is False
        assert context["last_weather_type"] == "sunny"
    
    def test_get_weather_continuity_changed(self):
        """Test weather continuity when weather changed"""
        memory = SessionMemory()
        
        # Add previous weather
        memory.add_script(
            script_type="weather",
            content="Sunny day",
            metadata={"weather_type": "sunny"}
        )
        
        # New weather is rainy
        current_weather = {"weather_type": "rainy"}
        context = memory.get_weather_continuity_context("Appalachia", current_weather)
        
        assert context["weather_changed"] is True
        assert context["last_weather_type"] == "sunny"
        assert context["continuity_phrase"] is not None
    
    def test_weather_continuity_phrase_generation(self):
        """Test that continuity phrases are generated"""
        memory = SessionMemory()
        
        memory.add_script(
            script_type="weather",
            content="Rainy",
            metadata={"weather_type": "rainy"}
        )
        
        current_weather = {"weather_type": "sunny"}
        context = memory.get_weather_continuity_context("Appalachia", current_weather)
        
        phrase = context["continuity_phrase"]
        assert phrase is not None
        assert isinstance(phrase, str)
        assert len(phrase) > 0
    
    def test_has_notable_history(self):
        """Test has_notable_history flag"""
        memory = SessionMemory()
        
        # Add several scripts
        for i in range(4):
            memory.add_script(
                script_type="weather",
                content=f"Weather {i}",
                metadata={"weather_type": "sunny"}
            )
        
        current_weather = {"weather_type": "sunny"}
        context = memory.get_weather_continuity_context("Appalachia", current_weather)
        
        assert context["has_notable_history"] is True


@pytest.mark.mock
class TestSessionMemoryStoryBeats:
    """Test suite for story beat tracking (Phase 7)"""
    
    def test_add_story_beat(self):
        """Test adding story beat"""
        memory = SessionMemory()
        
        beat_info = {
            "beat_type": "introduction",
            "content": "Story starts",
            "timestamp": "2102-08-15T08:00:00"
        }
        
        memory.add_story_beat(beat_info)
        
        assert len(memory.recent_story_beats) == 1
        assert memory.recent_story_beats[0] == beat_info
    
    def test_story_beat_max_limit(self):
        """Test story beat max limit enforcement"""
        memory = SessionMemory()
        
        # Add more than max (default 15)
        for i in range(20):
            memory.add_story_beat({"beat_id": i})
        
        assert len(memory.recent_story_beats) <= memory.max_story_beats
    
    def test_get_recent_story_beats(self):
        """Test getting recent story beats"""
        memory = SessionMemory()
        
        for i in range(10):
            memory.add_story_beat({"beat_id": i})
        
        recent = memory.get_recent_story_beats(count=3)
        
        assert len(recent) == 3
        # Should be most recent
        assert recent[-1]["beat_id"] == 9


@pytest.mark.mock
class TestSessionMemoryPersistence:
    """Test suite for serialization and persistence"""
    
    def test_to_dict(self):
        """Test converting memory to dictionary"""
        memory = SessionMemory()
        
        memory.add_script(
            script_type="weather",
            content="Test content"
        )
        
        data = memory.to_dict()
        
        assert "session_start" in data
        assert "segment_count" in data
        assert "recent_scripts" in data
        assert "catchphrase_history" in data
        assert "mentioned_topics" in data
        assert "recent_story_beats" in data
    
    def test_from_dict(self):
        """Test restoring memory from dictionary"""
        # Create and populate memory
        memory1 = SessionMemory()
        memory1.add_script(
            script_type="weather",
            content="Test content",
            catchphrases_used=["Stay safe!"]
        )
        
        # Serialize
        data = memory1.to_dict()
        
        # Restore to new instance
        memory2 = SessionMemory()
        memory2.from_dict(data)
        
        # Verify restoration
        assert memory2.segment_count == memory1.segment_count
        assert len(memory2.recent_scripts) == len(memory1.recent_scripts)
        assert memory2.catchphrase_history == memory1.catchphrase_history
    
    def test_round_trip_serialization(self):
        """Test complete round-trip serialization"""
        memory1 = SessionMemory(max_history=5, dj_name="Julie")
        
        # Add various data
        memory1.add_script("weather", "Sunny", metadata={"temp": 75})
        memory1.add_script("news", "Update", catchphrases_used=["Stay tuned"])
        memory1.add_story_beat({"beat_id": 1})
        
        # Serialize and deserialize
        data = memory1.to_dict()
        memory2 = SessionMemory()
        memory2.from_dict(data)
        
        # Verify all data preserved
        assert memory2.segment_count == 2
        assert len(memory2.recent_scripts) == 2
        assert len(memory2.catchphrase_history) == 1
        assert len(memory2.recent_story_beats) == 1


@pytest.mark.mock
class TestSessionMemoryReset:
    """Test suite for memory reset"""
    
    def test_reset_clears_all_data(self):
        """Test that reset clears all memory"""
        memory = SessionMemory()
        
        # Populate with data
        memory.add_script("weather", "Test", catchphrases_used=["Stay safe"])
        memory.add_story_beat({"beat_id": 1})
        
        # Reset
        memory.reset()
        
        # Verify session data is cleared
        assert len(memory.recent_scripts) == 0
        assert len(memory.catchphrase_history) == 0
        assert len(memory.mentioned_topics) == 0
        assert memory.segment_count == 0
        # Note: recent_story_beats is NOT cleared by reset() - it persists across sessions
    
    def test_reset_updates_session_start(self):
        """Test that reset updates session start time"""
        memory = SessionMemory()
        
        original_start = memory.session_start
        
        # Wait a tiny bit
        import time
        time.sleep(0.01)
        
        memory.reset()
        
        # Session start should be updated
        assert memory.session_start > original_start
