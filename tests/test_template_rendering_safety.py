"""
Template Rendering Safety Tests

Tests to verify all segment templates render correctly when story_context
and session_context variables are None, ensuring no Jinja2 errors or
undefined variable issues.

Phase 1.4 of Story Integration Fix Plan
"""

import pytest
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, UndefinedError


class TestTemplateRenderingSafety:
    """Test that templates handle missing context variables gracefully."""

    @pytest.fixture
    def jinja_env(self) -> Environment:
        """Create Jinja2 environment with template directory."""
        template_dir = Path(__file__).parent.parent / "tools" / "script-generator" / "templates"
        return Environment(loader=FileSystemLoader(str(template_dir)))

    @pytest.fixture
    def base_context(self) -> dict:
        """Provide minimal context required by all templates."""
        return {
            "personality": {
                "name": "Julie",
                "system_prompt": "You are Julie, a curious and friendly DJ.",
                "tone": "warm and conversational",
                "do": [
                    "Be curious and ask questions",
                    "Share excitement about the wasteland"
                ],
                "dont": [
                    "Don't be pessimistic",
                    "Don't use technical jargon"
                ],
                "catchphrases": ["Stay safe out there!", "Keep exploring!"],
                "examples": [
                    {
                        "type": "intro",
                        "text": "Hey there, wastelanders! This is Julie coming to you live..."
                    },
                    {
                        "type": "anecdote",
                        "text": "I heard someone found a pre-war radio..."
                    }
                ]
            },
            "catchphrase": {
                "should_use": False,
                "opening": None,
                "closing": None
            },
            "voice_elements": {
                "filler_words": ["uh", "you know", "like"],
                "sentence_variety_hint": "Mix short and long sentences",
                "spontaneous_element": "Add a personal thought"
            },
            "lore_context": "The Appalachian wasteland is recovering from the Scorched plague."
        }

    def test_gossip_template_with_none_story_context(self, jinja_env, base_context):
        """Gossip template should render without errors when story_context is None."""
        template = jinja_env.get_template("gossip.jinja2")
        
        context = {
            **base_context,
            "rumor_type": "settlement news",
            "character": "Duchess",
            "faction": "Foundation",
            "variety_hints": "Avoid repeating settlement names",
            "story_context": None,  # Explicitly None
            "session_context": None,
            "retry_feedback": None
        }
        
        result = template.render(context)
        
        # Verify template rendered successfully
        assert result is not None
        assert len(result) > 0
        assert "None" not in result
        assert "undefined" not in result.lower()
        assert "ACTIVE STORY BEATS" not in result  # Should not appear when None
        assert "BROADCAST CONTINUITY" not in result  # Should not appear when None
        assert "LORE CONTEXT" in result  # Should still appear

    def test_gossip_template_with_none_session_context(self, jinja_env, base_context):
        """Gossip template should render without errors when session_context is None."""
        template = jinja_env.get_template("gossip.jinja2")
        
        context = {
            **base_context,
            "rumor_type": "wasteland rumors",
            "variety_hints": None,
            "story_context": None,
            "session_context": None,  # Explicitly None
            "retry_feedback": None
        }
        
        result = template.render(context)
        
        assert result is not None
        assert "BROADCAST CONTINUITY" not in result
        assert "undefined" not in result.lower()

    def test_gossip_template_with_both_contexts_none(self, jinja_env, base_context):
        """Gossip template should render when both story and session contexts are None."""
        template = jinja_env.get_template("gossip.jinja2")
        
        context = {
            **base_context,
            "rumor_type": "faction politics",
            "faction": "Raiders",
            "story_context": None,  # Both None
            "session_context": None,
            "variety_hints": None,
            "retry_feedback": None
        }
        
        result = template.render(context)
        
        assert result is not None
        assert "ACTIVE STORY BEATS" not in result
        assert "BROADCAST CONTINUITY" not in result
        assert "Share some wasteland gossip about faction politics" in result

    def test_time_template_with_none_contexts(self, jinja_env, base_context):
        """Time template should render without errors when contexts are None."""
        template = jinja_env.get_template("time.jinja2")
        
        context = {
            **base_context,
            "hour": 14,
            "time_of_day": "afternoon",
            "special_event": None,
            "story_context": None,
            "session_context": None
        }
        
        result = template.render(context)
        
        assert result is not None
        assert "None" not in result
        assert "undefined" not in result.lower()
        assert "ACTIVE STORY BEATS" not in result
        assert "BROADCAST CONTINUITY" not in result
        assert "14:00" in result

    def test_weather_template_with_none_contexts(self, jinja_env, base_context):
        """Weather template should render without errors when contexts are None."""
        template = jinja_env.get_template("weather.jinja2")
        
        context = {
            **base_context,
            "weather_type": "rad-storm",
            "time_of_day": "evening",
            "hour": 18,
            "temperature": 72,
            "weather_continuity": None,
            "notable_weather_events": None,
            "story_context": None,
            "session_context": None
        }
        
        result = template.render(context)
        
        assert result is not None
        assert "None" not in result
        assert "undefined" not in result.lower()
        assert "ACTIVE STORY BEATS" not in result
        assert "BROADCAST CONTINUITY" not in result
        assert "rad-storm" in result

    def test_gossip_template_with_story_context_present(self, jinja_env, base_context):
        """Gossip template should include story context when provided."""
        template = jinja_env.get_template("gossip.jinja2")
        
        story_context = """
Story: The Lost Caravan (Daily, Act 1/1)
Summary: A supply caravan heading to Foundation has gone missing near Helvetia.
Entities: Foundation, Duchess, Helvetia
Themes: mystery, survival
"""
        
        context = {
            **base_context,
            "rumor_type": "missing persons",
            "story_context": story_context,
            "session_context": None,
            "variety_hints": None,
            "retry_feedback": None
        }
        
        result = template.render(context)
        
        assert result is not None
        assert "ACTIVE STORY BEATS" in result
        assert "The Lost Caravan" in result
        assert "that weaves in the story elements above" in result

    def test_gossip_template_with_session_context_present(self, jinja_env, base_context):
        """Gossip template should include session context when provided."""
        template = jinja_env.get_template("gossip.jinja2")
        
        session_context = """
Recent topics covered:
- Settlement trade routes
- Scorched sightings near Watoga
Last mood: cautiously optimistic
"""
        
        context = {
            **base_context,
            "rumor_type": "trade news",
            "story_context": None,
            "session_context": session_context,
            "variety_hints": None,
            "retry_feedback": None
        }
        
        result = template.render(context)
        
        assert result is not None
        assert "BROADCAST CONTINUITY" in result
        assert "Recent topics covered" in result

    def test_all_templates_handle_missing_optional_fields(self, jinja_env, base_context):
        """All templates should handle missing optional fields gracefully."""
        templates_and_contexts = [
            ("gossip.jinja2", {
                **base_context,
                "rumor_type": "wasteland news",
                "story_context": None,
                "session_context": None,
                "variety_hints": None,
                "retry_feedback": None,
                "character": None,  # Optional
                "faction": None     # Optional
            }),
            ("time.jinja2", {
                **base_context,
                "hour": 10,
                "time_of_day": "morning",
                "story_context": None,
                "session_context": None,
                "special_event": None
            }),
            ("weather.jinja2", {
                **base_context,
                "weather_type": "clear",
                "time_of_day": "midday",
                "hour": 12,
                "temperature": 68,
                "story_context": None,
                "session_context": None,
                "weather_continuity": None,
                "notable_weather_events": None
            }),
            ("news.jinja2", {
                **base_context,
                "news_topic": "settlement news",
                "story_context": None,
                "session_context": None,
                "faction": None,    # Optional
                "location": None    # Optional
            }),
            ("emergency_weather.jinja2", {
                **base_context,
                "year": 2102,
                "emergency_type": "dust_storm",
                "severity": "moderate",
                "location": "Charleston",
                "duration_hours": 1,
                "rag_context": "Charleston is in the Ash Heap region.",
                "shelter_instructions": "Seal windows and doors.",
                "story_context": None,
                "session_context": None,
                "temperature": None,  # Optional
                "nearby_shelters": None,  # Optional
                "catchphrase": {"should_use": False, "emergency_alert": None, "opening": None}
            }),
            ("music_intro.jinja2", {
                **base_context,
                "song_title": "Anything Goes",
                "story_context": None,
                "session_context": None,
                "artist": None,  # Optional
                "era": None,     # Optional
                "mood": None     # Optional
            })
        ]
        
        for template_name, context in templates_and_contexts:
            template = jinja_env.get_template(template_name)
            result = template.render(context)
            
            assert result is not None, f"{template_name} failed to render"
            assert len(result) > 0, f"{template_name} produced empty output"
            assert "None" not in result, f"{template_name} contains 'None' in output"
            assert "undefined" not in result.lower(), f"{template_name} contains 'undefined'"

    def test_conditional_task_modification_in_gossip(self, jinja_env, base_context):
        """Gossip TASK line should change based on story_context presence."""
        template = jinja_env.get_template("gossip.jinja2")
        
        # Without story_context
        context_without = {
            **base_context,
            "rumor_type": "general news",
            "story_context": None,
            "session_context": None,
            "variety_hints": None,
            "retry_feedback": None
        }
        result_without = template.render(context_without)
        assert "TASK: Share some wasteland gossip about general news." in result_without
        assert "weaves in the story elements" not in result_without
        
        # With story_context
        context_with = {
            **base_context,
            "rumor_type": "general news",
            "story_context": "Story: Test Story\nSummary: A test.",
            "session_context": None,
            "variety_hints": None,
            "retry_feedback": None
        }
        result_with = template.render(context_with)
        assert "TASK: Share some wasteland gossip that weaves in the story elements above about general news." in result_with

    def test_news_template_with_none_contexts(self, jinja_env, base_context):
        """News template should render without errors when contexts are None."""
        template = jinja_env.get_template("news.jinja2")
        
        context = {
            **base_context,
            "news_topic": "settlement expansion",
            "faction": "Foundation",
            "location": "Crater",
            "story_context": None,
            "session_context": None
        }
        
        result = template.render(context)
        
        assert result is not None
        assert "None" not in result
        assert "undefined" not in result.lower()
        assert "ACTIVE STORY BEATS" not in result
        assert "BROADCAST CONTINUITY" not in result
        assert "settlement expansion" in result

    def test_news_template_with_story_context(self, jinja_env, base_context):
        """News template should include story context when provided."""
        template = jinja_env.get_template("news.jinja2")
        
        story_context = """
Story: Trade Route Troubles (Weekly, Act 2/3)
Summary: Raiders have been attacking supply convoys between Foundation and Crater.
Entities: Foundation, Crater, Raiders
"""
        
        context = {
            **base_context,
            "news_topic": "trade disruptions",
            "faction": "Foundation",
            "story_context": story_context,
            "session_context": None
        }
        
        result = template.render(context)
        
        assert result is not None
        assert "ACTIVE STORY BEATS" in result
        assert "Trade Route Troubles" in result
        assert "that weaves in the story elements above" in result

    def test_emergency_weather_template_with_none_contexts(self, jinja_env, base_context):
        """Emergency weather template should render without errors when contexts are None."""
        template = jinja_env.get_template("emergency_weather.jinja2")
        
        context = {
            **base_context,
            "year": 2102,
            "emergency_type": "rad_storm",
            "severity": "severe",
            "location": "Flatwoods",
            "duration_hours": 3,
            "temperature": 68,
            "rag_context": "Flatwoods is a settled area in the Forest region.",
            "shelter_instructions": "Seek underground shelter immediately.",
            "nearby_shelters": [
                {"name": "Vault 76", "direction": "North", "distance": "2 miles"},
                {"name": "Overseer's Camp", "direction": "East", "distance": "1 mile"}
            ],
            "story_context": None,
            "session_context": None,
            "catchphrase": {
                "should_use": False,
                "emergency_alert": None,
                "opening": None
            }
        }
        
        result = template.render(context)
        
        assert result is not None
        assert "None" not in result
        assert "undefined" not in result.lower()
        assert "ACTIVE STORY BEATS" not in result
        assert "BROADCAST CONTINUITY" not in result
        assert "rad_storm" in result

    def test_music_intro_template_with_none_contexts(self, jinja_env, base_context):
        """Music intro template should render without errors when contexts are None."""
        template = jinja_env.get_template("music_intro.jinja2")
        
        context = {
            **base_context,
            "song_title": "A Kiss To Build A Dream On",
            "artist": "Louis Armstrong",
            "era": "1950s",
            "mood": "romantic",
            "story_context": None,
            "session_context": None
        }
        
        result = template.render(context)
        
        assert result is not None
        assert "None" not in result
        assert "undefined" not in result.lower()
        assert "ACTIVE STORY BEATS" not in result
        assert "BROADCAST CONTINUITY" not in result
        assert "A Kiss To Build A Dream On" in result

    def test_all_six_templates_handle_none_contexts(self, jinja_env, base_context):
        """All six segment templates should handle None contexts gracefully."""
        templates_and_contexts = [
            ("gossip.jinja2", {
                **base_context,
                "rumor_type": "wasteland news",
                "story_context": None,
                "session_context": None,
                "variety_hints": None,
                "retry_feedback": None
            }),
            ("time.jinja2", {
                **base_context,
                "hour": 10,
                "time_of_day": "morning",
                "story_context": None,
                "session_context": None
            }),
            ("weather.jinja2", {
                **base_context,
                "weather_type": "clear",
                "time_of_day": "midday",
                "hour": 12,
                "temperature": 68,
                "story_context": None,
                "session_context": None,
                "weather_continuity": None,
                "notable_weather_events": None
            }),
            ("news.jinja2", {
                **base_context,
                "news_topic": "settlement news",
                "story_context": None,
                "session_context": None
            }),
            ("emergency_weather.jinja2", {
                **base_context,
                "year": 2102,
                "emergency_type": "rad_storm",
                "severity": "critical",
                "location": "Watoga",
                "duration_hours": 2,
                "rag_context": "Watoga is in the Cranberry Bog.",
                "shelter_instructions": "Seek shelter in basement structures.",
                "story_context": None,
                "session_context": None,
                "catchphrase": {"should_use": False, "emergency_alert": None, "opening": None}
            }),
            ("music_intro.jinja2", {
                **base_context,
                "song_title": "Blue Moon",
                "artist": "Frank Sinatra",
                "story_context": None,
                "session_context": None
            })
        ]
        
        for template_name, context in templates_and_contexts:
            template = jinja_env.get_template(template_name)
            result = template.render(context)
            
            assert result is not None, f"{template_name} failed to render"
            assert len(result) > 0, f"{template_name} produced empty output"
            assert "None" not in result, f"{template_name} contains 'None' in output"
            assert "undefined" not in result.lower(), f"{template_name} contains 'undefined'"
            # Verify conditional blocks don't appear when None
            assert "ACTIVE STORY BEATS" not in result, f"{template_name} shows story beats when None"
            assert "BROADCAST CONTINUITY" not in result, f"{template_name} shows session context when None"
