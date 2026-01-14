#!/usr/bin/env python3
"""
Simple tests for free intervals calculation (no Django)
"""
from datetime import datetime, time, timedelta


def make_datetime(date_obj, hour, minute=0):
    """Create datetime object without timezone"""
    return datetime.combine(date_obj, time(hour, minute))


def calculate_free_intervals_simple(approved_bookings, date_obj, open_hour=9, close_hour=22):
    """
    Calculate free intervals based on approved bookings and working hours.
    Simplified version without timezone.
    
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
        workday_start = make_datetime(date_obj, open_hour, 0)
        workday_end = make_datetime(date_obj, close_hour, 0)
        return [(workday_start, workday_end)]
    
    # Sort bookings by start time
    sorted_bookings = sorted(approved_bookings, key=lambda x: x[0])
    
    # Create workday boundaries
    workday_start = make_datetime(date_obj, open_hour, 0)
    workday_end = make_datetime(date_obj, close_hour, 0)
    
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


def merge_adjacent_intervals_simple(intervals, gap_minutes=0):
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


def format_free_intervals_simple(intervals):
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
    result = calculate_free_intervals_simple([], test_date, open_hour=9, close_hour=22)
    assert len(result) == 1
    assert result[0][0].hour == 9
    assert result[0][1].hour == 22
    print("✓ Test 1: No bookings -> whole day free")
    
    # Test 2: Single booking in middle of day
    bookings = [
        (make_datetime(test_date, 12, 0), make_datetime(test_date, 14, 0))
    ]
    result = calculate_free_intervals_simple(bookings, test_date)
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
        (make_datetime(test_date, 9, 0), make_datetime(test_date, 11, 0))
    ]
    result = calculate_free_intervals_simple(bookings, test_date)
    assert len(result) == 1  # Only after booking
    assert result[0][0].hour == 11
    assert result[0][1].hour == 22
    print("✓ Test 3: Booking at start -> free after")
    
    # Test 4: Booking at end of day
    bookings = [
        (make_datetime(test_date, 20, 0), make_datetime(test_date, 22, 0))
    ]
    result = calculate_free_intervals_simple(bookings, test_date)
    assert len(result) == 1  # Only before booking
    assert result[0][0].hour == 9
    assert result[0][1].hour == 20
    print("✓ Test 4: Booking at end -> free before")
    
    # Test 5: Multiple bookings
    bookings = [
        (make_datetime(test_date, 10, 0), make_datetime(test_date, 12, 0)),
        (make_datetime(test_date, 14, 0), make_datetime(test_date, 16, 0)),
        (make_datetime(test_date, 18, 0), make_datetime(test_date, 20, 0))
    ]
    result = calculate_free_intervals_simple(bookings, test_date)
    assert len(result) == 4  # 09:00-10:00, 12:00-14:00, 16:00-18:00, 20:00-22:00
    print("✓ Test 5: Multiple bookings -> multiple free intervals")
    
    # Test 6: Adjacent bookings (should create single gap)
    bookings = [
        (make_datetime(test_date, 10, 0), make_datetime(test_date, 12, 0)),
        (make_datetime(test_date, 12, 0), make_datetime(test_date, 14, 0))
    ]
    result = calculate_free_intervals_simple(bookings, test_date)
    assert len(result) == 2  # 09:00-10:00, 14:00-22:00
    print("✓ Test 6: Adjacent bookings -> merged occupied time")
    
    # Test 7: Overlapping bookings (should handle correctly)
    bookings = [
        (make_datetime(test_date, 10, 0), make_datetime(test_date, 13, 0)),
        (make_datetime(test_date, 12, 0), make_datetime(test_date, 14, 0))  # Overlaps with first
    ]
    result = calculate_free_intervals_simple(bookings, test_date)
    # Should have: 09:00-10:00, 14:00-22:00
    assert len(result) == 2
    assert result[0][0].hour == 9
    assert result[0][1].hour == 10
    assert result[1][0].hour == 14
    assert result[1][1].hour == 22
    print("✓ Test 7: Overlapping bookings handled correctly")
    
    print("All calculate_free_intervals tests passed!\n")


def test_merge_adjacent_intervals():
    """Test merging of adjacent intervals"""
    print("Testing merge_adjacent_intervals...")
    
    test_date = datetime(2024, 1, 1).date()
    
    # Test 1: Empty list
    result = merge_adjacent_intervals_simple([])
    assert result == []
    print("✓ Test 1: Empty list")
    
    # Test 2: Single interval
    intervals = [
        (make_datetime(test_date, 9, 0), make_datetime(test_date, 12, 0))
    ]
    result = merge_adjacent_intervals_simple(intervals)
    assert len(result) == 1
    assert result[0] == intervals[0]
    print("✓ Test 2: Single interval")
    
    # Test 3: Adjacent intervals (should merge)
    intervals = [
        (make_datetime(test_date, 9, 0), make_datetime(test_date, 12, 0)),
        (make_datetime(test_date, 12, 0), make_datetime(test_date, 15, 0))
    ]
    result = merge_adjacent_intervals_simple(intervals)
    assert len(result) == 1
    assert result[0][0].hour == 9
    assert result[0][1].hour == 15
    print("✓ Test 3: Adjacent intervals merged")
    
    # Test 4: Non-adjacent intervals (should not merge)
    intervals = [
        (make_datetime(test_date, 9, 0), make_datetime(test_date, 12, 0)),
        (make_datetime(test_date, 14, 0), make_datetime(test_date, 17, 0))
    ]
    result = merge_adjacent_intervals_simple(intervals)
    assert len(result) == 2
    print("✓ Test 4: Non-adjacent intervals not merged")
    
    # Test 5: Intervals with small gap (should merge with gap_minutes)
    intervals = [
        (make_datetime(test_date, 9, 0), make_datetime(test_date, 12, 0)),
        (make_datetime(test_date, 12, 30), make_datetime(test_date, 15, 0))
    ]
    # Without gap tolerance
    result = merge_adjacent_intervals_simple(intervals, gap_minutes=0)
    assert len(result) == 2
    # With gap tolerance
    result = merge_adjacent_intervals_simple(intervals, gap_minutes=60)
    assert len(result) == 1
    print("✓ Test 5: Intervals with gap merged with tolerance")
    
    print("All merge_adjacent_intervals tests passed!\n")


def test_format_free_intervals():
    """Test formatting of free intervals"""
    print("Testing format_free_intervals...")
    
    test_date = datetime(2024, 1, 1).date()
    
    # Test 1: Empty list
    result = format_free_intervals_simple([])
    assert result == "нет свободного времени"
    print("✓ Test 1: Empty list -> 'нет свободного времени'")
    
    # Test 2: Single interval
    intervals = [
        (make_datetime(test_date, 9, 0), make_datetime(test_date, 12, 0))
    ]
    result = format_free_intervals_simple(intervals)
    assert "09:00-12:00" in result
    print(f"✓ Test 2: Single interval -> '{result}'")
    
    # Test 3: Multiple intervals
    intervals = [
        (make_datetime(test_date, 9, 0), make_datetime(test_date, 12, 0)),
        (make_datetime(test_date, 14, 0), make_datetime(test_date, 17, 0)),
        (make_datetime(test_date, 19, 0), make_datetime(test_date, 22, 0))
    ]
    result = format_free_intervals_simple(intervals)
    assert "09:00-12:00" in result
    assert "14:00-17:00" in result
    assert "19:00-22:00" in result
    print(f"✓ Test 3: Three intervals -> '{result}'")
    
    # Test 4: Many intervals (should truncate)
    intervals = []
    for i in range(10):
        hour = 9 + i
        intervals.append((
            make_datetime(test_date, hour, 0),
            make_datetime(test_date, hour + 1, 0)
        ))
    
    result = format_free_intervals_simple(intervals)
    assert "и еще" in result
    print(f"✓ Test 4: Many intervals (truncated) -> '{result}'")
    
    print("All format_free_intervals tests passed!\n")


def test_integration_example():
    """Test complete integration example from problem statement"""
    print("Testing integration example from problem statement...")
    
    test_date = datetime(2024, 1, 1).date()
    
    # Example from problem: bookings create occupied blocks
    # Original example showed: "занято 09:00-11:00, 09:30-11:30, 10:00-12:00 и еще 20"
    # This should be converted to free intervals
    
    # Simulate many bookings throughout the day
    # Let's say bookings occupy most of the day except some windows
    bookings = []
    
    print(f"\nDebug: Created bookings:")
    
    # Morning bookings: 09:00-15:00 (occupied)
    # Create overlapping 2-hour bookings every hour from 9-14
    for hour in [9, 10, 11, 12, 13, 14]:
        booking_start = make_datetime(test_date, hour, 0)
        booking_end = make_datetime(test_date, hour + 2, 0)
        bookings.append((booking_start, booking_end))
        print(f"  {booking_start.strftime('%H:%M')}-{booking_end.strftime('%H:%M')}")
    
    # Evening bookings: 17:00-21:00 (occupied)
    # Create overlapping 2-hour bookings every hour from 17-20
    for hour in [17, 18, 19, 20]:
        booking_start = make_datetime(test_date, hour, 0)
        booking_end = make_datetime(test_date, hour + 2, 0)
        bookings.append((booking_start, booking_end))
        print(f"  {booking_start.strftime('%H:%M')}-{booking_end.strftime('%H:%M')}")
    
    # Calculate free intervals
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=23)
    
    print(f"\nDebug: Raw free intervals before merging:")
    for start, end in free_intervals:
        print(f"  {start.strftime('%H:%M')}-{end.strftime('%H:%M')}")
    
    # Merge adjacent intervals (with some gap tolerance)
    merged_intervals = merge_adjacent_intervals_simple(free_intervals, gap_minutes=30)
    
    print(f"\nDebug: Merged intervals:")
    for start, end in merged_intervals:
        print(f"  {start.strftime('%H:%M')}-{end.strftime('%H:%M')}")
    
    # Format for display
    formatted = format_free_intervals_simple(merged_intervals)
    
    print(f"\nExample scenario:")
    print(f"Bookings occupy: 09:00-16:00 and 17:00-22:00")
    print(f"Free intervals should be: 16:00-17:00 and 22:00-23:00")
    print(f"Formatted output: {formatted}")
    
    # Verify
    assert len(merged_intervals) == 2, f"Expected 2 free intervals, got {len(merged_intervals)}"
    
    # First interval: 16:00-17:00
    assert merged_intervals[0][0].hour == 16
    assert merged_intervals[0][1].hour == 17
    
    # Second interval: 22:00-23:00
    assert merged_intervals[1][0].hour == 22
    assert merged_intervals[1][1].hour == 23
    
    print("✓ Integration example test passed!")


def compare_old_vs_new():
    """Compare old and new formats"""
    print("\n" + "=" * 60)
    print("COMPARING OLD vs NEW FORMATS")
    print("=" * 60)
    
    test_date = datetime(2024, 1, 1).date()
    
    # Old format example (showing booked slots)
    print("\nOLD FORMAT (showing booked time):")
    print("  Сегодня: занято 09:00-11:00, 09:30-11:30, 10:00-12:00 и еще 20, все остальное свободно")
    
    # New format (showing free intervals)
    print("\nNEW FORMAT (showing free windows):")
    print("  Сегодня: свободно 15:00-17:00, 21:00-23:00")
    
    print("\n" + "=" * 60)
    print("NEW FORMAT IS CLEARER: Shows available time windows directly!")
    print("=" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("FREE INTERVALS CALCULATION TESTS (Simple Version)")
    print("=" * 60)
    
    # Run tests
    test_calculate_free_intervals()
    test_merge_adjacent_intervals()
    test_format_free_intervals()
    test_integration_example()
    compare_old_vs_new()
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! Ready to implement new logic.")
    print("=" * 60)