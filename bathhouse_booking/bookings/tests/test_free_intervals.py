#!/usr/bin/env python3
"""
Tests for free intervals calculation
"""
from datetime import datetime, time, timedelta
from django.utils import timezone
import sys
import os

# Mock Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bathhouse_booking.config.settings')

def calculate_free_intervals(approved_bookings, date_obj, open_hour=9, close_hour=22):
    """
    Calculate free intervals based on approved bookings and working hours.
    
    Args:
        approved_bookings: List of (start_datetime, end_datetime) tuples for approved bookings
        date_obj: Date object
        open_hour: Opening hour
        close_hour: Closing hour
    
    Returns:
        List of (start_datetime, end_datetime) tuples for free intervals
    """
    if not approved_bookings:
        # Whole day is free
        workday_start = timezone.make_aware(datetime.combine(date_obj, datetime.min.time().replace(hour=open_hour, minute=0)))
        workday_end = timezone.make_aware(datetime.combine(date_obj, datetime.min.time().replace(hour=close_hour, minute=0)))
        return [(workday_start, workday_end)]
    
    # Sort bookings by start time
    sorted_bookings = sorted(approved_bookings, key=lambda x: x[0])
    
    # Create workday boundaries
    workday_start = timezone.make_aware(datetime.combine(date_obj, datetime.min.time().replace(hour=open_hour, minute=0)))
    workday_end = timezone.make_aware(datetime.combine(date_obj, datetime.min.time().replace(hour=close_hour, minute=0)))
    
    free_intervals = []
    current_start = workday_start
    
    for booking_start, booking_end in sorted_bookings:
        # If there's a gap before this booking, it's free
        if current_start < booking_start:
            free_intervals.append((current_start, booking_start))
        
        # Move current_start to the end of this booking
        current_start = max(current_start, booking_end)
    
    # Check for free time after last booking
    if current_start < workday_end:
        free_intervals.append((current_start, workday_end))
    
    # Filter out zero-length intervals
    free_intervals = [(start, end) for start, end in free_intervals if start < end]
    
    return free_intervals


def merge_adjacent_intervals(intervals, gap_minutes=0):
    """
    Merge adjacent or nearly adjacent intervals.
    
    Args:
        intervals: List of (start, end) tuples
        gap_minutes: Maximum gap to consider intervals as adjacent
    
    Returns:
        List of merged intervals
    """
    if not intervals:
        return []
    
    # Sort by start time
    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    
    merged = []
    current_start, current_end = sorted_intervals[0]
    
    for interval_start, interval_end in sorted_intervals[1:]:
        # If intervals are adjacent or have small gap, merge them
        if interval_start <= current_end + timedelta(minutes=gap_minutes):
            current_end = max(current_end, interval_end)
        else:
            merged.append((current_start, current_end))
            current_start, current_end = interval_start, interval_end
    
    merged.append((current_start, current_end))
    return merged


def format_free_intervals(intervals):
    """
    Format free intervals for display.
    
    Args:
        intervals: List of (start_datetime, end_datetime) tuples
    
    Returns:
        Formatted string
    """
    if not intervals:
        return "нет свободного времени"
    
    # Format intervals
    interval_strings = []
    for interval_start, interval_end in intervals:
        start_str = interval_start.strftime("%H:%M")
        end_str = interval_end.strftime("%H:%M")
        interval_strings.append(f"{start_str}-{end_str}")
    
    if len(interval_strings) <= 3:
        return ", ".join(interval_strings)
    else:
        return ", ".join(interval_strings[:3]) + f" и еще {len(interval_strings) - 3}"


