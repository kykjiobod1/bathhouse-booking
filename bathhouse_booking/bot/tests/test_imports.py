import sys
from pathlib import Path
import pytest

class TestBotImports:
    def test_main_module_imports(self):
        try:
            from bot import main
            assert hasattr(main, 'main')
            assert callable(main.main)
        except ImportError as e:
            pytest.fail(f"Failed to import bot.main: {e}")
    
    def test_routers_module_imports(self):
        try:
            from bot import routers
            assert hasattr(routers, 'router')
        except ImportError as e:
            pytest.fail(f"Failed to import bot.routers: {e}")
    
    def test_states_module_imports(self):
        try:
            from bot import states
            assert hasattr(states, 'BookingStates')
        except ImportError as e:
            pytest.fail(f"Failed to import bot.states: {e}")
    
    def test_keyboards_module_imports(self):
        try:
            from bot import keyboards
            assert hasattr(keyboards, 'main_menu_keyboard')
            assert callable(keyboards.main_menu_keyboard)
        except ImportError as e:
            pytest.fail(f"Failed to import bot.keyboards: {e}")
    
    def test_dependencies_module_imports(self):
        try:
            from bot import dependencies
            assert hasattr(dependencies, 'setup_dependencies')
            assert callable(dependencies.setup_dependencies)
            assert hasattr(dependencies, 'get_services')
            assert callable(dependencies.get_services)
        except ImportError as e:
            pytest.fail(f"Failed to import bot.dependencies: {e}")
    
    def test_handlers_imports(self):
        try:
            from bot.handlers import start
            assert hasattr(start, 'router')
        except ImportError as e:
            pytest.fail(f"Failed to import bot.handlers.start: {e}")
        
        try:
            from bot.handlers import booking
            assert hasattr(booking, 'router')
        except ImportError as e:
            pytest.fail(f"Failed to import bot.handlers.booking: {e}")