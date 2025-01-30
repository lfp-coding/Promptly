import time
import ctypes
from threading import Lock, Thread
from pynput import keyboard, mouse
from queue import Queue
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.utils.prompt_manager import PromptManager
from src.core.text_processor import TextProcessor
from src.utils.config_manager import ConfigManager 
from src.utils.log_manager import LogManager
from src.utils.ipc_command_handler import send_ipc_command
from src.utils.helper_methods import HelperMethods
from src.ui.prompt_selector_window import PromptSelector

class HotkeyManager:
    """
    A class to manage global hotkeys with support for both keyboard and mouse inputs.
    Hotkeys are triggered only when non-modifier keys are released.
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = HotkeyManager()
        return cls._instance
        
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._log_manager = LogManager.get_instance()
        self._prompt_manager = PromptManager.get_instance()
        self._text_processor = TextProcessor.get_instance()
        self._config_manager = ConfigManager.get_instance()
        self._helper = HelperMethods.get_instance()
        self._lock = Lock()  # Prevent concurrent hotkey processing
        self._modifier_keys = {
            'shift', 'ctrl', 'alt', 'cmd', 'win'
        }
        self._cur_mod = set() # Currently active modifiers
        self._non_mod = set() # Non-modifier keys pressed since the last modifier change
        self._cur_non_mod = set() # Currently active non modifiers
        self._mod = set() # Persistent modifiers pressed together
        self.load_hotkeys()

        # Initialize listeners as None
        self._keyboard_listener = None
        self._mouse_listener = None
        self._hotkey_queue = Queue()
        self._monitor_thread = None

        self._last_activity_time = None

        self._log_manager.log_info('HotkeyManager initialized')
    
    def _queue_handler(self):
        """
        handles the hotkey queue
        """
        while True:
            task = self._hotkey_queue.get()
            if task == 'STOP':
                break
            self._execute_hotkey(task)
            self._hotkey_queue.task_done()

    def _on_key_press(self, key):
        """
        Handles key press events
        """
        with self._lock:
            self._last_activity_time = time.time()
            key_str = self._helper.key_to_string(key)

            if key_str in self._modifier_keys:
                # Update current modifiers and reset non-modifiers
                self._cur_mod.add(key_str)
                self._mod.add(key_str)
            
                self._non_mod.clear()
            else:
                # Add to non-modifiers if it's not a modifier key and reset modifier
                self._non_mod.add(key_str)
                self._cur_non_mod.add(key_str)

                self._mod.clear()

    def _on_key_release(self, key):
        """
        Handles key release events.
        Checks if any hotkeys should be triggered.
        """
        with self._lock:
            key_str = self._helper.key_to_string(key)

            if key_str in self._modifier_keys:
                # Remove from current modifiers
                self._cur_mod.discard(key_str)
                    
            else:
                # Remove from current non-modifiers
                self._cur_non_mod.discard(key_str)

            # Trigger hotkey checks when no keys are pressed
            if not self._cur_non_mod:
                self._check_hotkeys()
        
    def _on_mouse_click(self, x, y, button, pressed):
        """
        Handles mouse click events.
        Tracks mouse buttons as part of hotkeys.
        """
        with self._lock:
            button_str = f"mouse_{button.name}"
            self._last_activity_time = time.time()
            if pressed:
                # Add mouse button to current and persistent non-modifiers
                self._cur_non_mod.add(button_str)
                self._non_mod.add(button_str)

                # Reset non modifiers
                self._mod.clear()
            else:
                self._cur_non_mod.discard(button_str)
                if not self._cur_non_mod:
                    self._check_hotkeys()

    def _check_hotkeys(self):
        """
        Check if any defined hotkeys match the current state of pressed keys/buttons
        """
        current_combination = frozenset(self._cur_mod | self._non_mod | self._mod)

        id = self._hotkeys.get(current_combination, None)

        if id == None:
            return
        else:
            self._cur_mod.clear()
            self._non_mod.clear()
            self._mod.clear()
            self._cur_non_mod.clear()
            self._hotkey_queue.put(id)     

    def _execute_hotkey(self, id: str):
        """
        executes hotkey
        """
        if id == 'chat_window':
            send_ipc_command('show-chat')
        elif id == 'settings_window':
            send_ipc_command('show-config')
        elif id == 'prompt_selector':
            send_ipc_command('show-prompt_selector')
        elif id is not None:
            self._text_processor.process_text_with_prompt(id)

    def show_prompt_selector(self):
        """
        Show the floating PromptSelector menu
        """
        self._prompt_selector = None
        if not self._prompt_selector:
            app = QApplication(sys.argv)  # Create a PyQt application instance if not already running
            self._prompt_selector = PromptSelector()

        # Show the context menu at cursor position
        
        QTimer.singleShot(0, self._prompt_selector.show_menu)
        app.exec_()

    def start_listeners(self):
        """
        Start the keyboard and mouse listeners
        """
        self._last_activity_time = time.time()
        self._cur_mod.clear()
        self._non_mod.clear()
        self._mod.clear()
        self._cur_non_mod.clear()
        if not (self._keyboard_listener or self._mouse_listener):
            # Initialize and start keyboard listener
            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            
            # Initialize and start mouse listener
            self._mouse_listener = mouse.Listener(
                on_click=self._on_mouse_click
            )

        # Start both listeners
        self._queue_thread = Thread(target=self._queue_handler, daemon=True)
        self._queue_thread.start()
        self._keyboard_listener.start()
        self._mouse_listener.start()

        if not self._monitor_thread or not self._monitor_thread.is_alive():
            self._monitor_thread = Thread(target=self._monitor_listener_health, daemon=True)
            self._monitor_thread.start()

    def stop_listeners(self):
        """
        Stop the keyboard and mouse listeners
        """
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener.join()
            self._keyboard_listener = None

        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener.join()
            self._mouse_listener = None

        from pynput.keyboard import Key, Controller

        keyboard_ = Controller()

        keys = [Key.ctrl, Key.alt, Key.shift, Key.esc]
        for key in keys:
            keyboard_.release(key)
        self._cur_mod.clear()
        self._non_mod.clear()
        self._cur_non_mod.clear()
        self._mod.clear()

        # Signal the queue handler thread to stop and wait for it to finish
        if hasattr(self, '_queue_thread') and self._queue_thread.is_alive():
            self._hotkey_queue.put("STOP")
            self._queue_thread.join()

    def _monitor_listener_health(self):
        """
        Periodically checks if the listener threads are still alive. If not,
        it restarts them. This approach recreates listener threads if they
        die after a PC lock event.
        """
        was_locked = False
        while True:
            time.sleep(3)  # Adjust interval as needed
            if not self._helper.get_hotkey_listener_status():
                return

            is_locked = ctypes.windll.user32.GetForegroundWindow() == 0
            if is_locked or was_locked or self._last_activity_time - time.time() > 30:
                with self._lock:
                    self._cur_mod.clear()
                    self._non_mod.clear()
                    self._mod.clear()
                    self._cur_non_mod.clear()

            if (not self._keyboard_listener or not self._keyboard_listener.is_alive()) \
                    or (not self._mouse_listener or not self._mouse_listener.is_alive()):
                self._log_manager.log_info("Listener thread seems to have stopped. Restarting.")
                self.start_listeners()

            was_locked = is_locked
    
    def load_hotkeys(self):
        """
        Load enabled hotkeys
        """
        try:
            system_hotkeys = self._config_manager.get_value('system_hotkeys')
            prompts = self._config_manager.get_value('prompts')

            # Initialize an empty dictionary to store enabled hotkeys
            self._hotkeys = {}

            for id, hotkey_config in system_hotkeys.items():
                if hotkey_config.hotkey_enabled:
                    self._add_hotkey(id=id, hotkey=hotkey_config.hotkey)

            # Process prompt hotkeys
            for id, prompt_config in prompts.items():
                if prompt_config.hotkey_enabled:
                    self._add_hotkey(id=id, hotkey=prompt_config.hotkey)

            self._log_manager.log_info(f"Loaded {len(self._hotkeys)} enabled hotkeys.")
        except Exception as e:
            self._log_manager.log_error(f"Failed to load hotkeys", error = e)

    def _add_hotkey(self, id: str, hotkey: str):
        """
        Adds hotkey to self._hotkey
        """
        # Convert the hotkey string to a frozenset and add it to the dictionary
        hotkey_set = frozenset(hotkey.split())
        self._hotkeys[hotkey_set] = id