def test_calculate_free_intervals():
    """Test free intervals calculation"""
    print("Testing calculate_free_intervals...")
    
    # Create test date
    test_date = datetime(2024, 1, 1).date()
    
    # Test 1: No bookings (whole day free)
    result = calculate_free_intervals([], test_date, open_hour=9, close_hour=22)
    assert len(result) == 1
    assert result[0][0].hour == 9
    assert result[0][1].hour == 22
    print("✓ Test 1: No bookings -> whole day free")
    
    # Test 2: Single booking in middle of day
    bookings = [
        (
            timezone.make_aware(datetime.combine(test_date, time(12, 0))),
            timezone.make_aware(datetime.combine(test_date, time(14, 0)))
        )
    ]
    result = calculate_free_intervals(bookings, test_date)
    assert len(result) == 2  # Before and after booking
    # Check first interval: 09:00-12:00
    assert result[0][0].hour == 9
    assert result[0][1].hour == 12
    # Check second interval: 14:00-22:00
    assert result[1][0].hour == 14
    assert result[1][1].hour == 22
    print("✓ Test 2: Single booking -> two free intervals")
    
    # Test 3: Booking at start of day
    bookings = [
        (
            timezone.make_aware(datetime.combine(test_date, time(9, 0))),
            timezone.make_aware(datetime.combine(test_date, time(11, 0)))
        )
    ]
    result = calculate_free_intervals(bookings, test_date)
    assert len(result) == 1  # Only after booking
    assert result[0][0].hour == 11
    assert result[0][1].hour == 22
    print("✓ Test 3: Booking at start -> free after")
    
    # Test 4: Booking at end of day
    bookings = [
        (
            timezone.make_aware(datetime.combine(test_date, time(20, 0))),
            timezone.make_aware(datetime.combine(test_date, time(22, 0)))
        )
    ]
    result = calculate_free_intervals(bookings, test_date)
    assert len(result) == 1  # Only before booking
    assert result[0][0].hour == 9
    assert result[0][1].hour == 20
    print("✓ Test 4: Booking at end -> free before")
    
    # Test 5: Multiple bookings
    bookings = [
        (
            timezone.make_aware(datetime.combine(test_date, time(10, 0))),
            timezone.make_aware(datetime.combine(test_date, time(12, 0)))
        ),
        (
            timezone.make_aware(datetime.combine(test_date, time(14, 0))),
            timezone.make_aware(datetime.combine(test_date, time(16, 0)))
        ),
        (
            timezone.make_aware(datetime.combine(test_date, time(18, 0))),
            timezone.make_aware(datetime.combine(test_date, time(20, 0)))
        )
    ]
    result = calculate_free_intervals(bookings, test_date)
    assert len(result) == 4  # 09:00-10:00, 12:00-14:00, 16:00-18:00, 20:00-22:00
    print("✓ Test 5: Multiple bookings -> multiple free intervals")
    
    # Test 6: Adjacent bookings (should create single gap)
    bookings = [
        (
            timezone.make_aware(datetime.combine(test_date, time(10, 0))),
            timezone.make_aware(datetime.combine(test_date, time(12, 0)))
        ),
        (
            timezone.make_aware(datetime.combine(test_date, time(12, 0))),
            timezone.make_aware(datetime.combine(test_date, time(14, 0)))
        )
    ]
    result = calculate_free_intervals(bookings, test_date)
    assert len(result) == 2  # 09:00-10:00, 14:00-22:00
    print("✓ Test 6: Adjacent bookings -> merged occupied time")
    
    print("All calculate_free_intervals tests passed!\n")


def test_merge_adjacent_intervals():
    """Test merging of adjacent intervals"""
    print("Testing merge_adjacent_intervals...")
    
    test_date = datetime(2024, 1, 1).date()
    
    # Test 1: Empty list
    result = merge_adjacent_intervals([])
    assert result == []
    print("✓ Test 1: Empty list")
    
    # Test 2: Single interval
    intervals = [
        (
            timezone.make_aware(datetime.combine(test_date, time(9, 0))),
            timezone.make_aware(datetime.combine(test_date, time(12, 0)))
        )
    ]
    result = merge_adjacent_intervals(intervals)
    assert len(result) == 1
    assert result[0] == intervals[0]
    print("✓ Test 2: Single interval")
    
    # Test 3: Adjacent intervals (should merge)
    intervals = [
        (
            timezone.make_aware(datetime.combine(test_date, time(9, 0))),
            timezone.make_aware(datetime.combine(test_date, time(12, 0)))
        ),
        (
            timezone.make_aware(datetime.combine(test_date, time(12, 0))),
            timezone.make_aware(datetime.combine(test_date, time(15, 0)))
        )
    ]
    result = merge_adjacent_intervals(intervals)
    assert len(result) == 1
    assert result[0][0].hour == 9
    assert result[0][1].hour == 15
    print("✓ Test 3: Adjacent intervals merged")
    
    # Test 4: Non-adjacent intervals (should not merge)
    intervals = [
        (
            timezone.make_aware(datetime.combine(test_date, time(9, 0))),
            timezone.make_aware(datetime.combine(test_date, time(12, 0)))
        ),
        (
            timezone.make_aware(datetime.combine(test_date, time(14, 0))),
            timezone.make_aware(datetime.combine(test_date, time(17, 0)))
        )
    ]
    result = merge_adjacent_intervals(intervals)
    assert len(result) == 2
    print("✓ Test 4: Non-adjacent intervals not merged")
    
    # Test 5: Intervals with small gap (should merge with gap_minutes)
    intervals = [
        (
            timezone.make_aware(datetime.combine(test_date, time(9, 0))),
            timezone.make_aware(datetime.combine(test_date, time(12, 0)))
        ),
        (
            timezone.make_aware(datetime.combine(test_date, time(12, 30))),
            timezone.make_aware(datetime.combine(test_date, time(15, 0)))
        )
    ]
    # Without gap tolerance
    result = merge_adjacent_intervals(intervals, gap_minutes=0)
    assert len(result) == 2
    # With gap tolerance
    result = merge_adjacent_intervals(intervals, gap_minutes=60)
    assert len(result) == 1
    print("✓ Test 5: Intervals with gap merged with tolerance")
    
    print("All merge_adjacent_intervals tests passed!\n")


