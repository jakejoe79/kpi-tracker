"""
Unit tests for goal recalculation functions.
Tests daily, weekly, and biweekly goal recalculation using the formula.
"""

import pytest
from services.goals import (
    recalculate_goals,
    recalculate_daily_goals,
    recalculate_weekly_goals,
    recalculate_biweekly_goals
)


class TestRecalculateGoals:
    """Tests for the core goal recalculation function"""
    
    def test_recalculate_goals_basic(self):
        """Test basic goal recalculation with standard metrics"""
        result = recalculate_goals(
            profit_target=72.08,
            booking_speed_interval=30.0,
            conversion_rate=16.0,
            avg_profit_per_booking=2.40
        )
        
        # reservations_needed = 72.08 / 2.40 = 30.03
        assert result["reservations_needed"] == 30
        # calls_needed = 30.03 / 0.16 = 187.69
        assert result["calls_needed"] == 188
        # time_needed = 187.69 * 30 = 5631.25 (rounded calls * booking_speed)
        assert abs(result["time_needed_minutes"] - 5631.25) < 1
    
    def test_recalculate_goals_improved_booking_speed(self):
        """Test goal recalculation with improved booking speed"""
        # If booking speed improves from 30 to 15 minutes per booking
        result = recalculate_goals(
            profit_target=72.08,
            booking_speed_interval=15.0,  # 2x faster
            conversion_rate=16.0,
            avg_profit_per_booking=2.40
        )
        
        # Calls and reservations stay the same
        assert result["reservations_needed"] == 30
        assert result["calls_needed"] == 188
        # But time needed is halved (approximately)
        assert abs(result["time_needed_minutes"] - 2815.625) < 1
    
    def test_recalculate_goals_improved_conversion_rate(self):
        """Test goal recalculation with improved conversion rate"""
        # If conversion rate improves from 16% to 20%
        result = recalculate_goals(
            profit_target=72.08,
            booking_speed_interval=30.0,
            conversion_rate=20.0,  # Improved
            avg_profit_per_booking=2.40
        )
        
        # Reservations stay the same
        assert result["reservations_needed"] == 30
        # But calls needed decreases
        # calls_needed = 30 / 0.20 = 150
        assert result["calls_needed"] == 150
        # Time needed also decreases
        assert abs(result["time_needed_minutes"] - 4505.0) < 1
    
    def test_recalculate_goals_improved_profit_per_booking(self):
        """Test goal recalculation with improved profit per booking"""
        # If profit per booking improves from $2.40 to $3.00
        result = recalculate_goals(
            profit_target=72.08,
            booking_speed_interval=30.0,
            conversion_rate=16.0,
            avg_profit_per_booking=3.00  # Improved
        )
        
        # Reservations needed decreases
        # reservations_needed = 72.08 / 3.00 = 24.03
        assert result["reservations_needed"] == 24
        # Calls needed also decreases
        # calls_needed = 24 / 0.16 = 150
        assert result["calls_needed"] == 150
        # Time needed decreases
        assert abs(result["time_needed_minutes"] - 4505.0) < 1
    
    def test_recalculate_goals_zero_profit_target(self):
        """Test goal recalculation with zero profit target"""
        result = recalculate_goals(
            profit_target=0,
            booking_speed_interval=30.0,
            conversion_rate=16.0,
            avg_profit_per_booking=2.40
        )
        
        assert result["reservations_needed"] == 0
        assert result["calls_needed"] == 0
        assert result["time_needed_minutes"] == 0.0
    
    def test_recalculate_goals_invalid_booking_speed(self):
        """Test goal recalculation with invalid booking speed"""
        with pytest.raises(ValueError, match="booking_speed_interval must be greater than 0"):
            recalculate_goals(
                profit_target=72.08,
                booking_speed_interval=0,
                conversion_rate=16.0,
                avg_profit_per_booking=2.40
            )
    
    def test_recalculate_goals_invalid_conversion_rate(self):
        """Test goal recalculation with invalid conversion rate"""
        with pytest.raises(ValueError, match="conversion_rate must be greater than 0"):
            recalculate_goals(
                profit_target=72.08,
                booking_speed_interval=30.0,
                conversion_rate=0,
                avg_profit_per_booking=2.40
            )
    
    def test_recalculate_goals_invalid_profit_per_booking(self):
        """Test goal recalculation with invalid profit per booking"""
        with pytest.raises(ValueError, match="avg_profit_per_booking must be greater than 0"):
            recalculate_goals(
                profit_target=72.08,
                booking_speed_interval=30.0,
                conversion_rate=16.0,
                avg_profit_per_booking=0
            )
    
    def test_recalculate_goals_negative_profit_target(self):
        """Test goal recalculation with negative profit target"""
        with pytest.raises(ValueError, match="profit_target cannot be negative"):
            recalculate_goals(
                profit_target=-100,
                booking_speed_interval=30.0,
                conversion_rate=16.0,
                avg_profit_per_booking=2.40
            )
    
    def test_recalculate_goals_high_profit_target(self):
        """Test goal recalculation with high profit target"""
        result = recalculate_goals(
            profit_target=1000.0,
            booking_speed_interval=30.0,
            conversion_rate=16.0,
            avg_profit_per_booking=2.40
        )
        
        # reservations_needed = 1000 / 2.40 = 416.67
        assert result["reservations_needed"] == 417
        # calls_needed = 417 / 0.16 = 2606.25
        assert result["calls_needed"] in [2604, 2605, 2606]
        # time_needed = calls * 30
        assert result["time_needed_minutes"] > 78000
    
    def test_recalculate_goals_low_conversion_rate(self):
        """Test goal recalculation with low conversion rate"""
        result = recalculate_goals(
            profit_target=72.08,
            booking_speed_interval=30.0,
            conversion_rate=5.0,  # Very low
            avg_profit_per_booking=2.40
        )
        
        # Reservations stay the same
        assert result["reservations_needed"] == 30
        # But calls needed increases significantly
        # calls_needed = 30 / 0.05 = 600
        assert result["calls_needed"] in [600, 601]
        # Time needed increases
        assert result["time_needed_minutes"] > 18000


