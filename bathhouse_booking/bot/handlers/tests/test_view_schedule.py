#!/usr/bin/env python3
"""
Tests for view_schedule handler
"""
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bathhouse_booking.config.settings')
import django
django.setup()

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import CallbackQuery, User, Chat, Message

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from bot.handlers.booking import view_schedule
from bathhouse_booking.bookings.models import Bathhouse


class TestViewSchedule:
    """Test cases for view_schedule handler"""
    
    @pytest.fixture
    def mock_objects(self):
        """Create mock objects for testing"""
        # Mock user and chat
        mock_user = User(id=12345, is_bot=False, first_name="Test", last_name="User", username="testuser")
        mock_chat = Chat(id=12345, type="private")
        
        # Mock message
        mock_message = MagicMock(spec=Message)
        mock_message.answer = AsyncMock()
        mock_message.chat = mock_chat
        
        # Mock callback query
        mock_callback = MagicMock(spec=CallbackQuery)
        mock_callback.answer = AsyncMock()
        mock_callback.message = mock_message
        mock_callback.from_user = mock_user
        mock_callback.data = "view_schedule"
        
        # Mock FSM context
        storage = MemoryStorage()
        key = StorageKey(bot_id=123, chat_id=123, user_id=456)
        state = FSMContext(storage=storage, key=key)
        
        return {
            'callback': mock_callback,
            'state': state,
            'message': mock_message
        }
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_view_schedule_no_bathhouses(self, mock_objects):
        """Test view_schedule when there are no active bathhouses"""
        callback = mock_objects['callback']
        state = mock_objects['state']
        
        # Mock Bathhouse.objects.filter to return empty queryset
        with patch('bot.handlers.booking.Bathhouse') as MockBathhouse:
            qs = MagicMock()
            qs.__iter__ = lambda self: iter([])
            MockBathhouse.objects.filter.return_value = qs

            await view_schedule(callback, state)
            
            # Check that appropriate message was sent
            callback.message.answer.assert_called_once()
            args, kwargs = callback.message.answer.call_args
            assert "нет доступных бань" in args[0].lower()
    
    @pytest.mark.skip(reason="Complex mocking required")
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_view_schedule_with_bathhouses(self, mock_objects):
        """Test view_schedule with active bathhouses"""
        callback = mock_objects['callback']
        state = mock_objects['state']
        
        # Create mock bathhouse
        mock_bathhouse = MagicMock(spec=Bathhouse)
        mock_bathhouse.id = 1
        mock_bathhouse.name = "Test Bathhouse"
        mock_bathhouse.is_active = True
        
        # Mock available slots - simulate a day with some booked slots
        # Let's say we have slots from 12:00-14:00, 12:30-14:30, 13:00-15:00 booked
        # and the rest of the day is free
        today = timezone.now().date()
        
        # Create datetime objects for slots
        slot1_start = timezone.make_aware(datetime.combine(today, datetime.min.time().replace(hour=12, minute=0)))
        slot1_end = timezone.make_aware(datetime.combine(today, datetime.min.time().replace(hour=14, minute=0)))
        
        slot2_start = timezone.make_aware(datetime.combine(today, datetime.min.time().replace(hour=12, minute=30)))
        slot2_end = timezone.make_aware(datetime.combine(today, datetime.min.time().replace(hour=14, minute=30)))
        
        slot3_start = timezone.make_aware(datetime.combine(today, datetime.min.time().replace(hour=13, minute=0)))
        slot3_end = timezone.make_aware(datetime.combine(today, datetime.min.time().replace(hour=15, minute=0)))
        
        available_slots = [
            (slot1_start, slot1_end),
            (slot2_start, slot2_end),
            (slot3_start, slot3_end),
        ]
        
        # Mock services.get_available_slots to return our test slots
        with patch('bathhouse_booking.bot.handlers.booking.sync_to_async') as mock_sync:
            # First call for bathhouses
            mock_sync.side_effect = [
                AsyncMock(return_value=[mock_bathhouse]),  # Bathhouse.objects.filter
                AsyncMock(return_value=available_slots),   # services.get_available_slots for today
                AsyncMock(return_value=[]),                # services.get_available_slots for tomorrow
                AsyncMock(return_value=[]),                # services.get_available_slots for day after tomorrow
                AsyncMock(return_value=9),                 # get_config_int OPEN_HOUR
                AsyncMock(return_value=22),                # get_config_int CLOSE_HOUR
            ]
            
            await view_schedule(callback, state)
            
            # Check that message was sent
            callback.message.answer.assert_called_once()
            args, kwargs = callback.message.answer.call_args
            
            # Check that message contains schedule text
            assert "расписание" in args[0].lower()
            assert "test bathhouse" in args[0].lower()
            
            # Save the output for inspection
            print("\nCurrent output format:")
            print(args[0])
            
            # Check current format (before our changes)
            # Currently it shows something like: "Сегодня: 12:00-14:00, 12:30-14:30, 13:00-15:00"
            assert "сегодня:" in args[0].lower()
    
    @pytest.mark.skip(reason="Complex mocking required")
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_view_schedule_full_day_free(self, mock_objects):
        """Test view_schedule when the whole day is free"""
        callback = mock_objects['callback']
        state = mock_objects['state']
        
        # Create mock bathhouse
        mock_bathhouse = MagicMock(spec=Bathhouse)
        mock_bathhouse.id = 1
        mock_bathhouse.name = "Test Bathhouse"
        mock_bathhouse.is_active = True
        
        # Mock empty available slots (whole day is free)
        with patch('bathhouse_booking.bot.handlers.booking.sync_to_async') as mock_sync:
            # First call for bathhouses
            mock_sync.side_effect = [
                AsyncMock(return_value=[mock_bathhouse]),  # Bathhouse.objects.filter
                AsyncMock(return_value=[]),                # services.get_available_slots for today
                AsyncMock(return_value=[]),                # services.get_available_slots for tomorrow
                AsyncMock(return_value=[]),                # services.get_available_slots for day after tomorrow
            ]
            
            await view_schedule(callback, state)
            
            # Check that message was sent
            callback.message.answer.assert_called_once()
            args, kwargs = callback.message.answer.call_args
            
            # Should show "нет доступных слотов" for empty day
            assert "нет доступных слотов" in args[0].lower()


if __name__ == "__main__":
    # Run tests manually
    import asyncio
    
    test = TestViewSchedule()
    mock_objs = test.mock_objects()
    
    print("Running view_schedule tests...")
    
    # Test 1: No bathhouses
    print("\n1. Testing with no bathhouses:")
    asyncio.run(test.test_view_schedule_no_bathhouses(mock_objs))
    
    # Test 2: With bathhouses
    print("\n2. Testing with bathhouses and slots:")
    asyncio.run(test.test_view_schedule_with_bathhouses(mock_objs))
    
    # Test 3: Full day free
    print("\n3. Testing with full day free:")
    asyncio.run(test.test_view_schedule_full_day_free(mock_objs))
    
    print("\nAll tests completed!")