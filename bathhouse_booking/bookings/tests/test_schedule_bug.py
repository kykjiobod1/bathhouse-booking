#!/usr/bin/env python3
"""
Test to reproduce the schedule bug
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

def test_scenario_fully_booked():
    """Test scenario: Fully booked day"""
    print("=" * 60)
    print("TEST: Fully booked day")
    print("=" * 60)
    
    test_date = datetime(2024, 1, 1).date()
    
    # Create booking covering entire day: 09:00-22:00
    bookings = [
        (make_datetime(test_date, 9, 0), make_datetime(test_date, 22, 0))
    ]
    
    # Calculate free intervals
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=22)
    
    print(f"\nFree intervals calculated: {len(free_intervals)}")
    for start, end in free_intervals:
        print(f"  {start.strftime('%H:%M')}-{end.strftime('%H:%M')}")
    
    # Format for display
    formatted = format_free_intervals_simple(free_intervals)
    
    print(f"\nFormatted output: {formatted}")
    print(f"Expected: 'нет свободного времени' (current behavior)")
    print(f"User wants: Should show free intervals even when fully booked?")
    
    return len(free_intervals) == 0

def test_scenario_partially_booked():
    """Test scenario: Partially booked day (13:00-15:00 occupied)"""
    print("\n" + "=" * 60)
    print("TEST: Partially booked day (13:00-15:00 occupied)")
    print("=" * 60)
    
    test_date = datetime(2024, 1, 1).date()
    
    # Create booking: 13:00-15:00 occupied
    bookings = [
        (make_datetime(test_date, 13, 0), make_datetime(test_date, 15, 0))
    ]
    
    # Calculate free intervals
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=22)
    
    print(f"\nFree intervals calculated: {len(free_intervals)}")
    for start, end in free_intervals:
        print(f"  {start.strftime('%H:%M')}-{end.strftime('%H:%M')}")
    
    # Format for display
    formatted = format_free_intervals_simple(free_intervals)
    
    print(f"\nFormatted output: свободно {formatted}")
    print(f"Expected: 'свободно 09:00-13:00, 15:00-22:00'")
    
    expected = "09:00-13:00, 15:00-22:00"
    actual = formatted
    return expected == actual

def test_scenario_multiple_bookings():
    """Test scenario: Multiple bookings throughout day"""
    print("\n" + "=" * 60)
    print("TEST: Multiple bookings throughout day")
    print("=" * 60)
    
    test_date = datetime(2024, 1, 1).date()
    
    # Create bookings: 10:00-12:00 and 14:00-16:00 occupied
    bookings = [
        (make_datetime(test_date, 10, 0), make_datetime(test_date, 12, 0)),
        (make_datetime(test_date, 14, 0), make_datetime(test_date, 16, 0))
    ]
    
    # Calculate free intervals
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=22)
    
    print(f"\nFree intervals calculated: {len(free_intervals)}")
    for start, end in free_intervals:
        print(f"  {start.strftime('%H:%M')}-{end.strftime('%H:%M')}")
    
    # Format for display
    formatted = format_free_intervals_simple(free_intervals)
    
    print(f"\nFormatted output: свободно {formatted}")
    print(f"Expected: 'свободно 09:00-10:00, 12:00-14:00, 16:00-22:00'")
    
    expected = "09:00-10:00, 12:00-14:00, 16:00-22:00"
    actual = formatted
    return expected == actual

def test_scenario_edge_cases():
    """Test edge cases"""
    print("\n" + "=" * 60)
    print("TEST: Edge cases")
    print("=" * 60)
    
    test_date = datetime(2024, 1, 1).date()
    
    # Test 1: Booking at start of day
    print("\n1. Booking at start of day (09:00-11:00):")
    bookings = [(make_datetime(test_date, 9, 0), make_datetime(test_date, 11, 0))]
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=22)
    formatted = format_free_intervals_simple(free_intervals)
    print(f"   Free intervals: {len(free_intervals)}")
    print(f"   Formatted: {formatted}")
    print(f"   Expected: '11:00-22:00'")
    
    # Test 2: Booking at end of day
    print("\n2. Booking at end of day (20:00-22:00):")
    bookings = [(make_datetime(test_date, 20, 0), make_datetime(test_date, 22, 0))]
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=22)
    formatted = format_free_intervals_simple(free_intervals)
    print(f"   Free intervals: {len(free_intervals)}")
    print(f"   Formatted: {formatted}")
    print(f"   Expected: '09:00-20:00'")
    
    # Test 3: Overlapping bookings
    print("\n3. Overlapping bookings (10:00-13:00 and 12:00-14:00):")
    bookings = [
        (make_datetime(test_date, 10, 0), make_datetime(test_date, 13, 0)),
        (make_datetime(test_date, 12, 0), make_datetime(test_date, 14, 0))
    ]
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=22)
    formatted = format_free_intervals_simple(free_intervals)
    print(f"   Free intervals: {len(free_intervals)}")
    print(f"   Formatted: {formatted}")
    print(f"   Expected: '09:00-10:00, 14:00-22:00'")
    
    pass

if __name__ == "__main__":
    print("Testing schedule display bug...")
    print("User says: расписание всегда выглядит так даже когда есть занятое время")
    print("Need format: 'свободно 09:00-13:00, 15:00-22:00' (если время с 13 часов до 15 занято)")
    print()
    
    test1 = test_scenario_fully_booked()
    test2 = test_scenario_partially_booked()
    test3 = test_scenario_multiple_bookings()
    test4 = test_scenario_edge_cases()
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    print(f"1. Fully booked day: {'PASS' if test1 else 'FAIL'}")
    print(f"2. Partially booked day: {'PASS' if test2 else 'FAIL'}")
    print(f"3. Multiple bookings: {'PASS' if test3 else 'FAIL'}")
    print(f"4. Edge cases: {'PASS' if test4 else 'FAIL'}")
    
    print("\n" + "=" * 60)
    print("ANALYSIS:")
    print("=" * 60)
    print("The issue seems to be:")
    print("1. When day is fully booked (09:00-22:00), free_intervals is empty")
    print("2. format_free_intervals_simple() returns 'нет свободного времени' for empty list")
    print("3. But user wants to always show free intervals format")
    print("\nPossible solution: Change format_free_intervals to return empty string or handle empty case differently")
    print("But wait... if day is fully booked, there ARE NO free intervals!")
    print("Maybe the real issue is in how we calculate free intervals?")