"""
Unit tests for metrics calculation functions.
Tests booking speed, conversion rate, and average profit per booking calculations.
"""

import pytest
from services.metrics import (
    calculate_booking_speed,
    calculate_conversion_rate,
    calculate_avg_profit_per_booking,
    calculate_metrics,
    calculate_rolling_average_metrics
)


class TestBookingSpeed:
    """Tests for booking speed calculation"""
    
    def test_calculate_booking_speed_basic(self):
        """Test basic booking speed calculation"""
        # 480 minutes / 16 bookings = 30 minutes per booking
        result = calculate_booking_speed(480, 16)
        assert result == 30.0
    
    def test_calculate_booking_speed_fractional(self):
        """Test booking speed with fractional result"""
        # 100 minutes / 3 bookings = 33.33... minutes per booking
        result = calculate_booking_speed(100, 3)
        assert abs(result - 33.333333) < 0.001
    
    def test_calculate_booking_speed_zero_bookings(self):
        """Test booking speed with zero bookings raises error"""
        with pytest.raises(ValueError, match="bookings_count must be greater than 0"):
            calculate_booking_speed(480, 0)
    
    def test_calculate_booking_speed_negative_bookings(self):
        """Test booking speed with negative bookings raises error"""
        with pytest.raises(ValueError, match="bookings_count must be greater than 0"):
            calculate_booking_speed(480, -5)
    
    def test_calculate_booking_speed_zero_time(self):
        """Test booking speed with zero time"""
        result = calculate_booking_speed(0, 10)
        assert result == 0.0
    
    def test_calculate_booking_speed_one_booking(self):
        """Test booking speed with one booking"""
        result = calculate_booking_speed(45, 1)
        assert result == 45.0


class TestConversionRate:
    """Tests for conversion rate calculation"""
    
    def test_calculate_conversion_rate_basic(self):
        """Test basic conversion rate calculation"""
        # 16 bookings / 100 calls = 16%
        result = calculate_conversion_rate(16, 100)
        assert result == 16.0
    
    def test_calculate_conversion_rate_perfect(self):
        """Test conversion rate with 100% conversion"""
        result = calculate_conversion_rate(50, 50)
        assert result == 100.0
    
    def test_calculate_conversion_rate_low(self):
        """Test conversion rate with low conversion"""
        # 1 booking / 100 calls = 1%
        result = calculate_conversion_rate(1, 100)
        assert result == 1.0
    
    def test_calculate_conversion_rate_zero_calls(self):
        """Test conversion rate with zero calls raises error"""
        with pytest.raises(ValueError, match="calls_count must be greater than 0"):
            calculate_conversion_rate(10, 0)
    
    def test_calculate_conversion_rate_negative_calls(self):
        """Test conversion rate with negative calls raises error"""
        with pytest.raises(ValueError, match="calls_count must be greater than 0"):
            calculate_conversion_rate(10, -5)
    
    def test_calculate_conversion_rate_zero_bookings(self):
        """Test conversion rate with zero bookings"""
        result = calculate_conversion_rate(0, 100)
        assert result == 0.0
    
    def test_calculate_conversion_rate_fractional(self):
        """Test conversion rate with fractional result"""
        # 1 booking / 3 calls = 33.33...%
        result = calculate_conversion_rate(1, 3)
        assert abs(result - 33.333333) < 0.001


class TestAvgProfitPerBooking:
    """Tests for average profit per booking calculation"""
    
    def test_calculate_avg_profit_basic(self):
        """Test basic average profit calculation"""
        # $38.40 / 16 bookings = $2.40 per booking
        result = calculate_avg_profit_per_booking(38.40, 16)
        assert abs(result - 2.40) < 0.01
    
    def test_calculate_avg_profit_zero_bookings(self):
        """Test average profit with zero bookings raises error"""
        with pytest.raises(ValueError, match="bookings_count must be greater than 0"):
            calculate_avg_profit_per_booking(100, 0)
    
    def test_calculate_avg_profit_negative_bookings(self):
        """Test average profit with negative bookings raises error"""
        with pytest.raises(ValueError, match="bookings_count must be greater than 0"):
            calculate_avg_profit_per_booking(100, -5)
    
    def test_calculate_avg_profit_zero_profit(self):
        """Test average profit with zero profit"""
        result = calculate_avg_profit_per_booking(0, 10)
        assert result == 0.0
    
    def test_calculate_avg_profit_negative_profit(self):
        """Test average profit with negative profit (loss)"""
        result = calculate_avg_profit_per_booking(-50, 10)
        assert result == -5.0
    
    def test_calculate_avg_profit_one_booking(self):
        """Test average profit with one booking"""
        result = calculate_avg_profit_per_booking(100, 1)
        assert result == 100.0


