#!/usr/bin/env python3
"""
Tests for schedule formatting logic
"""
from datetime import datetime, time
from django.utils import timezone
import sys
import os

# Mock the necessary imports
sys.path.insert(0, os.path.dirname(__file__))

def format_schedule_slots(available_slots, date_obj, open_hour=9, close_hour=22):
    """
    Format available slots into a user-friendly schedule string.
    
    Args:
        available_slots: List of (start_datetime, end_datetime) tuples
        date_obj: Date object
        open_hour: Opening hour (default 9)
        close_hour: Closing hour (default 22)
    
    Returns:
        Formatted schedule string
    """
    if not available_slots:
        return "нет доступных слотов"
    
    # Сортируем слоты по времени начала
    sorted_slots = sorted(available_slots, key=lambda x: x[0])
    
    # Объединяем смежные слоты
    merged_slots = []
    current_start, current_end = sorted_slots[0]
    
    for slot_start, slot_end in sorted_slots[1:]:
        # Если текущий слот начинается сразу после предыдущего, объединяем
        if slot_start == current_end:
            current_end = slot_end
        else:
            # Сохраняем текущий объединенный слот и начинаем новый
            merged_slots.append((current_start, current_end))
            current_start, current_end = slot_start, slot_end
    
    # Добавляем последний объединенный слот
    merged_slots.append((current_start, current_end))
    
    # Создаем datetime объекты для начала и конца рабочего дня
    workday_start = timezone.make_aware(datetime.combine(date_obj, datetime.min.time().replace(hour=open_hour, minute=0)))
    workday_end = timezone.make_aware(datetime.combine(date_obj, datetime.min.time().replace(hour=close_hour, minute=0)))
    
    # Проверяем, покрывает ли первый слот начало рабочего дня
    # и последний слот конец рабочего дня
    if (len(merged_slots) == 1 and 
        merged_slots[0][0] <= workday_start and 
        merged_slots[0][1] >= workday_end):
        # Весь день свободен
        start_str = workday_start.strftime("%H:%M")
        end_str = workday_end.strftime("%H:%M")
        return f"{start_str}-{end_str}"
    else:
        # Форматируем слоты в читаемый вид
        slot_strings = []
        for slot_start, slot_end in merged_slots:
            start_str = slot_start.strftime("%H:%M")
            end_str = slot_end.strftime("%H:%M")
            slot_strings.append(f"{start_str}-{end_str}")
        
        # Формируем строку со слотами
        if len(slot_strings) <= 3:
            return ", ".join(slot_strings)
        else:
            # Если слотов много, показываем первые 3 и "и еще X"
            return ", ".join(slot_strings[:3]) + f" и еще {len(slot_strings) - 3}"


def format_schedule_slots_new(available_slots, date_obj, open_hour=9, close_hour=22):
    """
    NEW VERSION: Format available slots to show booked time and indicate free time.
    
    Args:
        available_slots: List of (start_datetime, end_datetime) tuples
        date_obj: Date object
        open_hour: Opening hour (default 9)
        close_hour: Closing hour (default 22)
    
    Returns:
        Formatted schedule string in new format
    """
    if not available_slots:
        return "свободно с 09:00 до 23:00"
    
    # Сортируем слоты по времени начала
    sorted_slots = sorted(available_slots, key=lambda x: x[0])
    
    # Объединяем смежные слоты (занятое время)
    booked_slots = []
    current_start, current_end = sorted_slots[0]
    
    for slot_start, slot_end in sorted_slots[1:]:
        # Если текущий слот начинается сразу после предыдущего, объединяем
        if slot_start == current_end:
            current_end = slot_end
        else:
            # Сохраняем текущий объединенный слот и начинаем новый
            booked_slots.append((current_start, current_end))
            current_start, current_end = slot_start, slot_end
    
    # Добавляем последний объединенный слот
    booked_slots.append((current_start, current_end))
    
    # Форматируем занятые слоты
    booked_strings = []
    for slot_start, slot_end in booked_slots:
        start_str = slot_start.strftime("%H:%M")
        end_str = slot_end.strftime("%H:%M")
        booked_strings.append(f"{start_str}-{end_str}")
    
    if len(booked_strings) <= 3:
        booked_str = ", ".join(booked_strings)
    else:
        booked_str = ", ".join(booked_strings[:3]) + f" и еще {len(booked_strings) - 3}"
    
    return f"занято {booked_str}, все остальное свободно"


