"""
Test Suite for Enhanced Broadcast Scheduler (Phase 2)

Tests the priority-based scheduling, constraint generation,
and structured segment planning.
"""

import pytest
from broadcast_scheduler_v2 import BroadcastSchedulerV2, TimeOfDay
from segment_plan import (
    SegmentPlan,
    SegmentType,
    Priority,
    ValidationConstraints
)


class TestSchedulerPrioritySystem:
    """Test priority-based segment selection."""
    
    def test_emergency_weather_has_highest_priority(self):
        """Emergency weather should override all other segments."""
        scheduler = BroadcastSchedulerV2()
        
        context = {
            'dj_name': 'Julie',
            'dj_year': 2102,
            'dj_region': 'Appalachia',
            'weather_state': {
                'type': 'rad_storm',
                'date': '2102-06-15',
                'is_emergency': True,
                'severity': 'critical'
            },
            'enable_stories': True
        }
        
        plan = scheduler.get_next_segment_plan(hour=6, context=context)
        
        assert plan.segment_type == SegmentType.EMERGENCY_WEATHER
        assert plan.priority == Priority.CRITICAL
        assert plan.is_emergency()
        assert plan.metadata['weather_type'] == 'rad_storm'
    
    def test_time_check_priority_over_filler(self):
        """Time checks should have priority over story/gossip."""
        scheduler = BroadcastSchedulerV2()
        
        context = {
            'dj_name': 'Julie',
            'dj_year': 2102,
            'dj_region': 'Appalachia',
            'enable_stories': True
        }
        
        plan = scheduler.get_next_segment_plan(hour=10, context=context)
        
        assert plan.segment_type == SegmentType.TIME_CHECK
        assert plan.priority == Priority.REQUIRED
        assert plan.is_required()
    
    def test_weather_priority_at_scheduled_time(self):
        """Weather should be scheduled at 6am, 12pm, 5pm."""
        scheduler = BroadcastSchedulerV2()
        
        context = {
            'dj_name': 'Julie',
            'dj_year': 2102,
            'dj_region': 'Appalachia'
        }
        
        # Mark time check as done so weather is next
        scheduler.time_check_done_hours.add(6)
        
        plan = scheduler.get_next_segment_plan(hour=6, context=context)
        
        assert plan.segment_type == SegmentType.WEATHER
        assert plan.priority == Priority.REQUIRED
        assert plan.metadata['hour'] == 6
        assert plan.metadata['weather_context'] == 'morning'
    
    def test_news_priority_at_scheduled_time(self):
        """News should be scheduled at 6am, 12pm, 5pm."""
        scheduler = BroadcastSchedulerV2()
        
        context = {
            'dj_name': 'Julie',
            'dj_year': 2102,
            'dj_region': 'Appalachia'
        }
        
        # Mark time check and weather as done
        scheduler.time_check_done_hours.add(12)
        scheduler.weather_done_hours.add(12)
        
        plan = scheduler.get_next_segment_plan(hour=12, context=context)
        
        assert plan.segment_type == SegmentType.NEWS
        assert plan.priority == Priority.REQUIRED
        assert plan.metadata['hour'] == 12
        assert 'category' in plan.metadata
    
    def test_gossip_as_default_filler(self):
        """Gossip should be returned when no required segments are pending."""
        scheduler = BroadcastSchedulerV2()
        
        context = {
            'dj_name': 'Julie',
            'dj_year': 2102,
            'dj_region': 'Appalachia',
            'enable_stories': False
        }
        
        # Mark all required segments as done
        scheduler.time_check_done_hours.add(10)
        
        plan = scheduler.get_next_segment_plan(hour=10, context=context)
        
        assert plan.segment_type == SegmentType.GOSSIP
        assert plan.priority == Priority.FILLER
        assert not plan.is_required()


