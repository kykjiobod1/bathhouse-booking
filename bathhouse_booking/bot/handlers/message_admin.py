from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async
from bathhouse_booking.bookings.models import SystemConfig, Client
import logging

logger = logging.getLogger(__name__)

router = Router()

class MessageAdminStates(StatesGroup):
    waiting_for_message = State()

async def get_admin_telegram_id():
    """Получить Telegram ID администратора из SystemConfig"""
    try:
        config = await sync_to_async(SystemConfig.objects.get)(key="TELEGRAM_ADMIN_ID")
        return config.value if config.value else None
    except SystemConfig.DoesNotExist:
        return None

@router.callback_query(lambda c: c.data == "message_admin")
async def start_message_admin(callback: types.CallbackQuery, state: FSMContext):
    """Начать диалог с администратором"""
    admin_id = await get_admin_telegram_id()
    
    if not admin_id:
        await callback.message.edit_text(
            "❌ Администратор еще не назначен.\n"
            "Пожалуйста, попробуйте позже или свяжитесь другим способом."
        )
        return
    
    await state.set_state(MessageAdminStates.waiting_for_message)
    await callback.message.edit_text(
        "💬 Напишите сообщение для администратора:\n\n"
        "Вы можете отправить текст, фото или любой другой тип сообщения.\n"
        "Для отмены нажмите /cancel"
    )

@router.message(Command("cancel"), MessageAdminStates.waiting_for_message)
async def cancel_message(message: types.Message, state: FSMContext):
    """Отменить отправку сообщения"""
    await state.clear()
    await message.answer("❌ Отправка сообщения отменена.")

@router.message(MessageAdminStates.waiting_for_message)
async def forward_to_admin(message: types.Message, state: FSMContext, bot):
    """Переслать сообщение администратору"""
    admin_id = await get_admin_telegram_id()
    
    if not admin_id:
        await message.answer("❌ Администратор еще не назначен.")
        await state.clear()
        return
    
    try:
        # Получаем или создаем клиента
        client, created = await sync_to_async(Client.objects.get_or_create)(
            telegram_id=str(message.from_user.id),
            defaults={
                'name': message.from_user.full_name or 'Неизвестный',
                'phone': ''
            }
        )
        
        # Пересылаем сообщение администратору
        forwarded_msg = await message.forward(chat_id=admin_id)
        
        # Добавляем информацию о клиенте
        client_info = (
            f"\n\n👤 От: {client.name}\n"
            f"Telegram ID: {client.telegram_id}\n"
            f"Телефон: {client.phone or 'не указан'}"
        )
        
        await bot.send_message(
            chat_id=admin_id,
            text=client_info,
            reply_to_message_id=forwarded_msg.message_id
        )
        
        await message.answer(
            "✅ Ваше сообщение отправлено администратору!\n"
            "Администратор ответит вам в этом чате, когда будет возможность."
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Failed to forward message to admin: {e}")
        await message.answer(
            "❌ Не удалось отправить сообщение.\n"
            "Пожалуйста, попробуйте позже."
        )
        await state.clear()

@router.message(F.reply_to_message)
async def handle_admin_reply(message: types.Message, bot):
    """Обработать ответ администратора на пересланное сообщение"""
    try:
        # Проверяем, является ли сообщение ответом на пересланное сообщение
        replied_msg = message.reply_to_message
        
        if not replied_msg:
            return
        
        # Пытаемся найти original_sender_id разными способами
        original_sender_id = None
        
        # Способ 1: администратор ответил напрямую на пересланное сообщение
        if replied_msg.forward_from:
            original_sender_id = replied_msg.forward_from.id
            logger.info(f"Found sender via forward_from: {original_sender_id}")
        
        # Способ 2: администратор ответил на текстовое сообщение с информацией о клиенте,
        # которое само является ответом на пересланное сообщение
        elif replied_msg.reply_to_message and replied_msg.reply_to_message.forward_from:
            original_sender_id = replied_msg.reply_to_message.forward_from.id
            logger.info(f"Found sender via reply_to_message.forward_from: {original_sender_id}")
        
        # Способ 3: администратор ответил на текстовое сообщение с информацией о клиенте,
        # в котором есть упоминание Telegram ID в тексте (резервный способ)
        if not original_sender_id and replied_msg.text:
            import re
            # Ищем Telegram ID в тексте сообщения (например: "Telegram ID: 123456")
            match = re.search(r'Telegram ID:\s*(\d+)', replied_msg.text)
            if match:
                original_sender_id = match.group(1)
                logger.info(f"Found sender via text parsing: {original_sender_id}")
        
        if not original_sender_id:
            logger.warning(f"Could not find original sender for admin reply. replied_msg: {replied_msg}")
            return
        
        # Отправляем ответ обратно клиенту
        reply_text = f"📨 Ответ от администратора:\n\n{message.text or '📎 (сообщение с вложением)'}"
        
        await bot.send_message(
            chat_id=original_sender_id,
            text=reply_text
        )
        
        # Подтверждаем администратору, что ответ отправлен
        await message.reply("✅ Ответ отправлен клиенту.")
        
        logger.info(f"Admin reply forwarded to user {original_sender_id}")
        
    except Exception as e:
        logger.error(f"Failed to handle admin reply: {e}", exc_info=True)
        await message.reply("❌ Не удалось отправить ответ клиенту.")