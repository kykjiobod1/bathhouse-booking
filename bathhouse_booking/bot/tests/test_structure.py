import os
import sys
from pathlib import Path

class TestBotStructure:
    def test_bot_directory_exists(self):
        bot_dir = Path(__file__).parent.parent
        assert bot_dir.exists()
        assert bot_dir.is_dir()
        assert bot_dir.name == "bot"
    
    def test_bot_files_exist(self):
        bot_dir = Path(__file__).parent.parent
        
        required_files = [
            "main.py",
            "routers.py", 
            "states.py",
            "keyboards.py",
            "dependencies.py",
        ]
        
        for file_name in required_files:
            file_path = bot_dir / file_name
            assert file_path.exists(), f"Файл {file_name} не найден"
    
    def test_handlers_directory_exists(self):
        bot_dir = Path(__file__).parent.parent
        handlers_dir = bot_dir / "handlers"
        
        assert handlers_dir.exists()
        assert handlers_dir.is_dir()
        
        required_handler_files = [
            "start.py",
            "booking.py",
        ]
        
        for file_name in required_handler_files:
            file_path = handlers_dir / file_name
            assert file_path.exists(), f"Файл handlers/{file_name} не найден"
    
    def test_init_files_exist(self):
        bot_dir = Path(__file__).parent.parent
        
        init_files = [
            bot_dir / "__init__.py",
            bot_dir / "handlers" / "__init__.py",
            bot_dir / "tests" / "__init__.py",
        ]
        
        for init_file in init_files:
            assert init_file.exists(), f"__init__.py не найден: {init_file}"