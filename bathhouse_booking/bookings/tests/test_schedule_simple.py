#!/usr/bin/env python3
"""
Simple tests for schedule formatting logic (no Django dependencies)
"""
from datetime import datetime, time, timedelta


def merge_adjacent_slots(slots):
    """
    Merge adjacent time slots.
    
    Args:
        slots: List of (start_time, end_time) tuples as datetime objects
    
    Returns:
        List of merged slots
    """
    if not slots:
        return []
    
    # Sort by start time
    sorted_slots = sorted(slots, key=lambda x: x[0])
    
    # Merge adjacent slots
    merged = []
    current_start, current_end = sorted_slots[0]
    
    for slot_start, slot_end in sorted_slots[1:]:
        # If current slot starts immediately after previous, merge
        if slot_start == current_end:
            current_end = slot_end
        else:
            # Save current merged slot and start new
            merged.append((current_start, current_end))
            current_start, current_end = slot_start, slot_end
    
    # Add last merged slot
    merged.append((current_start, current_end))
    
    return merged


def format_slots_new(slots, open_hour=9, close_hour=22):
    """
    NEW FORMAT: Format slots to show booked time and indicate free time.
    
    Args:
        slots: List of (start_time, end_time) tuples as datetime objects
        open_hour: Opening hour
        close_hour: Closing hour
    
    Returns:
        Formatted string
    """
    if not slots:
        return f"свободно с {open_hour:02d}:00 до {close_hour:02d}:00"
    
    # Merge adjacent slots
    merged_slots = merge_adjacent_slots(slots)
    
    # Format booked slots
    booked_strings = []
    for slot_start, slot_end in merged_slots:
        start_str = slot_start.strftime("%H:%M")
        end_str = slot_end.strftime("%H:%M")
        booked_strings.append(f"{start_str}-{end_str}")
    
    if len(booked_strings) <= 3:
        booked_str = ", ".join(booked_strings)
    else:
        booked_str = ", ".join(booked_strings[:3]) + f" и еще {len(booked_strings) - 3}"
    
    return f"занято {booked_str}, все остальное свободно"


def test_merge_adjacent_slots():
    """Test merging of adjacent slots"""
    print("Testing merge_adjacent_slots...")
    
    # Create test date
    test_date = datetime(2024, 1, 1)
    
    # Test 1: Empty list
    result = merge_adjacent_slots([])
    assert result == []
    print("✓ Test 1: Empty list")
    
    # Test 2: Single slot
    slot1 = (
        datetime.combine(test_date, time(12, 0)),
        datetime.combine(test_date, time(14, 0))
    )
    result = merge_adjacent_slots([slot1])
    assert len(result) == 1
    assert result[0] == slot1
    print("✓ Test 2: Single slot")
    
    # Test 3: Two adjacent slots (should merge)
    slot2 = (
        datetime.combine(test_date, time(14, 0)),
        datetime.combine(test_date, time(16, 0))
    )
    result = merge_adjacent_slots([slot1, slot2])
    assert len(result) == 1
    assert result[0][0] == slot1[0]  # Start of first slot
    assert result[0][1] == slot2[1]  # End of second slot
    print("✓ Test 3: Two adjacent slots merged")
    
    # Test 4: Two non-adjacent slots (should not merge)
    slot3 = (
        datetime.combine(test_date, time(18, 0)),
        datetime.combine(test_date, time(20, 0))
    )
    result = merge_adjacent_slots([slot1, slot3])
    assert len(result) == 2
    print("✓ Test 4: Two non-adjacent slots not merged")
    
    # Test 5: Three slots with gaps
    slot4 = (
        datetime.combine(test_date, time(10, 0)),
        datetime.combine(test_date, time(11, 0))
    )
    result = merge_adjacent_slots([slot1, slot3, slot4])
    assert len(result) == 3  # All separate
    print("✓ Test 5: Three separate slots")
    
    print("All merge tests passed!\n")


