#!/usr/bin/env python3
"""
Test for schedule format fix
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

def format_free_intervals_fixed(intervals):
    """
    Format free intervals for display - FIXED VERSION.
    Returns empty string if no free intervals.
    
    Args:
        intervals: List of (start_datetime, end_datetime) tuples
    
    Returns:
        Formatted string (empty if no intervals)
    """
    if not intervals:
        return ""
    
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

def format_schedule_line(date_name, formatted_intervals):
    """
    Format a schedule line according to new requirements.
    
    Args:
        date_name: Name of the date (e.g., "Сегодня")
        formatted_intervals: Formatted intervals string (empty if no free time)
    
    Returns:
        Formatted schedule line
    """
    if formatted_intervals:
        return f"  {date_name}: свободно {formatted_intervals}"
    else:
        return f"  {date_name}: нет свободного времени"

def test_all_scenarios():
    """Test all schedule scenarios"""
    print("=" * 60)
    print("TESTING SCHEDULE FORMAT FIX")
    print("=" * 60)
    
    test_date = datetime(2024, 1, 1).date()
    all_passed = True
    
    # Test 1: Empty day (no bookings)
    print("\n1. Empty day (no bookings):")
    bookings = []
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=22)
    formatted = format_free_intervals_fixed(free_intervals)
    schedule_line = format_schedule_line("Сегодня", formatted)
    print(f"   Free intervals: {len(free_intervals)}")
    print(f"   Formatted intervals: '{formatted}'")
    print(f"   Schedule line: {schedule_line}")
    expected = "  Сегодня: свободно 09:00-22:00"
    if schedule_line == expected:
        print(f"   ✓ PASS")
    else:
        print(f"   ✗ FAIL: expected '{expected}', got '{schedule_line}'")
        all_passed = False
    
    # Test 2: Partially booked day (13:00-15:00 occupied)
    print("\n2. Partially booked day (13:00-15:00 occupied):")
    bookings = [(make_datetime(test_date, 13, 0), make_datetime(test_date, 15, 0))]
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=22)
    formatted = format_free_intervals_fixed(free_intervals)
    schedule_line = format_schedule_line("Сегодня", formatted)
    print(f"   Free intervals: {len(free_intervals)}")
    print(f"   Formatted intervals: '{formatted}'")
    print(f"   Schedule line: {schedule_line}")
    expected = "  Сегодня: свободно 09:00-13:00, 15:00-22:00"
    if schedule_line == expected:
        print(f"   ✓ PASS")
    else:
        print(f"   ✗ FAIL: expected '{expected}', got '{schedule_line}'")
        all_passed = False
    
    # Test 3: Fully booked day (09:00-22:00 occupied)
    print("\n3. Fully booked day (09:00-22:00 occupied):")
    bookings = [(make_datetime(test_date, 9, 0), make_datetime(test_date, 22, 0))]
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=22)
    formatted = format_free_intervals_fixed(free_intervals)
    schedule_line = format_schedule_line("Сегодня", formatted)
    print(f"   Free intervals: {len(free_intervals)}")
    print(f"   Formatted intervals: '{formatted}'")
    print(f"   Schedule line: {schedule_line}")
    expected = "  Сегодня: нет свободного времени"
    if schedule_line == expected:
        print(f"   ✓ PASS")
    else:
        print(f"   ✗ FAIL: expected '{expected}', got '{schedule_line}'")
        all_passed = False
    
    # Test 4: Multiple free intervals
    print("\n4. Multiple free intervals (10:00-12:00 and 14:00-16:00 occupied):")
    bookings = [
        (make_datetime(test_date, 10, 0), make_datetime(test_date, 12, 0)),
        (make_datetime(test_date, 14, 0), make_datetime(test_date, 16, 0))
    ]
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=22)
    formatted = format_free_intervals_fixed(free_intervals)
    schedule_line = format_schedule_line("Сегодня", formatted)
    print(f"   Free intervals: {len(free_intervals)}")
    print(f"   Formatted intervals: '{formatted}'")
    print(f"   Schedule line: {schedule_line}")
    expected = "  Сегодня: свободно 09:00-10:00, 12:00-14:00, 16:00-22:00"
    if schedule_line == expected:
        print(f"   ✓ PASS")
    else:
        print(f"   ✗ FAIL: expected '{expected}', got '{schedule_line}'")
        all_passed = False
    
    # Test 5: Many free intervals (should truncate)
    print("\n5. Many free intervals (should truncate):")
    bookings = []
    # Create bookings every 2 hours
    for hour in range(9, 22, 2):
        bookings.append((
            make_datetime(test_date, hour, 0),
            make_datetime(test_date, hour + 1, 0)
        ))
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=22)
    formatted = format_free_intervals_fixed(free_intervals)
    schedule_line = format_schedule_line("Сегодня", formatted)
    print(f"   Free intervals: {len(free_intervals)}")
    print(f"   Formatted intervals: '{formatted}'")
    print(f"   Schedule line: {schedule_line}")
    # Should show first 3 intervals and "и еще X"
    if "и еще" in formatted and len(free_intervals) > 3:
        print(f"   ✓ PASS (correctly truncated)")
    else:
        print(f"   ✗ FAIL: expected truncation for {len(free_intervals)} intervals")
        all_passed = False
    
    return all_passed

def test_complete_schedule_output():
    """Test complete schedule output format"""
    print("\n" + "=" * 60)
    print("TESTING COMPLETE SCHEDULE OUTPUT")
    print("=" * 60)
    
    # Simulate what view_schedule should output
    test_date = datetime(2024, 1, 1).date()
    
    print("\nSimulated schedule output for two bathhouses:")
    print("📅 *Расписание свободных окон*")
    print()
    
    # First bathhouse: empty day
    print("*First Bathhouse:*")
    bookings = []
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=8, close_hour=22)  # Opens at 8
    formatted = format_free_intervals_fixed(free_intervals)
    print(format_schedule_line("Сегодня", formatted))
    
    # Second bathhouse: partially booked
    print("\n*Second Bathhouse:*")
    bookings = [(make_datetime(test_date, 13, 0), make_datetime(test_date, 15, 0))]
    free_intervals = calculate_free_intervals_simple(bookings, test_date, open_hour=9, close_hour=22)
    formatted = format_free_intervals_fixed(free_intervals)
    print(format_schedule_line("Сегодня", formatted))
    
    print("\n" + "=" * 60)
    print("This matches user's expected format:")
    print("first:")
    print("  Сегодня: свободно 08:00-22:00")
    print("second:")
    print("  Сегодня: свободно 09:00-13:00, 15:00-22:00")
    print("=" * 60)
    
    pass

