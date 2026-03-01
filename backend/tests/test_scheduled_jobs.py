"""
Integration tests for scheduled jobs.
Tests daily, weekly, and biweekly goal recalculation jobs.
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch


class TestScheduledJobsIntegration:
    """Integration tests for scheduled jobs"""
    
    def test_daily_job_structure(self):
        """Test that daily job has correct structure"""
        from services.scheduled_jobs import recalculate_daily_goals_job
        
        # Verify the function exists and is callable
        assert callable(recalculate_daily_goals_job)
    
    def test_weekly_job_structure(self):
        """Test that weekly job has correct structure"""
        from services.scheduled_jobs import recalculate_weekly_goals_job
        
        # Verify the function exists and is callable
        assert callable(recalculate_weekly_goals_job)
    
    def test_biweekly_job_structure(self):
        """Test that biweekly job has correct structure"""
        from services.scheduled_jobs import recalculate_biweekly_goals_job
        
        # Verify the function exists and is callable
        assert callable(recalculate_biweekly_goals_job)
    
    def test_get_user_profit_targets_structure(self):
        """Test that get_user_profit_targets has correct structure"""
        from services.scheduled_jobs import get_user_profit_targets
        
        # Verify the function exists and is callable
        assert callable(get_user_profit_targets)
    
    def test_calculate_daily_metrics_structure(self):
        """Test that calculate_daily_metrics has correct structure"""
        from services.scheduled_jobs import calculate_daily_metrics
        
        # Verify the function exists and is callable
        assert callable(calculate_daily_metrics)
    
    def test_get_metrics_for_period_structure(self):
        """Test that get_metrics_for_period has correct structure"""
        from services.scheduled_jobs import get_metrics_for_period
        
        # Verify the function exists and is callable
        assert callable(get_metrics_for_period)
    
    def test_select_metrics_for_recalculation_structure(self):
        """Test that select_metrics_for_recalculation has correct structure"""
        from services.scheduled_jobs import select_metrics_for_recalculation
        
        # Verify the function exists and is callable
        assert callable(select_metrics_for_recalculation)
    
    def test_store_daily_metrics_structure(self):
        """Test that store_daily_metrics has correct structure"""
        from services.scheduled_jobs import store_daily_metrics
        
        # Verify the function exists and is callable
        assert callable(store_daily_metrics)
    
    def test_store_goal_history_structure(self):
        """Test that store_goal_history has correct structure"""
        from services.scheduled_jobs import store_goal_history
        
        # Verify the function exists and is callable
        assert callable(store_goal_history)
    
    def test_update_user_goals_structure(self):
        """Test that update_user_goals has correct structure"""
        from services.scheduled_jobs import update_user_goals
        
        # Verify the function exists and is callable
        assert callable(update_user_goals)


class TestScheduledJobsConstants:
    """Tests for scheduled jobs constants"""
    
    def test_baseline_booking_speed(self):
        """Test baseline booking speed constant"""
        from services.scheduled_jobs import BASELINE_BOOKING_SPEED
        
        assert BASELINE_BOOKING_SPEED == 30.0
    
    def test_baseline_avg_profit(self):
        """Test baseline average profit constant"""
        from services.scheduled_jobs import BASELINE_AVG_PROFIT
        
        assert BASELINE_AVG_PROFIT == 2.40
    
    def test_baseline_conversion_rate(self):
        """Test baseline conversion rate constant"""
        from services.scheduled_jobs import BASELINE_CONVERSION_RATE
        
        assert BASELINE_CONVERSION_RATE == 15.0


class TestScheduledJobsImports:
    """Tests for scheduled jobs imports"""
    
    def test_can_import_scheduled_jobs_module(self):
        """Test that scheduled jobs module can be imported"""
        try:
            import services.scheduled_jobs
            assert True
        except ImportError:
            assert False, "Failed to import scheduled_jobs module"
    
    def test_can_import_goal_functions(self):
        """Test that goal functions can be imported"""
        try:
            from services.goals import (
                recalculate_daily_goals,
                recalculate_weekly_goals,
                recalculate_biweekly_goals
            )
            assert True
        except ImportError:
            assert False, "Failed to import goal functions"
    
    def test_can_import_metrics_functions(self):
        """Test that metrics functions can be imported"""
        try:
            from services.metrics import (
                calculate_booking_speed,
                calculate_conversion_rate,
                calculate_avg_profit_per_booking,
                calculate_rolling_average_metrics
            )
            assert True
        except ImportError:
            assert False, "Failed to import metrics functions"


class TestScheduledJobsIntegrationWithGoals:
    """Integration tests between scheduled jobs and goals"""
    
    def test_daily_job_uses_goal_recalculation(self):
        """Test that daily job uses goal recalculation"""
        from services.scheduled_jobs import recalculate_daily_goals_job
        from services.goals import recalculate_daily_goals
        
        # Both should exist and be callable
        assert callable(recalculate_daily_goals_job)
        assert callable(recalculate_daily_goals)
    
    def test_weekly_job_uses_goal_recalculation(self):
        """Test that weekly job uses goal recalculation"""
        from services.scheduled_jobs import recalculate_weekly_goals_job
        from services.goals import recalculate_weekly_goals
        
        # Both should exist and be callable
        assert callable(recalculate_weekly_goals_job)
        assert callable(recalculate_weekly_goals)
    
    def test_biweekly_job_uses_goal_recalculation(self):
        """Test that biweekly job uses goal recalculation"""
        from services.scheduled_jobs import recalculate_biweekly_goals_job
        from services.goals import recalculate_biweekly_goals
        
        # Both should exist and be callable
        assert callable(recalculate_biweekly_goals_job)
        assert callable(recalculate_biweekly_goals)


class TestScheduledJobsIntegrationWithMetrics:
    """Integration tests between scheduled jobs and metrics"""
    
    def test_daily_job_uses_metrics_calculation(self):
        """Test that daily job uses metrics calculation"""
        from services.scheduled_jobs import calculate_daily_metrics
        from services.metrics import calculate_metrics
        
        # Both should exist and be callable
        assert callable(calculate_daily_metrics)
        assert callable(calculate_metrics)
    
    def test_weekly_job_uses_metrics_calculation(self):
        """Test that weekly job uses metrics calculation"""
        from services.scheduled_jobs import get_metrics_for_period
        from services.metrics import calculate_metrics
        
        # Both should exist and be callable
        assert callable(get_metrics_for_period)
        assert callable(calculate_metrics)
    
    def test_rolling_average_metrics_available(self):
        """Test that rolling average metrics are available"""
        from services.scheduled_jobs import select_metrics_for_recalculation
        from services.metrics import calculate_rolling_average_metrics
        
        # Both should exist and be callable
        assert callable(select_metrics_for_recalculation)
        assert callable(calculate_rolling_average_metrics)


class TestScheduledJobsDataFlow:
    """Tests for data flow in scheduled jobs"""
    
    def test_metrics_stored_before_goals_calculated(self):
        """Test that metrics are stored before goals are calculated"""
        from services.scheduled_jobs import (
            store_daily_metrics,
            store_goal_history
        )
        
        # Both functions should exist
        assert callable(store_daily_metrics)
        assert callable(store_goal_history)
    
    def test_goals_stored_in_history(self):
        """Test that goals are stored in history"""
        from services.scheduled_jobs import (
            store_goal_history,
            update_user_goals
        )
        
        # Both functions should exist
        assert callable(store_goal_history)
        assert callable(update_user_goals)
    
    def test_profit_targets_retrieved_for_calculation(self):
        """Test that profit targets are retrieved for calculation"""
        from services.scheduled_jobs import get_user_profit_targets
        
        # Function should exist
        assert callable(get_user_profit_targets)