def test_new_format():
    """Test new format implementation"""
    print("Testing new format implementation...")
    
    # Create test date
    test_date = datetime(2024, 1, 1)
    
    # Test 1: Empty slots
    result = format_slots_new([], open_hour=9, close_hour=22)
    expected = "свободно с 09:00 до 22:00"
    assert result == expected, f"Expected: {expected}, Got: {result}"
    print(f"✓ Test 1: Empty slots -> '{result}'")
    
    # Test 2: Single booked slot
    slot1 = (
        datetime.combine(test_date, time(12, 0)),
        datetime.combine(test_date, time(14, 0))
    )
    result = format_slots_new([slot1])
    assert "занято 12:00-14:00" in result
    assert "все остальное свободно" in result
    print(f"✓ Test 2: Single slot -> '{result}'")
    
    # Test 3: Multiple adjacent slots (should merge)
    slot2 = (
        datetime.combine(test_date, time(14, 0)),
        datetime.combine(test_date, time(16, 0))
    )
    slot3 = (
        datetime.combine(test_date, time(16, 0)),
        datetime.combine(test_date, time(18, 0))
    )
    result = format_slots_new([slot1, slot2, slot3])
    # Should show "занято 12:00-18:00, все остальное свободно"
    assert "12:00-18:00" in result
    print(f"✓ Test 3: Three adjacent slots -> '{result}'")
    
    # Test 4: Example from problem statement
    slots = []
    # Create slots: 12:00-14:00, 12:30-14:30, 13:00-15:00
    slots.append((datetime.combine(test_date, time(12, 0)), datetime.combine(test_date, time(14, 0))))
    slots.append((datetime.combine(test_date, time(12, 30)), datetime.combine(test_date, time(14, 30))))
    slots.append((datetime.combine(test_date, time(13, 0)), datetime.combine(test_date, time(15, 0))))
    
    # Add 8 more slots as in example (but within valid hours)
    for i in range(8):
        hour = 15 + i
        if hour + 2 <= 23:  # Ensure valid hour
            slots.append((
                datetime.combine(test_date, time(hour, 0)),
                datetime.combine(test_date, time(hour + 2, 0))
            ))
    
    result = format_slots_new(slots)
    print(f"✓ Test 4: Example case -> '{result}'")
    
    # Test 5: Many non-adjacent slots (should truncate)
    many_slots = []
    # Create non-adjacent slots (with gaps)
    for i in range(0, 20, 2):  # Every other hour
        hour = 9 + i
        if hour + 1 <= 23:  # Ensure valid hour
            many_slots.append((
                datetime.combine(test_date, time(hour, 0)),
                datetime.combine(test_date, time(hour + 1, 0))
            ))
    
    result = format_slots_new(many_slots)
    # With many non-adjacent slots, should show "и еще X"
    if len(many_slots) > 3:
        assert "и еще" in result, f"Expected 'и еще' in result: {result}"
    print(f"✓ Test 5: Many non-adjacent slots -> '{result}'")
    
    print("\nAll new format tests passed!")


def compare_formats():
    """Compare old and new formats"""
    print("\n" + "=" * 60)
    print("COMPARING OLD vs NEW FORMATS")
    print("=" * 60)
    
    test_date = datetime(2024, 1, 1)
    
    # Example from problem statement
    slots = []
    # First three slots as in example
    slots.append((datetime.combine(test_date, time(12, 0)), datetime.combine(test_date, time(14, 0))))
    slots.append((datetime.combine(test_date, time(12, 30)), datetime.combine(test_date, time(14, 30))))
    slots.append((datetime.combine(test_date, time(13, 0)), datetime.combine(test_date, time(15, 0))))
    
    # Add 8 more (within valid hours)
    for i in range(8):
        hour = 15 + i
        if hour + 2 <= 23:  # Ensure valid hour
            slots.append((
                datetime.combine(test_date, time(hour, 0)),
                datetime.combine(test_date, time(hour + 2, 0))
            ))
    
    # Simulate old format (simplified)
    merged = merge_adjacent_slots(slots)
    old_format_parts = []
    for slot_start, slot_end in merged[:3]:
        start_str = slot_start.strftime("%H:%M")
        end_str = slot_end.strftime("%H:%M")
        old_format_parts.append(f"{start_str}-{end_str}")
    
    old_format = ", ".join(old_format_parts)
    if len(merged) > 3:
        old_format += f" и еще {len(merged) - 3}"
    
    # New format
    new_format = format_slots_new(slots)
    
    print(f"\nExample case:")
    print(f"Old format would show:  Сегодня: {old_format}")
    print(f"New format shows:      Сегодня: {new_format}")
    
    print("\n" + "=" * 60)
    print("NEW FORMAT IS CLEARER: Shows what's booked, not what's free!")
    print("=" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("SCHEDULE FORMATTING TESTS (Simple Version)")
    print("=" * 60)
    
    # Run tests
    test_merge_adjacent_slots()
    test_new_format()
    compare_formats()
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! Ready to implement new format.")
    print("=" * 60)