class TestCalculateMetrics:
    """Tests for combined metrics calculation"""
    
    def test_calculate_metrics_basic(self):
        """Test basic metrics calculation"""
        result = calculate_metrics(
            total_time_minutes=480,
            bookings_count=16,
            calls_count=100,
            total_profit=38.40
        )
        
        assert result["booking_speed_interval"] == 30.0
        assert result["conversion_rate"] == 16.0
        assert abs(result["avg_profit_per_booking"] - 2.40) < 0.01
    
    def test_calculate_metrics_zero_bookings(self):
        """Test metrics calculation with zero bookings raises error"""
        with pytest.raises(ValueError):
            calculate_metrics(
                total_time_minutes=480,
                bookings_count=0,
                calls_count=100,
                total_profit=38.40
            )
    
    def test_calculate_metrics_zero_calls(self):
        """Test metrics calculation with zero calls raises error"""
        with pytest.raises(ValueError):
            calculate_metrics(
                total_time_minutes=480,
                bookings_count=16,
                calls_count=0,
                total_profit=38.40
            )
    
    def test_calculate_metrics_all_zeros(self):
        """Test metrics calculation with all zeros raises error"""
        with pytest.raises(ValueError):
            calculate_metrics(
                total_time_minutes=0,
                bookings_count=0,
                calls_count=0,
                total_profit=0
            )


class TestRollingAverageMetrics:
    """Tests for rolling average metrics calculation"""
    
    def test_calculate_rolling_average_single_metric(self):
        """Test rolling average with single metric"""
        metrics_list = [
            {
                "booking_speed_interval": 30.0,
                "conversion_rate": 16.0,
                "avg_profit_per_booking": 2.40
            }
        ]
        
        result = calculate_rolling_average_metrics(metrics_list)
        
        assert result["booking_speed_interval"] == 30.0
        assert result["conversion_rate"] == 16.0
        assert result["avg_profit_per_booking"] == 2.40
    
    def test_calculate_rolling_average_multiple_metrics(self):
        """Test rolling average with multiple metrics"""
        metrics_list = [
            {
                "booking_speed_interval": 30.0,
                "conversion_rate": 16.0,
                "avg_profit_per_booking": 2.40
            },
            {
                "booking_speed_interval": 25.0,
                "conversion_rate": 20.0,
                "avg_profit_per_booking": 2.50
            },
            {
                "booking_speed_interval": 35.0,
                "conversion_rate": 14.0,
                "avg_profit_per_booking": 2.30
            }
        ]
        
        result = calculate_rolling_average_metrics(metrics_list)
        
        # Average booking speed: (30 + 25 + 35) / 3 = 30
        assert result["booking_speed_interval"] == 30.0
        # Average conversion rate: (16 + 20 + 14) / 3 = 16.67
        assert abs(result["conversion_rate"] - 16.666667) < 0.001
        # Average profit: (2.40 + 2.50 + 2.30) / 3 = 2.40
        assert abs(result["avg_profit_per_booking"] - 2.40) < 0.01
    
    def test_calculate_rolling_average_empty_list(self):
        """Test rolling average with empty list raises error"""
        with pytest.raises(ValueError, match="metrics_list cannot be empty"):
            calculate_rolling_average_metrics([])
    
    def test_calculate_rolling_average_14_days(self):
        """Test rolling average with 14 days of data"""
        metrics_list = [
            {
                "booking_speed_interval": 30.0 + i,
                "conversion_rate": 15.0 + i,
                "avg_profit_per_booking": 2.40 + (i * 0.01)
            }
            for i in range(14)
        ]
        
        result = calculate_rolling_average_metrics(metrics_list)
        
        # Average booking speed: (30 + 31 + ... + 43) / 14 = 36.5
        assert abs(result["booking_speed_interval"] - 36.5) < 0.01
        # Average conversion rate: (15 + 16 + ... + 28) / 14 = 21.5
        assert abs(result["conversion_rate"] - 21.5) < 0.01
        # Average profit: (2.40 + 2.41 + ... + 2.53) / 14 ≈ 2.465
        assert abs(result["avg_profit_per_booking"] - 2.465) < 0.01


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""
    
    def test_very_small_values(self):
        """Test with very small values"""
        result = calculate_metrics(
            total_time_minutes=0.1,
            bookings_count=1,
            calls_count=1,
            total_profit=0.01
        )
        
        assert result["booking_speed_interval"] == 0.1
        assert result["conversion_rate"] == 100.0
        assert result["avg_profit_per_booking"] == 0.01
    
    def test_very_large_values(self):
        """Test with very large values"""
        result = calculate_metrics(
            total_time_minutes=1000000,
            bookings_count=10000,
            calls_count=100000,
            total_profit=1000000
        )
        
        assert result["booking_speed_interval"] == 100.0
        assert result["conversion_rate"] == 10.0
        assert result["avg_profit_per_booking"] == 100.0
    
    def test_floating_point_precision(self):
        """Test floating point precision"""
        result = calculate_metrics(
            total_time_minutes=100.123,
            bookings_count=3,
            calls_count=7,
            total_profit=7.777
        )
        
        # Verify calculations are precise
        assert abs(result["booking_speed_interval"] - (100.123 / 3)) < 0.0001
        assert abs(result["conversion_rate"] - (3 / 7 * 100)) < 0.0001
        assert abs(result["avg_profit_per_booking"] - (7.777 / 3)) < 0.0001
