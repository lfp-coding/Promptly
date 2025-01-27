from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtCore import Qt
from pynput import keyboard


import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.utils.prompt_manager import PromptManager
from src.core.text_processor import TextProcessor

class PromptSelector(QMenu):
    def __init__(self):
        """
        Initialize the PromptSelector context menu
        """
        super().__init__()

        self._active_index = 0

        self.setFocusPolicy(Qt.NoFocus)
        self._prompt_manager = PromptManager.get_instance()
        self._load_prompts()

    def _load_prompts(self):
        self._actions_list = []

        for prompt in self._prompt_manager.get_all_prompts().keys():
            action = QAction(prompt, self)
            self.addAction(action)

            self._actions_list.append(action)
            if self._actions_list:
                self.set_active_action(self._actions_list[self._active_index])

    def _process_prompt(self, prompt: str = None):
        """
        Handle the selected prompt and pass it to the callback function.
        """
        if not prompt is None:
            TextProcessor.get_instance().process_text_with_prompt(prompt)

    def key_press(self, key):
        """Handle keyboard navigation and selection."""
        if key == keyboard.Key.up:
            # Navigate up
            self._active_index = (self._active_index - 1) % len(self._actions_list)
            self.set_active_action(self._actions_list[self._active_index])

        elif key == keyboard.Key.down:
            # Navigate down
            self._active_index = (self._active_index + 1) % len(self._actions_list)
            self.set_active_action(self._actions_list[self._active_index])

    def set_active_action(self, action):
        """Highlight the given action."""
        self.setActiveAction(action)