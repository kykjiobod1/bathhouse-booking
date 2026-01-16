from aiogram import Router, types
from aiogram.filters import Command
import os
from asgiref.sync import sync_to_async
from bathhouse_booking.bookings.models import SystemConfig
from bathhouse_booking.bookings.config_init import get_config

router = Router()

@router.message(Command("admin"))
async def cmd_admin(message: types.Message) -> None:
    """Команда /admin пароль для назначения администратора"""
    # Проверяем, есть ли аргумент (пароль)
    if not message.text or len(message.text.split()) < 2:
        await message.answer(
            "Использование: /admin пароль\n"
            "Введите пароль администратора."
        )
        return
    
    # Получаем пароль из аргумента команды
    command, password = message.text.split(maxsplit=1)
    
    # Получаем правильный пароль из переменной окружения
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    # Сравниваем пароли
    if password != admin_password:
        await message.answer("❌ Неверный пароль.")
        return
    
    # Сохраняем Telegram ID пользователя в SystemConfig
    telegram_id = str(message.from_user.id)
    
    try:
        # Получаем или создаём запись TELEGRAM_ADMIN_ID (асинхронно)
        config, created = await sync_to_async(SystemConfig.objects.get_or_create)(
            key="TELEGRAM_ADMIN_ID",
            defaults={"value": telegram_id, "description": "Telegram ID администратора"}
        )
        
        if not created:
            # Обновляем существующую запись
            config.value = telegram_id
            await sync_to_async(config.save)()
        
        await message.answer(
            f"✅ Вы назначены администратором!\n"
            f"Ваш Telegram ID: {telegram_id}\n"
            f"Теперь вы будете получать уведомления о новых заявках."
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении: {e}")