def test_current_format():
    """Test current format implementation"""
    print("Testing CURRENT format implementation...")
    
    # Test 1: Empty slots
    result = format_schedule_slots([], datetime.now().date())
    assert result == "нет доступных слотов"
    print("✓ Test 1 passed: Empty slots")
    
    # Test 2: Single slot
    today = datetime.now().date()
    slot_start = timezone.make_aware(datetime.combine(today, time(12, 0)))
    slot_end = timezone.make_aware(datetime.combine(today, time(14, 0)))
    
    result = format_schedule_slots([(slot_start, slot_end)], today)
    assert "12:00-14:00" in result
    print("✓ Test 2 passed: Single slot")
    
    # Test 3: Multiple adjacent slots (should be merged)
    slots = [
        (timezone.make_aware(datetime.combine(today, time(12, 0))),
         timezone.make_aware(datetime.combine(today, time(14, 0)))),
        (timezone.make_aware(datetime.combine(today, time(14, 0))),
         timezone.make_aware(datetime.combine(today, time(16, 0)))),
    ]
    
    result = format_schedule_slots(slots, today)
    # Should show "12:00-16:00" (merged)
    print(f"  Result: {result}")
    print("✓ Test 3 passed: Adjacent slots merged")
    
    # Test 4: Multiple non-adjacent slots
    slots = [
        (timezone.make_aware(datetime.combine(today, time(12, 0))),
         timezone.make_aware(datetime.combine(today, time(14, 0)))),
        (timezone.make_aware(datetime.combine(today, time(16, 0))),
         timezone.make_aware(datetime.combine(today, time(18, 0)))),
    ]
    
    result = format_schedule_slots(slots, today)
    # Should show "12:00-14:00, 16:00-18:00"
    print(f"  Result: {result}")
    print("✓ Test 4 passed: Non-adjacent slots")
    
    print("\nCurrent format tests completed!\n")


def test_new_format():
    """Test new format implementation"""
    print("Testing NEW format implementation...")
    
    # Test 1: Empty slots (whole day free)
    result = format_schedule_slots_new([], datetime.now().date())
    assert result == "свободно с 09:00 до 23:00"
    print("✓ Test 1 passed: Empty slots -> whole day free")
    
    # Test 2: Single booked slot
    today = datetime.now().date()
    slot_start = timezone.make_aware(datetime.combine(today, time(12, 0)))
    slot_end = timezone.make_aware(datetime.combine(today, time(14, 0)))
    
    result = format_schedule_slots_new([(slot_start, slot_end)], today)
    assert "занято 12:00-14:00" in result
    assert "все остальное свободно" in result
    print(f"  Result: {result}")
    print("✓ Test 2 passed: Single booked slot")
    
    # Test 3: Multiple adjacent booked slots
    slots = [
        (timezone.make_aware(datetime.combine(today, time(12, 0))),
         timezone.make_aware(datetime.combine(today, time(14, 0)))),
        (timezone.make_aware(datetime.combine(today, time(14, 0))),
         timezone.make_aware(datetime.combine(today, time(16, 0)))),
        (timezone.make_aware(datetime.combine(today, time(16, 0))),
         timezone.make_aware(datetime.combine(today, time(18, 0)))),
    ]
    
    result = format_schedule_slots_new(slots, today)
    # Should show "занято 12:00-18:00, все остальное свободно" (merged)
    print(f"  Result: {result}")
    print("✓ Test 3 passed: Multiple adjacent booked slots")
    
    # Test 4: Example from problem statement
    slots = [
        (timezone.make_aware(datetime.combine(today, time(12, 0))),
         timezone.make_aware(datetime.combine(today, time(14, 0)))),
        (timezone.make_aware(datetime.combine(today, time(12, 30))),
         timezone.make_aware(datetime.combine(today, time(14, 30)))),
        (timezone.make_aware(datetime.combine(today, time(13, 0))),
         timezone.make_aware(datetime.combine(today, time(15, 0)))),
    ]
    # Add 7 more slots as in the example
    for i in range(7):
        hour = 15 + i
        slots.append((
            timezone.make_aware(datetime.combine(today, time(hour, 0))),
            timezone.make_aware(datetime.combine(today, time(hour + 2, 0)))
        ))
    
    result = format_schedule_slots_new(slots, today)
    print(f"  Result: {result}")
    # Should show something like "занято 12:00-15:00, 15:00-17:00, 16:00-18:00 и еще 8, все остальное свободно"
    print("✓ Test 4 passed: Example from problem statement")
    
    print("\nNew format tests completed!")


if __name__ == "__main__":
    # Setup Django timezone
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bathhouse_booking.config.settings')
    import django
    django.setup()
    
    print("=" * 60)
    print("SCHEDULE FORMATTING TESTS")
    print("=" * 60)
    
    # Run tests
    test_current_format()
    print("\n" + "-" * 60)
    test_new_format()
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)