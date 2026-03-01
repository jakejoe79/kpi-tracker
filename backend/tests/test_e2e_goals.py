"""
End-to-end tests for dynamic goal recalculation workflow.
Tests the full workflow from setting profit targets to goal recalculation.
"""

import pytest
from services.goals import recalculate_daily_goals, recalculate_weekly_goals, recalculate_biweekly_goals
from services.metrics import calculate_metrics, calculate_rolling_average_metrics


class TestE2EGoalRecalculationWorkflow:
    """End-to-end tests for goal recalculation workflow"""
    
    def test_e2e_user_sets_profit_target_and_goals_calculated(self):
        """Test full workflow: user sets profit target, goals are calculated"""
        # Step 1: User sets profit target
        profit_target = 72.08
        
        # Step 2: System has baseline metrics (first 14 days)
        booking_speed = 30.0  # minutes per booking
        conversion_rate = 16.0  # percentage
        avg_profit = 2.40  # dollars per booking
        
        # Step 3: System recalculates daily goals
        daily_goals = recalculate_daily_goals(
            profit_target=profit_target,
            booking_speed_interval=booking_speed,
            conversion_rate=conversion_rate,
            avg_profit_per_booking=avg_profit
        )
        
        # Verify goals are calculated correctly
        assert daily_goals["period_type"] == "daily"
        assert daily_goals["profit_target"] == profit_target
        assert daily_goals["calls_needed"] > 0
        assert daily_goals["reservations_needed"] > 0
        assert daily_goals["time_needed_minutes"] > 0
    
    def test_e2e_user_works_day_metrics_calculated_goals_updated(self):
        """Test workflow: user works, metrics calculated, goals updated"""
        # Step 1: User works for a day
        total_time_minutes = 480  # 8 hours
        bookings_count = 16
        calls_count = 100
        total_profit = 38.40
        
        # Step 2: System calculates daily metrics
        metrics = calculate_metrics(
            total_time_minutes=total_time_minutes,
            bookings_count=bookings_count,
            calls_count=calls_count,
            total_profit=total_profit
        )
        
        # Verify metrics are calculated
        assert metrics["booking_speed_interval"] == 30.0
        assert metrics["conversion_rate"] == 16.0
        assert abs(metrics["avg_profit_per_booking"] - 2.40) < 0.01
        
        # Step 3: System recalculates goals with new metrics
        profit_target = 72.08
        daily_goals = recalculate_daily_goals(
            profit_target=profit_target,
            booking_speed_interval=metrics["booking_speed_interval"],
            conversion_rate=metrics["conversion_rate"],
            avg_profit_per_booking=metrics["avg_profit_per_booking"]
        )
        
        # Verify goals are updated
        assert daily_goals["calls_needed"] > 0
        assert daily_goals["reservations_needed"] > 0
    
    def test_e2e_improved_performance_reduces_goals(self):
        """Test workflow: user improves performance, goals are reduced"""
        # Step 1: Initial metrics (baseline)
        initial_booking_speed = 30.0
        initial_conversion_rate = 16.0
        initial_avg_profit = 2.40
        
        # Step 2: Calculate initial goals
        profit_target = 72.08
        initial_goals = recalculate_daily_goals(
            profit_target=profit_target,
            booking_speed_interval=initial_booking_speed,
            conversion_rate=initial_conversion_rate,
            avg_profit_per_booking=initial_avg_profit
        )
        
        # Step 3: User improves performance (2x faster booking speed)
        improved_booking_speed = 15.0  # 2x faster
        
        # Step 4: Calculate improved goals
        improved_goals = recalculate_daily_goals(
            profit_target=profit_target,
            booking_speed_interval=improved_booking_speed,
            conversion_rate=initial_conversion_rate,
            avg_profit_per_booking=initial_avg_profit
        )
        
        # Verify time needed is reduced
        assert improved_goals["time_needed_minutes"] < initial_goals["time_needed_minutes"]
        # Calls and reservations should stay the same
        assert improved_goals["calls_needed"] == initial_goals["calls_needed"]
        assert improved_goals["reservations_needed"] == initial_goals["reservations_needed"]
    
    def test_e2e_14_days_data_triggers_rolling_average(self):
        """Test workflow: after 14 days, rolling average is used"""
        # Step 1: Generate 14 days of metrics
        metrics_list = []
        for i in range(14):
            metrics_list.append({
                "booking_speed_interval": 30.0 + i,  # Gradually improving
                "conversion_rate": 15.0 + i,
                "avg_profit_per_booking": 2.40 + (i * 0.01)
            })
        
        # Step 2: Calculate rolling average
        rolling_avg = calculate_rolling_average_metrics(metrics_list)
        
        # Verify rolling average is calculated
        assert rolling_avg["booking_speed_interval"] > 0
        assert rolling_avg["conversion_rate"] > 0
        assert rolling_avg["avg_profit_per_booking"] > 0
        
        # Step 3: Use rolling average for goal recalculation
        profit_target = 72.08
        goals = recalculate_daily_goals(
            profit_target=profit_target,
            booking_speed_interval=rolling_avg["booking_speed_interval"],
            conversion_rate=rolling_avg["conversion_rate"],
            avg_profit_per_booking=rolling_avg["avg_profit_per_booking"]
        )
        
        # Verify goals are calculated with rolling average
        assert goals["calls_needed"] > 0
        assert goals["reservations_needed"] > 0
    
    def test_e2e_weekly_goals_calculated_from_daily_metrics(self):
        """Test workflow: weekly goals calculated from daily metrics"""
        # Step 1: Collect 7 days of metrics
        daily_metrics = []
        for day in range(7):
            daily_metrics.append({
                "booking_speed_interval": 30.0,
                "conversion_rate": 16.0,
                "avg_profit_per_booking": 2.40
            })
        
        # Step 2: Calculate weekly rolling average
        weekly_avg = calculate_rolling_average_metrics(daily_metrics)
        
        # Step 3: Calculate weekly goals
        weekly_profit_target = 504.56  # 7x daily
        weekly_goals = recalculate_weekly_goals(
            profit_target=weekly_profit_target,
            booking_speed_interval=weekly_avg["booking_speed_interval"],
            conversion_rate=weekly_avg["conversion_rate"],
            avg_profit_per_booking=weekly_avg["avg_profit_per_booking"]
        )
        
        # Verify weekly goals are calculated
        assert weekly_goals["period_type"] == "weekly"
        assert weekly_goals["profit_target"] == weekly_profit_target
        assert weekly_goals["calls_needed"] > 0
    
    def test_e2e_biweekly_goals_calculated_from_daily_metrics(self):
        """Test workflow: biweekly goals calculated from daily metrics"""
        # Step 1: Collect 14 days of metrics
        daily_metrics = []
        for day in range(14):
            daily_metrics.append({
                "booking_speed_interval": 30.0,
                "conversion_rate": 16.0,
                "avg_profit_per_booking": 2.40
            })
        
        # Step 2: Calculate biweekly rolling average
        biweekly_avg = calculate_rolling_average_metrics(daily_metrics)
        
        # Step 3: Calculate biweekly goals
        biweekly_profit_target = 1009.12  # 14x daily
        biweekly_goals = recalculate_biweekly_goals(
            profit_target=biweekly_profit_target,
            booking_speed_interval=biweekly_avg["booking_speed_interval"],
            conversion_rate=biweekly_avg["conversion_rate"],
            avg_profit_per_booking=biweekly_avg["avg_profit_per_booking"]
        )
        
        # Verify biweekly goals are calculated
        assert biweekly_goals["period_type"] == "biweekly"
        assert biweekly_goals["profit_target"] == biweekly_profit_target
        assert biweekly_goals["calls_needed"] > 0
    
    def test_e2e_profit_target_preserved_through_recalculation(self):
        """Test workflow: profit target is preserved through recalculation"""
        profit_target = 100.0
        
        # Recalculate with different metrics
        goals1 = recalculate_daily_goals(
            profit_target=profit_target,
            booking_speed_interval=30.0,
            conversion_rate=16.0,
            avg_profit_per_booking=2.40
        )
        
        goals2 = recalculate_daily_goals(
            profit_target=profit_target,
            booking_speed_interval=25.0,
            conversion_rate=18.0,
            avg_profit_per_booking=3.00
        )
        
        # Profit target should be preserved
        assert goals1["profit_target"] == profit_target
        assert goals2["profit_target"] == profit_target
    
    def test_e2e_goals_scale_with_profit_target(self):
        """Test workflow: goals scale proportionally with profit target"""
        booking_speed = 30.0
        conversion_rate = 16.0
        avg_profit = 2.40
        
        # Calculate goals for $100 target
        goals_100 = recalculate_daily_goals(
            profit_target=100.0,
            booking_speed_interval=booking_speed,
            conversion_rate=conversion_rate,
            avg_profit_per_booking=avg_profit
        )
        
        # Calculate goals for $200 target (2x)
        goals_200 = recalculate_daily_goals(
            profit_target=200.0,
            booking_speed_interval=booking_speed,
            conversion_rate=conversion_rate,
            avg_profit_per_booking=avg_profit
        )
        
        # Goals should scale proportionally
        assert goals_200["calls_needed"] > goals_100["calls_needed"]
        assert goals_200["reservations_needed"] > goals_100["reservations_needed"]
        assert goals_200["time_needed_minutes"] > goals_100["time_needed_minutes"]
    
    def test_e2e_multiple_period_types_calculated_independently(self):
        """Test workflow: daily, weekly, biweekly goals calculated independently"""
        metrics = {
            "booking_speed_interval": 30.0,
            "conversion_rate": 16.0,
            "avg_profit_per_booking": 2.40
        }
        
        # Calculate goals for all period types
        daily_goals = recalculate_daily_goals(
            profit_target=72.08,
            **metrics
        )
        
        weekly_goals = recalculate_weekly_goals(
            profit_target=504.56,
            **metrics
        )
        
        biweekly_goals = recalculate_biweekly_goals(
            profit_target=1009.12,
            **metrics
        )
        
        # Verify all period types are calculated
        assert daily_goals["period_type"] == "daily"
        assert weekly_goals["period_type"] == "weekly"
        assert biweekly_goals["period_type"] == "biweekly"
        
        # Verify goals scale with profit targets
        assert weekly_goals["calls_needed"] > daily_goals["calls_needed"]
        assert biweekly_goals["calls_needed"] > weekly_goals["calls_needed"]
