"""
Property-based tests for dynamic goal recalculation.
Tests correctness properties using hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, assume
from services.goals import recalculate_goals, recalculate_daily_goals, recalculate_weekly_goals, recalculate_biweekly_goals
from services.metrics import calculate_metrics, calculate_booking_speed, calculate_conversion_rate, calculate_avg_profit_per_booking


# Strategies for generating test data
positive_float = st.floats(min_value=0.01, max_value=10000.0)
positive_int = st.integers(min_value=1, max_value=10000)
conversion_rate = st.floats(min_value=0.1, max_value=100.0)


class TestPropertyGoalCalculationAccuracy:
    """Property 1: Goal calculation accuracy
    
    **Validates: Requirements 2.5, 2.6**
    
    For any profit target P, conversion rate C, and average profit per booking A:
    - reservations_needed = P / A
    - calls_needed = reservations_needed / (C / 100)
    - The calculated goals SHALL match the formula exactly
    """
    
    @given(
        profit_target=positive_float,
        booking_speed=positive_float,
        conv_rate=conversion_rate,
        avg_profit=positive_float
    )
    def test_goal_formula_accuracy(self, profit_target, booking_speed, conv_rate, avg_profit):
        """Test that goal calculation formula is accurate"""
        result = recalculate_goals(
            profit_target=profit_target,
            booking_speed_interval=booking_speed,
            conversion_rate=conv_rate,
            avg_profit_per_booking=avg_profit
        )
        
        # Calculate expected values
        expected_reservations = profit_target / avg_profit
        expected_calls = expected_reservations / (conv_rate / 100)
        expected_time = expected_calls * booking_speed
        
        # Verify calculations match formula
        assert abs(result["reservations_needed"] - round(expected_reservations)) <= 1
        assert abs(result["calls_needed"] - round(expected_calls)) <= 1
        assert abs(result["time_needed_minutes"] - expected_time) <= 1


class TestPropertyMetricCalculationAccuracy:
    """Property 2: Metric calculation accuracy
    
    **Validates: Requirements 2.1, 2.2**
    
    For any day's data:
    - booking_speed = total_time / bookings
    - conversion_rate = (bookings / calls) * 100
    - avg_profit = total_profit / bookings
    - The calculated metrics SHALL match the formula exactly
    """
    
    @given(
        total_time=positive_float,
        bookings=positive_int,
        calls=positive_int,
        total_profit=positive_float
    )
    def test_metric_formula_accuracy(self, total_time, bookings, calls, total_profit):
        """Test that metric calculation formula is accurate"""
        result = calculate_metrics(
            total_time_minutes=total_time,
            bookings_count=bookings,
            calls_count=calls,
            total_profit=total_profit
        )
        
        # Calculate expected values
        expected_booking_speed = total_time / bookings
        expected_conversion_rate = (bookings / calls) * 100
        expected_avg_profit = total_profit / bookings
        
        # Verify calculations match formula
        assert abs(result["booking_speed_interval"] - expected_booking_speed) < 0.01
        assert abs(result["conversion_rate"] - expected_conversion_rate) < 0.01
        assert abs(result["avg_profit_per_booking"] - expected_avg_profit) < 0.01


class TestPropertyProfitTargetPreservation:
    """Property 5: Profit target preservation
    
    **Validates: Requirements 2.7, 3.2**
    
    When goals are recalculated:
    - The profit target SHALL remain unchanged
    - Only intermediate goals (calls, reservations) SHALL adjust
    - The profit target SHALL be the source of truth
    """
    
    @given(
        profit_target=positive_float,
        booking_speed=positive_float,
        conv_rate=conversion_rate,
        avg_profit=positive_float
    )
    def test_profit_target_preserved_daily(self, profit_target, booking_speed, conv_rate, avg_profit):
        """Test that profit target is preserved in daily goals"""
        result = recalculate_daily_goals(
            profit_target=profit_target,
            booking_speed_interval=booking_speed,
            conversion_rate=conv_rate,
            avg_profit_per_booking=avg_profit
        )
        
        # Profit target must be exactly preserved
        assert result["profit_target"] == profit_target
    
    @given(
        profit_target=positive_float,
        booking_speed=positive_float,
        conv_rate=conversion_rate,
        avg_profit=positive_float
    )
    def test_profit_target_preserved_weekly(self, profit_target, booking_speed, conv_rate, avg_profit):
        """Test that profit target is preserved in weekly goals"""
        result = recalculate_weekly_goals(
            profit_target=profit_target,
            booking_speed_interval=booking_speed,
            conversion_rate=conv_rate,
            avg_profit_per_booking=avg_profit
        )
        
        # Profit target must be exactly preserved
        assert result["profit_target"] == profit_target
    
    @given(
        profit_target=positive_float,
        booking_speed=positive_float,
        conv_rate=conversion_rate,
        avg_profit=positive_float
    )
    def test_profit_target_preserved_biweekly(self, profit_target, booking_speed, conv_rate, avg_profit):
        """Test that profit target is preserved in biweekly goals"""
        result = recalculate_biweekly_goals(
            profit_target=profit_target,
            booking_speed_interval=booking_speed,
            conversion_rate=conv_rate,
            avg_profit_per_booking=avg_profit
        )
        
        # Profit target must be exactly preserved
        assert result["profit_target"] == profit_target


class TestPropertyGoalScaling:
    """Property: Goals scale proportionally with metrics
    
    **Validates: Requirements 2.6**
    
    When metrics improve:
    - Booking speed improvement should reduce time needed
    - Conversion rate improvement should reduce calls needed
    - Profit per booking improvement should reduce reservations needed
    """
    
    @given(
        profit_target=positive_float,
        booking_speed=positive_float,
        conv_rate=conversion_rate,
        avg_profit=positive_float
    )
    def test_booking_speed_improvement_reduces_time(self, profit_target, booking_speed, conv_rate, avg_profit):
        """Test that booking speed improvement reduces time needed"""
        # Calculate goals with original booking speed
        original_goals = recalculate_goals(
            profit_target=profit_target,
            booking_speed_interval=booking_speed,
            conversion_rate=conv_rate,
            avg_profit_per_booking=avg_profit
        )
        
        # Calculate goals with improved booking speed (50% faster)
        improved_booking_speed = booking_speed * 0.5
        improved_goals = recalculate_goals(
            profit_target=profit_target,
            booking_speed_interval=improved_booking_speed,
            conversion_rate=conv_rate,
            avg_profit_per_booking=avg_profit
        )
        
        # Time needed should be reduced
        assert improved_goals["time_needed_minutes"] < original_goals["time_needed_minutes"]
        # Calls and reservations should stay the same
        assert improved_goals["calls_needed"] == original_goals["calls_needed"]
        assert improved_goals["reservations_needed"] == original_goals["reservations_needed"]
    
    @given(
        profit_target=positive_float,
        booking_speed=positive_float,
        conv_rate=conversion_rate,
        avg_profit=positive_float
    )
    def test_conversion_rate_improvement_reduces_calls(self, profit_target, booking_speed, conv_rate, avg_profit):
        """Test that conversion rate improvement reduces calls needed"""
        # Ensure conversion rate is less than 50 (so improvement is meaningful)
        assume(conv_rate < 50)
        
        # Calculate goals with original conversion rate
        original_goals = recalculate_goals(
            profit_target=profit_target,
            booking_speed_interval=booking_speed,
            conversion_rate=conv_rate,
            avg_profit_per_booking=avg_profit
        )
        
        # Calculate goals with improved conversion rate (2x better)
        improved_conv_rate = min(conv_rate * 2, 99.9)  # Cap at 99.9%
        improved_goals = recalculate_goals(
            profit_target=profit_target,
            booking_speed_interval=booking_speed,
            conversion_rate=improved_conv_rate,
            avg_profit_per_booking=avg_profit
        )
        
        # Calls needed should be reduced or equal (due to rounding)
        assert improved_goals["calls_needed"] <= original_goals["calls_needed"]
        # Reservations should stay the same
        assert improved_goals["reservations_needed"] == original_goals["reservations_needed"]
    
    @given(
        profit_target=positive_float,
        booking_speed=positive_float,
        conv_rate=conversion_rate,
        avg_profit=positive_float
    )
    def test_profit_improvement_reduces_reservations(self, profit_target, booking_speed, conv_rate, avg_profit):
        """Test that profit per booking improvement reduces reservations needed"""
        # Calculate goals with original profit per booking
        original_goals = recalculate_goals(
            profit_target=profit_target,
            booking_speed_interval=booking_speed,
            conversion_rate=conv_rate,
            avg_profit_per_booking=avg_profit
        )
        
        # Calculate goals with improved profit per booking (50% better)
        improved_avg_profit = avg_profit * 1.5
        improved_goals = recalculate_goals(
            profit_target=profit_target,
            booking_speed_interval=booking_speed,
            conversion_rate=conv_rate,
            avg_profit_per_booking=improved_avg_profit
        )
        
        # Reservations needed should be reduced or equal (due to rounding)
        assert improved_goals["reservations_needed"] <= original_goals["reservations_needed"]


class TestPropertyGoalMonotonicity:
    """Property: Goals increase monotonically with profit target
    
    **Validates: Requirements 2.5**
    
    For any fixed metrics, increasing profit target should increase goals
    """
    
    @given(
        profit_target_1=positive_float,
        profit_target_2=positive_float,
        booking_speed=positive_float,
        conv_rate=conversion_rate,
        avg_profit=positive_float
    )
    def test_goals_increase_with_profit_target(self, profit_target_1, profit_target_2, booking_speed, conv_rate, avg_profit):
        """Test that goals increase with profit target"""
        # Ensure profit_target_1 < profit_target_2
        if profit_target_1 >= profit_target_2:
            profit_target_1, profit_target_2 = profit_target_2, profit_target_1
        
        # Calculate goals for both targets
        goals_1 = recalculate_goals(
            profit_target=profit_target_1,
            booking_speed_interval=booking_speed,
            conversion_rate=conv_rate,
            avg_profit_per_booking=avg_profit
        )
        
        goals_2 = recalculate_goals(
            profit_target=profit_target_2,
            booking_speed_interval=booking_speed,
            conversion_rate=conv_rate,
            avg_profit_per_booking=avg_profit
        )
        
        # Goals should increase with profit target
        assert goals_2["calls_needed"] >= goals_1["calls_needed"]
        assert goals_2["reservations_needed"] >= goals_1["reservations_needed"]
        assert goals_2["time_needed_minutes"] >= goals_1["time_needed_minutes"]


class TestPropertyMetricBoundaries:
    """Property: Metrics stay within valid bounds
    
    **Validates: Requirements 2.1, 2.2**
    
    Calculated metrics should always be non-negative and reasonable
    """
    
    @given(
        total_time=positive_float,
        bookings=positive_int,
        calls=positive_int,
        total_profit=positive_float
    )
    def test_metrics_non_negative(self, total_time, bookings, calls, total_profit):
        """Test that all metrics are non-negative"""
        result = calculate_metrics(
            total_time_minutes=total_time,
            bookings_count=bookings,
            calls_count=calls,
            total_profit=total_profit
        )
        
        # All metrics should be non-negative
        assert result["booking_speed_interval"] >= 0
        assert result["conversion_rate"] >= 0
        assert result["avg_profit_per_booking"] >= 0
    
    @given(
        total_time=positive_float,
        bookings=positive_int,
        calls=positive_int,
        total_profit=positive_float
    )
    def test_conversion_rate_bounded(self, total_time, bookings, calls, total_profit):
        """Test that conversion rate is bounded between 0 and 100"""
        # Ensure bookings <= calls (realistic scenario)
        assume(bookings <= calls)
        
        result = calculate_metrics(
            total_time_minutes=total_time,
            bookings_count=bookings,
            calls_count=calls,
            total_profit=total_profit
        )
        
        # Conversion rate should be between 0 and 100
        assert 0 <= result["conversion_rate"] <= 100


class TestPropertyGoalConsistency:
    """Property: Goals are consistent across period types
    
    **Validates: Requirements 2.5, 2.6, 2.7**
    
    Goals calculated with same metrics should be consistent
    """
    
    @given(
        profit_target=positive_float,
        booking_speed=positive_float,
        conv_rate=conversion_rate,
        avg_profit=positive_float
    )
    def test_goals_consistent_across_periods(self, profit_target, booking_speed, conv_rate, avg_profit):
        """Test that goals are consistent across period types"""
        metrics = {
            "booking_speed_interval": booking_speed,
            "conversion_rate": conv_rate,
            "avg_profit_per_booking": avg_profit
        }
        
        # Calculate goals for all period types
        daily_goals = recalculate_daily_goals(profit_target=profit_target, **metrics)
        weekly_goals = recalculate_weekly_goals(profit_target=profit_target * 7, **metrics)
        biweekly_goals = recalculate_biweekly_goals(profit_target=profit_target * 14, **metrics)
        
        # All should have the same metrics
        assert daily_goals["booking_speed_interval"] == weekly_goals["booking_speed_interval"]
        assert daily_goals["conversion_rate"] == weekly_goals["conversion_rate"]
        assert daily_goals["avg_profit_per_booking"] == weekly_goals["avg_profit_per_booking"]
        
        # Goals should scale with profit targets
        assert weekly_goals["calls_needed"] >= daily_goals["calls_needed"]
        assert biweekly_goals["calls_needed"] >= weekly_goals["calls_needed"]
