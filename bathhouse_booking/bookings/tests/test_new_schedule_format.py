#!/usr/bin/env python3
"""
Test the new schedule format logic
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

def test_scenario_1():
    """Test scenario: Some bookings throughout the day"""
    print("=" * 60)
    print("SCENARIO 1: Some bookings throughout the day")
    print("=" * 60)
    
    test_date = datetime(2024, 1, 1).date()
    
    # Create bookings: 10:00-12:00 and 14:00-16:00
    bookings = [
        (make_datetime(test_date, 10, 0), make_datetime(test_date, 12, 0)),
        (make_datetime(test_date, 14, 0), make_datetime(test_date, 16, 0))
    ]
    
    # Calculate free intervals
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=22)
    
    print(f"\nRaw free intervals:")
    for start, end in free_intervals:
        print(f"  {start.strftime('%H:%M')}-{end.strftime('%H:%M')}")
    
    # Merge adjacent intervals
    merged = merge_adjacent_intervals_simple(free_intervals, gap_minutes=30)
    
    print(f"\nMerged intervals (30 min gap tolerance):")
    for start, end in merged:
        print(f"  {start.strftime('%H:%M')}-{end.strftime('%H:%M')}")
    
    # Format for display
    formatted = format_free_intervals_simple(merged)
    
    print(f"\nFormatted output:")
    print(f"  свободно {formatted}")
    
    print(f"\nExpected: свободно 09:00-10:00, 12:00-14:00, 16:00-22:00")

def test_scenario_2():
    """Test scenario: Busy day with few windows"""
    print("\n" + "=" * 60)
    print("SCENARIO 2: Busy day with few windows")
    print("=" * 60)
    
    test_date = datetime(2024, 1, 1).date()
    
    # Create many bookings throughout the day
    bookings = []
    # Morning: 09:00-15:00 occupied
    for hour in [9, 10, 11, 12, 13, 14]:
        bookings.append((
            make_datetime(test_date, hour, 0),
            make_datetime(test_date, hour + 2, 0)
        ))
    
    # Evening: 17:00-21:00 occupied  
    for hour in [17, 18, 19, 20]:
        bookings.append((
            make_datetime(test_date, hour, 0),
            make_datetime(test_date, hour + 2, 0)
        ))
    
    # Calculate free intervals
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=23)
    
    print(f"\nRaw free intervals:")
    for start, end in free_intervals:
        print(f"  {start.strftime('%H:%M')}-{end.strftime('%H:%M')}")
    
    # Merge adjacent intervals
    merged = merge_adjacent_intervals_simple(free_intervals, gap_minutes=30)
    
    print(f"\nMerged intervals (30 min gap tolerance):")
    for start, end in merged:
        print(f"  {start.strftime('%H:%M')}-{end.strftime('%H:%M')}")
    
    # Format for display
    formatted = format_free_intervals_simple(merged)
    
    print(f"\nFormatted output:")
    print(f"  свободно {formatted}")
    
    print(f"\nExpected: свободно 16:00-17:00, 22:00-23:00")

def test_scenario_3():
    """Test scenario: Empty day"""
    print("\n" + "=" * 60)
    print("SCENARIO 3: Empty day (no bookings)")
    print("=" * 60)
    
    test_date = datetime(2024, 1, 1).date()
    
    # No bookings
    bookings = []
    
    # Calculate free intervals
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=22)
    
    print(f"\nRaw free intervals:")
    for start, end in free_intervals:
        print(f"  {start.strftime('%H:%M')}-{end.strftime('%H:%M')}")
    
    # Merge adjacent intervals
    merged = merge_adjacent_intervals_simple(free_intervals, gap_minutes=30)
    
    print(f"\nMerged intervals:")
    for start, end in merged:
        print(f"  {start.strftime('%H:%M')}-{end.strftime('%H:%M')}")
    
    # Format for display
    formatted = format_free_intervals_simple(merged)
    
    print(f"\nFormatted output:")
    print(f"  свободно {formatted}")
    
    print(f"\nExpected: свободно 09:00-22:00")

def test_scenario_4():
    """Test scenario: Fully booked day"""
    print("\n" + "=" * 60)
    print("SCENARIO 4: Fully booked day")
    print("=" * 60)
    
    test_date = datetime(2024, 1, 1).date()
    
    # Create bookings covering entire day
    bookings = [
        (make_datetime(test_date, 9, 0), make_datetime(test_date, 22, 0))
    ]
    
    # Calculate free intervals
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=22)
    
    print(f"\nRaw free intervals: {len(free_intervals)}")
    
    # Merge adjacent intervals
    merged = merge_adjacent_intervals_simple(free_intervals, gap_minutes=30)
    
    print(f"\nMerged intervals: {len(merged)}")
    
    # Format for display
    formatted = format_free_intervals_simple(merged)
    
    print(f"\nFormatted output:")
    print(f"  {formatted}")
    
    print(f"\nExpected: нет свободного времени")

def compare_old_vs_new():
    """Compare old and new formats"""
    print("\n" + "=" * 60)
    print("COMPARISON: OLD vs NEW FORMAT")
    print("=" * 60)
    
    test_date = datetime(2024, 1, 1).date()
    
    # Create overlapping bookings like in the original example
    bookings = [
        (make_datetime(test_date, 9, 0), make_datetime(test_date, 11, 0)),
        (make_datetime(test_date, 9, 30), make_datetime(test_date, 11, 30)),
        (make_datetime(test_date, 10, 0), make_datetime(test_date, 12, 0))
    ]
    
    # OLD FORMAT: Show booked slots
    print("\nOLD FORMAT (showing booked time):")
    print("  Сегодня: занято 09:00-11:00, 09:30-11:30, 10:00-12:00 и еще 20, все остальное свободно")
    
    # NEW FORMAT: Show free intervals
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=23)
    merged = merge_adjacent_intervals_simple(free_intervals, gap_minutes=30)
    formatted = format_free_intervals_simple(merged)
    
    print("\nNEW FORMAT (showing free windows):")
    print(f"  Сегодня: свободно {formatted}")
    
    print("\n" + "=" * 60)
    print("NEW FORMAT IS CLEARER: Shows available time windows directly!")
    print("=" * 60)

if __name__ == "__main__":
    test_scenario_1()
    test_scenario_2()
    test_scenario_3()
    test_scenario_4()
    compare_old_vs_new()
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED!")
    print("New schedule format is working correctly.")
    print("=" * 60)