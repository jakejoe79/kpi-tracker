"""
Metrics calculation service for dynamic goal recalculation.
Calculates booking speed, conversion rate, and average profit per booking.
"""

from typing import Dict, Tuple, Optional


def calculate_booking_speed(total_time_minutes: float, bookings_count: int) -> float:
    """
    Calculate booking speed (minutes per booking).
    
    Formula: booking_speed = total_time_minutes / bookings_count
    
    Args:
        total_time_minutes: Total time spent in minutes
        bookings_count: Number of bookings completed
        
    Returns:
        Booking speed in minutes per booking
        
    Raises:
        ValueError: If bookings_count is 0 or negative
    """
    if bookings_count <= 0:
        raise ValueError("bookings_count must be greater than 0")
    
    return total_time_minutes / bookings_count


def calculate_conversion_rate(bookings_count: int, calls_count: int) -> float:
    """
    Calculate conversion rate as a percentage.
    
    Formula: conversion_rate = (bookings_count / calls_count) * 100
    
    Args:
        bookings_count: Number of bookings completed
        calls_count: Number of calls received
        
    Returns:
        Conversion rate as a percentage (0-100)
        
    Raises:
        ValueError: If calls_count is 0 or negative
    """
    if calls_count <= 0:
        raise ValueError("calls_count must be greater than 0")
    
    return (bookings_count / calls_count) * 100


def calculate_avg_profit_per_booking(total_profit: float, bookings_count: int) -> float:
    """
    Calculate average profit per booking.
    
    Formula: avg_profit_per_booking = total_profit / bookings_count
    
    Args:
        total_profit: Total profit in dollars
        bookings_count: Number of bookings completed
        
    Returns:
        Average profit per booking in dollars
        
    Raises:
        ValueError: If bookings_count is 0 or negative
    """
    if bookings_count <= 0:
        raise ValueError("bookings_count must be greater than 0")
    
    return total_profit / bookings_count


def calculate_metrics(
    total_time_minutes: float,
    bookings_count: int,
    calls_count: int,
    total_profit: float
) -> Dict[str, float]:
    """
    Calculate all metrics for a period.
    
    Args:
        total_time_minutes: Total time spent in minutes
        bookings_count: Number of bookings completed
        calls_count: Number of calls received
        total_profit: Total profit in dollars
        
    Returns:
        Dictionary with booking_speed, conversion_rate, and avg_profit_per_booking
        
    Raises:
        ValueError: If any count is 0 or negative
    """
    booking_speed = calculate_booking_speed(total_time_minutes, bookings_count)
    conversion_rate = calculate_conversion_rate(bookings_count, calls_count)
    avg_profit = calculate_avg_profit_per_booking(total_profit, bookings_count)
    
    return {
        "booking_speed_interval": booking_speed,
        "conversion_rate": conversion_rate,
        "avg_profit_per_booking": avg_profit,
    }


def calculate_rolling_average_metrics(
    metrics_list: list
) -> Dict[str, float]:
    """
    Calculate rolling average of metrics from multiple periods.
    
    Args:
        metrics_list: List of metric dictionaries, each containing:
                     - booking_speed_interval
                     - conversion_rate
                     - avg_profit_per_booking
        
    Returns:
        Dictionary with averaged metrics
        
    Raises:
        ValueError: If metrics_list is empty
    """
    if not metrics_list:
        raise ValueError("metrics_list cannot be empty")
    
    count = len(metrics_list)
    
    avg_booking_speed = sum(m["booking_speed_interval"] for m in metrics_list) / count
    avg_conversion_rate = sum(m["conversion_rate"] for m in metrics_list) / count
    avg_profit = sum(m["avg_profit_per_booking"] for m in metrics_list) / count
    
    return {
        "booking_speed_interval": avg_booking_speed,
        "conversion_rate": avg_conversion_rate,
        "avg_profit_per_booking": avg_profit,
    }
