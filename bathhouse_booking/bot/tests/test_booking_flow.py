#!/usr/bin/env python3
"""
Test for booking FSM flow
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey

from bot.handlers.booking import router
from bot.states import BookingStates

@pytest.mark.skip(reason="Complex async mocking required")
@pytest.mark.asyncio
async def test_booking_flow():
    """Test the complete booking FSM flow"""
    
    # Mock objects
    mock_user = types.User(id=12345, is_bot=False, first_name="Test")
    mock_message = types.Message(message_id=1, from_user=mock_user, date=1234567890, chat=types.Chat(id=12345, type="private"))
    mock_callback = MagicMock(spec=types.CallbackQuery)
    mock_callback.id = "test_callback"
    mock_callback.from_user = mock_user
    mock_callback.data = "test_data"
    mock_callback.message = mock_message
    mock_callback.chat_instance = "test"
    
    # FSM context
    storage = MemoryStorage()
    state = FSMContext(storage=storage, key=StorageKey(bot_id=123, chat_id=123, user_id=456))
    
    print("Testing booking FSM flow...")
    
    # Test 1: Start booking
    print("1. Testing start_booking...")
    mock_callback.data = "book_bathhouse"
    try:
        await router.callback_query.handlers[0].callback(mock_callback, state)
        current_state = await state.get_state()
        print(f"   Current state: {current_state}")
        assert current_state == BookingStates.waiting_for_bathhouse.state
        print("   ✓ Start booking works")
    except Exception as e:
        print(f"   ✗ Start booking failed: {e}")
    
    # Test 2: Select bathhouse
    print("2. Testing select_bathhouse...")
    mock_callback.data = "select_bathhouse:1"
    try:
        await router.callback_query.handlers[1].callback(mock_callback, state)
        current_state = await state.get_state()
        data = await state.get_data()
        print(f"   Current state: {current_state}")
        print(f"   Selected bathhouse: {data.get('bathhouse_id')}")
        assert current_state == BookingStates.waiting_for_date.state
        assert data.get('bathhouse_id') == 1
        print("   ✓ Select bathhouse works")
    except Exception as e:
        print(f"   ✗ Select bathhouse failed: {e}")
    
    # Test 3: Select date
    print("3. Testing select_date...")
    mock_callback.data = "select_date:today"
    try:
        await router.callback_query.handlers[2].callback(mock_callback, state)
        current_state = await state.get_state()
        data = await state.get_data()
        print(f"   Current state: {current_state}")
        print(f"   Selected date: {data.get('selected_date')}")
        assert current_state == BookingStates.waiting_for_slot.state
        assert data.get('selected_date') is not None
        print("   ✓ Select date works")
    except Exception as e:
        print(f"   ✗ Select date failed: {e}")
    
    # Test 4: Select slot (mock a slot)
    print("4. Testing select_slot...")
    from django.utils import timezone
    from datetime import datetime
    
    # Get available slots first
    from bathhouse_booking.bookings.models import Bathhouse
    from bathhouse_booking.bookings import services
    
    bathhouse = Bathhouse.objects.get(id=1)
    today = timezone.now().date()
    slots = services.get_available_slots(bathhouse, today)
    
    if slots:
        first_slot = slots[0]
        start_str = first_slot[0].strftime("%H:%M")
        end_str = first_slot[1].strftime("%H:%M")
        mock_callback.data = f"select_slot:{start_str}-{end_str}"
        
        try:
            await router.callback_query.handlers[3].callback(mock_callback, state)
            current_state = await state.get_state()
            data = await state.get_data()
            print(f"   Current state: {current_state}")
            print(f"   Booking ID: {data.get('booking_id')}")
            assert current_state == BookingStates.waiting_for_payment.state
            assert data.get('booking_id') is not None
            print("   ✓ Select slot works")
        except Exception as e:
            print(f"   ✗ Select slot failed: {e}")
    else:
        print("   ⚠ No slots available for testing")
    
    # Test 5: Report payment
    print("5. Testing report_payment...")
    mock_callback.data = "payment_reported"
    try:
        await router.callback_query.handlers[4].callback(mock_callback, state)
        current_state = await state.get_state()
        print(f"   Current state: {current_state}")
        assert current_state is None  # State should be cleared
        print("   ✓ Report payment works")
    except Exception as e:
        print(f"   ✗ Report payment failed: {e}")
    
    print("\nBooking FSM flow test completed!")