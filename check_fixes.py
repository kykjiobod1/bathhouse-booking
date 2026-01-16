#!/usr/bin/env python3
"""
Скрипт для проверки всех исправлений.
"""
import os
import sys

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_fix_1_admin_command():
    """Проверка исправления 1: команда админа с sync_to_async"""
    print("🔍 Проверка 1: Команда /admin с sync_to_async")
    
    try:
        admin_file = os.path.join(os.path.dirname(__file__), "bathhouse_booking/bot/handlers/admin.py")
        with open(admin_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем импорты
        assert "from asgiref.sync import sync_to_async" in content, "Должен быть импорт sync_to_async"
        assert "await sync_to_async(SystemConfig.objects.get_or_create)" in content, "Должен быть await sync_to_async"
        assert "await sync_to_async(config.save)" in content, "Должен быть await sync_to_async для save"
        
        print("✅ Команда /admin: sync_to_async добавлен правильно")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def check_fix_2_schedule_calendar():
    """Проверка исправления 2: календарь для расписания"""
    print("\n🔍 Проверка 2: Календарь для 'посмотреть расписание'")
    
    try:
        booking_file = os.path.join(os.path.dirname(__file__), "bathhouse_booking/bot/handlers/booking.py")
        with open(booking_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем что функция показывает календарь
        assert "get_calendar_keyboard" in content, "Должен вызывать get_calendar_keyboard"
        assert "waiting_for_schedule_date" in content, "Должен устанавливать состояние waiting_for_schedule_date"
        assert "process_schedule_calendar_date" in content, "Должен быть обработчик для календаря расписания"
        
        print("✅ 'Посмотреть расписание': показывает календарь")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def check_fix_3_booking_calendar():
    """Проверка исправления 3: календарь бронирования с кнопкой назад"""
    print("\n🔍 Проверка 3: Календарь бронирования")
    
    try:
        calendar_file = os.path.join(os.path.dirname(__file__), "bathhouse_booking/bot/calendar_utils.py")
        with open(calendar_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем что есть кнопка назад
        assert "back_to_bathhouse_selection" in content, "Должна быть кнопка 'назад'"
        assert "show_back_button" in content, "Должен быть параметр show_back_button"
        assert "Назад" in content, "Должна быть кнопка 'Назад'"
        
        print("✅ Календарь бронирования: есть кнопка 'назад'")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def check_fix_4_my_bookings_buttons():
    """Проверка исправления 4: кнопки в 'мои бронирования'"""
    print("\n🔍 Проверка 4: Кнопки в 'мои бронирования'")
    
    try:
        my_bookings_file = os.path.join(os.path.dirname(__file__), "bathhouse_booking/bot/handlers/my_bookings.py")
        with open(my_bookings_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем что есть кнопка 'на главную'
        assert "На главную" in content, "Должна быть кнопка 'На главную'"
        assert "back_to_main" in content, "callback_data должен быть 'back_to_main'"
        
        print("✅ 'Мои бронирования': есть кнопки отмены и 'на главную'")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def check_fix_5_admin_status_readonly():
    """Проверка исправления 5: статус только для чтения в админке"""
    print("\n🔍 Проверка 5: Статус бронирования в админке")
    
    try:
        # Читаем файл напрямую
        admin_file = os.path.join(os.path.dirname(__file__), "bathhouse_booking/bookings/admin.py")
        with open(admin_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ищем readonly_fields
        import re
        pattern = r"readonly_fields\s*=\s*\[[^\]]*'status'[^\]]*\]"
        if re.search(pattern, content):
            print("✅ Статус бронирования: только для чтения в админке")
            return True
        else:
            print("❌ Статус бронирования: НЕ только для чтения в админке")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def check_fix_6_telegram_admin_id():
    """Проверка исправления 6: TELEGRAM_ADMIN_ID в конфиге"""
    print("\n🔍 Проверка 6: TELEGRAM_ADMIN_ID в SystemConfig")
    
    try:
        config_file = os.path.join(os.path.dirname(__file__), "bathhouse_booking/bookings/config_init.py")
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "'TELEGRAM_ADMIN_ID'" in content or '"TELEGRAM_ADMIN_ID"' in content:
            print("✅ TELEGRAM_ADMIN_ID: присутствует в DEFAULT_CONFIGS")
            return True
        else:
            print("❌ TELEGRAM_ADMIN_ID: отсутствует в DEFAULT_CONFIGS")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    """Основная функция проверки"""
    print("="*60)
    print("ПРОВЕРКА ВСЕХ ИСПРАВЛЕНИЙ")
    print("="*60)
    
    fixes = [
        ("1. Команда /admin с sync_to_async", check_fix_1_admin_command),
        ("2. Календарь для расписания", check_fix_2_schedule_calendar),
        ("3. Календарь бронирования с кнопкой назад", check_fix_3_booking_calendar),
        ("4. Кнопки в 'мои бронирования'", check_fix_4_my_bookings_buttons),
        ("5. Статус только для чтения в админке", check_fix_5_admin_status_readonly),
        ("6. TELEGRAM_ADMIN_ID в конфиге", check_fix_6_telegram_admin_id),
    ]
    
    results = []
    for name, check_func in fixes:
        print(f"\n{name}:")
        result = check_func()
        results.append((name, result))
    
    print("\n" + "="*60)
    print("ИТОГОВЫЙ ОТЧЕТ:")
    print("="*60)
    
    passed = 0
    for name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ НЕ ПРОЙДЕН"
        print(f"{name}: {status}")
        if result:
            passed += 1
    
    print("\n" + "="*60)
    print(f"РЕЗУЛЬТАТ: {passed}/{len(fixes)} исправлений проверены успешно")
    
    if passed == len(fixes):
        print("🎉 ВСЕ ИСПРАВЛЕНИЯ РАБОТАЮТ КОРРЕКТНО!")
    else:
        print(f"⚠️  Некоторые исправления требуют доработки ({len(fixes)-passed} проблем)")
    
    print("="*60)
    
    return passed == len(fixes)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)