def test_format_free_intervals():
    """Test formatting of free intervals"""
    print("Testing format_free_intervals...")
    
    test_date = datetime(2024, 1, 1).date()
    
    # Test 1: Empty list
    result = format_free_intervals([])
    assert result == "нет свободного времени"
    print("✓ Test 1: Empty list -> 'нет свободного времени'")
    
    # Test 2: Single interval
    intervals = [
        (
            timezone.make_aware(datetime.combine(test_date, time(9, 0))),
            timezone.make_aware(datetime.combine(test_date, time(12, 0)))
        )
    ]
    result = format_free_intervals(intervals)
    assert "09:00-12:00" in result
    print(f"✓ Test 2: Single interval -> '{result}'")
    
    # Test 3: Multiple intervals
    intervals = [
        (
            timezone.make_aware(datetime.combine(test_date, time(9, 0))),
            timezone.make_aware(datetime.combine(test_date, time(12, 0)))
        ),
        (
            timezone.make_aware(datetime.combine(test_date, time(14, 0))),
            timezone.make_aware(datetime.combine(test_date, time(17, 0)))
        ),
        (
            timezone.make_aware(datetime.combine(test_date, time(19, 0))),
            timezone.make_aware(datetime.combine(test_date, time(22, 0)))
        )
    ]
    result = format_free_intervals(intervals)
    assert "09:00-12:00" in result
    assert "14:00-17:00" in result
    assert "19:00-22:00" in result
    print(f"✓ Test 3: Three intervals -> '{result}'")
    
    # Test 4: Many intervals (should truncate)
    intervals = []
    for i in range(10):
        hour = 9 + i
        intervals.append((
            timezone.make_aware(datetime.combine(test_date, time(hour, 0))),
            timezone.make_aware(datetime.combine(test_date, time(hour + 1, 0)))
        ))
    
    result = format_free_intervals(intervals)
    assert "и еще" in result
    print(f"✓ Test 4: Many intervals (truncated) -> '{result}'")
    
    print("All format_free_intervals tests passed!\n")


def test_integration():
    """Test complete integration example"""
    print("Testing integration example...")
    
    test_date = datetime(2024, 1, 1).date()
    
    # Example from problem: bookings at 09:00-11:00, 09:30-11:30, 10:00-12:00
    # These should create one occupied block: 09:00-12:00
    bookings = [
        (
            timezone.make_aware(datetime.combine(test_date, time(9, 0))),
            timezone.make_aware(datetime.combine(test_date, time(11, 0)))
        ),
        (
            timezone.make_aware(datetime.combine(test_date, time(9, 30))),
            timezone.make_aware(datetime.combine(test_date, time(11, 30)))
        ),
        (
            timezone.make_aware(datetime.combine(test_date, time(10, 0))),
            timezone.make_aware(datetime.combine(test_date, time(12, 0)))
        )
    ]
    
    # Calculate free intervals
    free_intervals = calculate_free_intervals(bookings, test_date, open_hour=9, close_hour=23)
    
    # Should have: 12:00-23:00 (after all bookings)
    assert len(free_intervals) == 1
    assert free_intervals[0][0].hour == 12
    assert free_intervals[0][1].hour == 23
    
    # Format for display
    formatted = format_free_intervals(free_intervals)
    
    print(f"Example: Bookings at 09:00-11:00, 09:30-11:30, 10:00-12:00")
    print(f"Free intervals: {formatted}")
    print("✓ Integration test passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("FREE INTERVALS CALCULATION TESTS")
    print("=" * 60)
    
    # Setup timezone
    import django
    django.setup()
    
    # Run tests
    test_calculate_free_intervals()
    test_merge_adjacent_intervals()
    test_format_free_intervals()
    test_integration()
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! Ready to implement new logic.")
    print("=" * 60)