class TestRecalculateDailyGoals:
    """Tests for daily goal recalculation"""
    
    def test_recalculate_daily_goals_basic(self):
        """Test basic daily goal recalculation"""
        result = recalculate_daily_goals(
            profit_target=72.08,
            booking_speed_interval=30.0,
            conversion_rate=16.0,
            avg_profit_per_booking=2.40
        )
        
        assert result["period_type"] == "daily"
        assert result["profit_target"] == 72.08
        assert result["calls_needed"] == 188
        assert result["reservations_needed"] == 30
        assert abs(result["time_needed_minutes"] - 5631.25) < 1
        assert result["booking_speed_interval"] == 30.0
        assert result["conversion_rate"] == 16.0
        assert result["avg_profit_per_booking"] == 2.40
    
    def test_recalculate_daily_goals_includes_metrics(self):
        """Test that daily goals include all metrics"""
        result = recalculate_daily_goals(
            profit_target=100.0,
            booking_speed_interval=25.0,
            conversion_rate=20.0,
            avg_profit_per_booking=3.50
        )
        
        # Verify all fields are present
        assert "period_type" in result
        assert "profit_target" in result
        assert "calls_needed" in result
        assert "reservations_needed" in result
        assert "time_needed_minutes" in result
        assert "booking_speed_interval" in result
        assert "conversion_rate" in result
        assert "avg_profit_per_booking" in result


class TestRecalculateWeeklyGoals:
    """Tests for weekly goal recalculation"""
    
    def test_recalculate_weekly_goals_basic(self):
        """Test basic weekly goal recalculation"""
        result = recalculate_weekly_goals(
            profit_target=504.56,  # 7x daily
            booking_speed_interval=30.0,
            conversion_rate=16.0,
            avg_profit_per_booking=2.40
        )
        
        assert result["period_type"] == "weekly"
        assert result["profit_target"] == 504.56
        # Should be approximately 7x the daily goals
        assert result["calls_needed"] > 1000
        assert result["reservations_needed"] > 200
    
    def test_recalculate_weekly_goals_includes_metrics(self):
        """Test that weekly goals include all metrics"""
        result = recalculate_weekly_goals(
            profit_target=500.0,
            booking_speed_interval=30.0,
            conversion_rate=16.0,
            avg_profit_per_booking=2.40
        )
        
        # Verify all fields are present
        assert "period_type" in result
        assert "profit_target" in result
        assert "calls_needed" in result
        assert "reservations_needed" in result
        assert "time_needed_minutes" in result
        assert "booking_speed_interval" in result
        assert "conversion_rate" in result
        assert "avg_profit_per_booking" in result