class TestConstraintGeneration:
    """Test validation constraint generation for different segment types."""
    
    def test_time_check_constraints(self):
        """Time check constraints should be minimal."""
        scheduler = BroadcastSchedulerV2()
        
        context = {
            'dj_name': 'Julie',
            'dj_year': 2102,
            'dj_region': 'Appalachia'
        }
        
        plan = scheduler.get_next_segment_plan(hour=10, context=context)
        
        assert plan.segment_type == SegmentType.TIME_CHECK
        assert plan.constraints.max_year == 2102
        assert 'Appalachia' in plan.constraints.allowed_regions
        assert plan.constraints.required_tone == 'casual'
        assert plan.constraints.max_length == 300
    
    def test_weather_constraints_include_dj_limits(self):
        """Weather constraints should respect DJ knowledge limits."""
        scheduler = BroadcastSchedulerV2()
        
        context = {
            'dj_name': 'Julie',
            'dj_year': 2102,
            'dj_region': 'Appalachia'
        }
        
        scheduler.time_check_done_hours.add(6)
        plan = scheduler.get_next_segment_plan(hour=6, context=context)
        
        assert plan.segment_type == SegmentType.WEATHER
        assert plan.constraints.max_year == 2102
        assert 'Institute' in plan.constraints.forbidden_topics or \
               'Institute' in plan.constraints.forbidden_factions
    
    def test_news_constraints_include_category(self):
        """News constraints should include the selected category."""
        scheduler = BroadcastSchedulerV2()
        
        context = {
            'dj_name': 'Julie',
            'dj_year': 2102,
            'dj_region': 'Appalachia'
        }
        
        scheduler.time_check_done_hours.add(12)
        scheduler.weather_done_hours.add(12)
        plan = scheduler.get_next_segment_plan(hour=12, context=context)
        
        assert plan.segment_type == SegmentType.NEWS
        assert plan.metadata['category'] in plan.constraints.required_elements
        assert plan.constraints.required_tone == 'journalistic'
    
    def test_constraints_to_prompt_text(self):
        """Constraints should convert to formatted prompt text."""
        constraints = ValidationConstraints(
            max_year=2102,
            forbidden_topics=['Institute', 'Synths'],
            forbidden_factions=['Railroad'],
            required_tone='casual'
        )
        
        prompt_text = constraints.to_prompt_text()
        
        assert '2102' in prompt_text
        assert 'Institute' in prompt_text
        assert 'Railroad' in prompt_text
        assert 'casual' in prompt_text


class TestSchedulingLogic:
    """Test scheduling logic and state management."""
    
    def test_time_check_only_once_per_hour(self):
        """Time check should only be scheduled once per hour."""
        scheduler = BroadcastSchedulerV2()
        
        context = {
            'dj_name': 'Julie',
            'dj_year': 2102,
            'dj_region': 'Appalachia'
        }
        
        # First call - should get time check
        plan1 = scheduler.get_next_segment_plan(hour=10, context=context)
        assert plan1.segment_type == SegmentType.TIME_CHECK
        
        # Second call same hour - should get gossip (no stories enabled)
        plan2 = scheduler.get_next_segment_plan(hour=10, context=context)
        assert plan2.segment_type == SegmentType.GOSSIP
    
    def test_weather_only_at_fixed_hours(self):
        """Weather should only be scheduled at 6am, 12pm, 5pm."""
        scheduler = BroadcastSchedulerV2()
        
        context = {
            'dj_name': 'Julie',
            'dj_year': 2102,
            'dj_region': 'Appalachia',
            'enable_stories': False
        }
        
        # Hour 10 (not weather time) - should not get weather
        scheduler.time_check_done_hours.add(10)
        plan = scheduler.get_next_segment_plan(hour=10, context=context)
        assert plan.segment_type != SegmentType.WEATHER
        
        # Hour 6 (weather time) - should get weather after time check
        scheduler.time_check_done_hours.add(6)
        plan = scheduler.get_next_segment_plan(hour=6, context=context)
        assert plan.segment_type == SegmentType.WEATHER
    
    def test_news_category_variety(self):
        """News categories should vary over multiple broadcasts."""
        scheduler = BroadcastSchedulerV2()
        
        context = {
            'dj_name': 'Julie',
            'dj_year': 2102,
            'dj_region': 'Appalachia'
        }
        
        categories = []
        
        # Generate news at different hours
        for hour in [6, 12, 17]:
            scheduler.time_check_done_hours.add(hour)
            scheduler.weather_done_hours.add(hour)
            plan = scheduler.get_next_segment_plan(hour=hour, context=context)
            categories.append(plan.metadata['category'])
            scheduler.reset()  # Reset for next hour
        
        # Should have some variety (at least 2 different categories)
        unique_categories = len(set(categories))
        assert unique_categories >= 2
    
    def test_state_reset(self):
        """Reset should clear all tracking."""
        scheduler = BroadcastSchedulerV2()
        
        # Add some state
        scheduler.time_check_done_hours.add(10)
        scheduler.news_done_hours.add(6)
        scheduler.weather_done_hours.add(12)
        scheduler.recent_news_categories.append('combat')
        
        # Reset
        scheduler.reset()
        
        # Verify cleared
        assert len(scheduler.time_check_done_hours) == 0
        assert len(scheduler.news_done_hours) == 0
        assert len(scheduler.weather_done_hours) == 0
        assert len(scheduler.recent_news_categories) == 0


