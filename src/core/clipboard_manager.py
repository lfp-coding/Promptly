import pyperclip 
from pynput.keyboard import Controller
from typing import Optional
from time import sleep
import pyautogui

import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.utils.log_manager import LogManager

class ClipboardManager:
    """Singleton class for managing clipboard operations"""
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ClipboardManager()
        return cls._instance
        
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._keyboard = Controller()
        self._log_manager = LogManager.get_instance()
        self._sleep_time = 0.05
        self._log_manager.log_info("ClipboardManager initialized")

    def get_selected_text(self) -> Optional[str]:
        """
        Get currently selected text by simulating Ctrl+C
        
        Returns:
            Optional[str]: Selected text or None if no selection/error
        """
        try:
            # Store current clipboard content
            original = pyperclip.paste()
            
            # Clear clipboard
            pyperclip.copy('')
            
            # Release all modifiers to ensure no interference
            self.release_all_modifiers()

            # Simulate Ctrl+C
            pyautogui.hotkey('ctrl', 'c')    
            
            # Wait a bit for the clipboard to update
            sleep(self._sleep_time)
            
            # Get selection
            selected_text = pyperclip.paste()
            
            # Restore original clipboard content
            if original:
                pyperclip.copy(original)
                
            return selected_text if selected_text else None
            
        except Exception as e:
            self._log_manager.log_error(f"Failed to get selected text", error = e)
            return None

    def release_all_modifiers(self):
        """
        Release all currently pressed modifiers
        """
        pyautogui.keyUp('shift')
        pyautogui.keyUp('ctrl')
        pyautogui.keyUp('alt')
        pyautogui.keyUp('win') 
        pyautogui.keyUp('cmd') 

    def replace_text(self, new_text: str):
        """
        Replace currently selected text with new text
        
        Args:
            new_text: Text to replace selection with
        """
        try:
             # Store current clipboard content
            original = pyperclip.paste()

            # Copy new text to clipboard
            pyperclip.copy(new_text)

            # Release all modifiers to ensure no interference
            self.release_all_modifiers()

            # Simulate Ctrl+V
            pyautogui.hotkey('ctrl', 'v')  
            
            if original:
                pyperclip.copy(original)
            
            self._log_manager.log_info("Text replaced successfully")
            return True
        except Exception as e:
            self._log_manager.log_error(f"Failed to replace text", error = e)
            return False

    def select_all_text(self) -> Optional[str]:
        """
        Select all text in active window and return it
        
        Returns:
            Optional[str]: All text or None if error
        """
        try:
            # Release all modifiers to ensure no interference
            self.release_all_modifiers()
  
            pyautogui.hotkey('ctrl', 'a')  # Select all
            sleep(self._sleep_time)  # Wait for selection
            pyautogui.hotkey('ctrl', 'c')  # Copy
            sleep(self._sleep_time)  # Wait for clipboard update

            selected_text = pyperclip.paste() 
            return selected_text
            
        except Exception as e:
            self._log_manager.log_error(f"Failed to select all text", error = e)
            return None