class TestRecalculateBiweeklyGoals:
    """Tests for biweekly goal recalculation"""
    
    def test_recalculate_biweekly_goals_basic(self):
        """Test basic biweekly goal recalculation"""
        result = recalculate_biweekly_goals(
            profit_target=1009.12,  # 14x daily
            booking_speed_interval=30.0,
            conversion_rate=16.0,
            avg_profit_per_booking=2.40
        )
        
        assert result["period_type"] == "biweekly"
        assert result["profit_target"] == 1009.12
        # Should be approximately 14x the daily goals
        assert result["calls_needed"] > 2000
        assert result["reservations_needed"] > 400
    
    def test_recalculate_biweekly_goals_includes_metrics(self):
        """Test that biweekly goals include all metrics"""
        result = recalculate_biweekly_goals(
            profit_target=1000.0,
            booking_speed_interval=30.0,
            conversion_rate=16.0,
            avg_profit_per_booking=2.40
        )
        
        # Verify all fields are present
        assert "period_type" in result
        assert "profit_target" in result
        assert "calls_needed" in result
        assert "reservations_needed" in result
        assert "time_needed_minutes" in result
        assert "booking_speed_interval" in result
        assert "conversion_rate" in result
        assert "avg_profit_per_booking" in result


class TestGoalFormula:
    """Tests to verify the goal calculation formula is correct"""
    
    def test_formula_accuracy_daily(self):
        """Test that daily goal formula is accurate"""
        profit_target = 72.08
        booking_speed = 30.0
        conversion_rate = 16.0
        avg_profit = 2.40
        
        result = recalculate_daily_goals(
            profit_target=profit_target,
            booking_speed_interval=booking_speed,
            conversion_rate=conversion_rate,
            avg_profit_per_booking=avg_profit
        )
        
        # Manually calculate expected values
        expected_reservations = profit_target / avg_profit
        expected_calls = expected_reservations / (conversion_rate / 100)
        expected_time = expected_calls * booking_speed
        
        assert abs(result["reservations_needed"] - round(expected_reservations)) < 1
        assert abs(result["calls_needed"] - round(expected_calls)) < 1
        assert abs(result["time_needed_minutes"] - expected_time) < 1
    
    def test_formula_preserves_profit_target(self):
        """Test that profit target is preserved in recalculation"""
        profit_target = 150.0
        
        result = recalculate_daily_goals(
            profit_target=profit_target,
            booking_speed_interval=25.0,
            conversion_rate=18.0,
            avg_profit_per_booking=3.50
        )
        
        # Profit target should be exactly preserved
        assert result["profit_target"] == profit_target
    
    def test_formula_with_different_metrics(self):
        """Test formula with various metric combinations"""
        test_cases = [
            (100.0, 20.0, 15.0, 2.50),
            (50.0, 40.0, 10.0, 1.50),
            (200.0, 15.0, 25.0, 4.00),
            (75.0, 35.0, 12.0, 2.25),
        ]
        
        for profit_target, booking_speed, conversion_rate, avg_profit in test_cases:
            result = recalculate_daily_goals(
                profit_target=profit_target,
                booking_speed_interval=booking_speed,
                conversion_rate=conversion_rate,
                avg_profit_per_booking=avg_profit
            )
            
            # Verify all values are positive
            assert result["calls_needed"] > 0
            assert result["reservations_needed"] > 0
            assert result["time_needed_minutes"] > 0
            
            # Verify profit target is preserved
            assert result["profit_target"] == profit_target