class TestSegmentPlan:
    """Test SegmentPlan dataclass functionality."""
    
    def test_segment_plan_rag_topic_mapping(self):
        """SegmentPlan should map segment types to RAG topics."""
        plan_weather = SegmentPlan(
            segment_type=SegmentType.WEATHER,
            priority=Priority.REQUIRED,
            constraints=ValidationConstraints()
        )
        assert plan_weather.get_rag_topic() == 'regional_climate'
        
        plan_news = SegmentPlan(
            segment_type=SegmentType.NEWS,
            priority=Priority.REQUIRED,
            constraints=ValidationConstraints()
        )
        assert plan_news.get_rag_topic() == 'current_events'
        
        plan_story = SegmentPlan(
            segment_type=SegmentType.STORY,
            priority=Priority.FILLER,
            constraints=ValidationConstraints()
        )
        assert plan_story.get_rag_topic() == 'story_arc'
        
        plan_time = SegmentPlan(
            segment_type=SegmentType.TIME_CHECK,
            priority=Priority.REQUIRED,
            constraints=ValidationConstraints()
        )
        assert plan_time.get_rag_topic() is None
    
    def test_segment_plan_is_required(self):
        """SegmentPlan should correctly identify required segments."""
        plan_required = SegmentPlan(
            segment_type=SegmentType.NEWS,
            priority=Priority.REQUIRED,
            constraints=ValidationConstraints()
        )
        assert plan_required.is_required()
        
        plan_filler = SegmentPlan(
            segment_type=SegmentType.GOSSIP,
            priority=Priority.FILLER,
            constraints=ValidationConstraints()
        )
        assert not plan_filler.is_required()
    
    def test_segment_plan_to_dict(self):
        """SegmentPlan should serialize to dictionary."""
        plan = SegmentPlan(
            segment_type=SegmentType.WEATHER,
            priority=Priority.REQUIRED,
            constraints=ValidationConstraints(max_year=2102),
            metadata={'hour': 6, 'weather_context': 'morning'}
        )
        
        data = plan.to_dict()
        
        assert data['segment_type'] == 'weather'
        assert data['priority'] == 'REQUIRED'
        assert data['constraints']['temporal']['max_year'] == 2102
        assert data['metadata']['hour'] == 6


class TestBackwardsCompatibility:
    """Test backwards compatibility with old scheduler API."""
    
    def test_legacy_get_required_segment_for_hour(self):
        """Legacy method should still work."""
        from broadcast_scheduler_v2 import BroadcastScheduler
        
        scheduler = BroadcastScheduler()
        
        # Should get time check first
        segment = scheduler.get_required_segment_for_hour(10)
        assert segment == "time_check"
        
        # Second call - no required segments at hour 10
        segment = scheduler.get_required_segment_for_hour(10)
        assert segment == "gossip"  # Default filler
    
    def test_legacy_mark_segment_done(self):
        """Legacy mark_segment_done should still work."""
        from broadcast_scheduler_v2 import BroadcastScheduler
        
        scheduler = BroadcastScheduler()
        
        scheduler.mark_segment_done("time_check", 10)
        assert 10 in scheduler.time_check_done_hours
        
        scheduler.mark_segment_done("news", 6)
        assert 6 in scheduler.news_done_hours
    
    def test_legacy_get_segments_status(self):
        """Legacy get_segments_status should still work."""
        from broadcast_scheduler_v2 import BroadcastScheduler
        
        scheduler = BroadcastScheduler()
        
        scheduler.time_check_done_hours.add(10)
        scheduler.news_done_hours.add(6)
        
        status = scheduler.get_segments_status()
        
        assert 10 in status['time_checks_done']
        assert 6 in status['news_done']
        assert status['news_hours'] == [6, 12, 17]


class TestTimeOfDay:
    """Test time of day detection."""
    
    def test_time_of_day_morning(self):
        """Hours 6-10 should be morning."""
        scheduler = BroadcastSchedulerV2()
        
        assert scheduler._get_time_of_day(6) == TimeOfDay.MORNING
        assert scheduler._get_time_of_day(9) == TimeOfDay.MORNING
    
    def test_time_of_day_midday(self):
        """Hours 10-14 should be midday."""
        scheduler = BroadcastSchedulerV2()
        
        assert scheduler._get_time_of_day(10) == TimeOfDay.MIDDAY
        assert scheduler._get_time_of_day(13) == TimeOfDay.MIDDAY
    
    def test_time_of_day_afternoon(self):
        """Hours 14-18 should be afternoon."""
        scheduler = BroadcastSchedulerV2()
        
        assert scheduler._get_time_of_day(14) == TimeOfDay.AFTERNOON
        assert scheduler._get_time_of_day(17) == TimeOfDay.AFTERNOON
    
    def test_time_of_day_evening(self):
        """Hours 18-22 should be evening."""
        scheduler = BroadcastSchedulerV2()
        
        assert scheduler._get_time_of_day(18) == TimeOfDay.EVENING
        assert scheduler._get_time_of_day(21) == TimeOfDay.EVENING
    
    def test_time_of_day_night(self):
        """Hours 22-6 should be night."""
        scheduler = BroadcastSchedulerV2()
        
        assert scheduler._get_time_of_day(22) == TimeOfDay.NIGHT
        assert scheduler._get_time_of_day(0) == TimeOfDay.NIGHT
        assert scheduler._get_time_of_day(5) == TimeOfDay.NIGHT


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
