from typing import List, Dict

import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.utils.log_manager import LogManager
from src.utils.json_manager import JsonManager
from src.utils.path_manager import get_chat_history_file

class ChatHistory:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ChatHistory()
        return cls._instance
    
    def __init__(self):
        self._log_manager = LogManager.get_instance()
        self._history_path = get_chat_history_file()
        
        self._listeners = []

        self._messages: List[Dict] = []
        self.clear_history()

    def add_listener(self, listener):
        """
        Register a listener to be notified on changes
        """
        self._listeners.append(listener)

    def _notify_listeners(self):
        """
        Notify all registered listeners of a change
        """
        for listener in self._listeners:
            listener.update()

    def _load_history(self):
        """
        Loads chat history from file
        """
        try:
            if not self._history_path.exists():
                self._log_manager.log_info("No chat history file found, creating empty history.")
                self._messages = []
                return
            
            self._messages = JsonManager.load_from_file(self._history_path)
            self._log_manager.log_info("Chat history loaded successfully")
        except Exception as e:
            self._log_manager.log_error(f"Failed to load chat history", error = e)
            self._messages = []
    
    def save_history(self):
        """
        Saves current chat history to file
        """
        try:
            JsonManager.save_to_file(self._messages, self._history_path)
        except Exception as e:
            self._log_manager.log_error(f"Failed to save chat history", error = e)
    
    def add_message(self, role: str, content: str):
        """
        Adds a new message to the chat history
        Args:
            role: The role of the message sender (user/assistant)
            content: The message content
        """
        try:
            self._messages.append({"role": role, "content": content})
            self._notify_listeners()
        except Exception as e:
            self._log_manager.log_error(f"Failed to add message", error = e)
    
    def clear_history(self):
        """if something is unclear, just ask again.
        Clears the chat history
        """
        try:
            self._messages = []
            self._notify_listeners()
        except Exception as e:
            self._log_manager.log_error(f"Failed to clear history", error = e)
    
    def get_messages(self) -> List[Dict]:
        """
        Returns the current chat history
        Returns:
            List[Dict]: List of message dictionaries
        """
        self._log_manager.log_info("Retrieving chat history")
        return self._messages