from PyQt5.QtWidgets import QWidget, QLineEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, QTimer
from pynput import keyboard, mouse
from threading import Lock

import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.utils.log_manager import LogManager
from src.core.hotkey_manager import HotkeyManager
from src.utils.helper_methods import HelperMethods

class HotkeyInputWidget(QWidget):
    hotkeyChanged = pyqtSignal()  

    def __init__(self, parent=None):
        """
        Initialize hotkey input widget
        """
        super().__init__(parent)
        self._log_manager = LogManager.get_instance()
        self._hotkey_manager = HotkeyManager.get_instance()
        self._helper = HelperMethods.get_instance()
        
        self._last_hotkey = None
        self._recording = False
        
        self._modifier_keys = {
            'shift', 'ctrl', 'alt', 'cmd', 'win'
        }

        # Listeners
        self._keyboard_listener = None
        self._mouse_listener = None

        # Thread safety
        self._lock = Lock()

        self._cur_pressed = set()
        self._pressed = set()

        self._create_widgets()
        
    def _create_widgets(self):
        """
        Create the hotkey input widgets
        """
        try:
            # Create the hotkey display field (read-only)
            self._hotkey_display = QLineEdit(self)
            self._hotkey_display.setReadOnly(True)  # Make it read-only
            self._hotkey_display.setPlaceholderText("")  # Placeholder text
            self._hotkey_display.setFixedWidth(200)  # Set a fixed width

            # Create the "Record" button
            self._record_button = QPushButton("Record", self)
            self._record_button.clicked.connect(self._toggle_recording)  # Connect to toggle recording

            # Create the "Clear" button
            self._clear_button = QPushButton("Clear", self)
            self._clear_button.clicked.connect(self._clear_hotkey)  # Connect to clear hotkey

            # Arrange widgets in a horizontal layout
            layout = QHBoxLayout()
            layout.addWidget(self._hotkey_display)  # Add hotkey display field
            layout.addWidget(self._record_button)   # Add "Record" button
            layout.addWidget(self._clear_button)    # Add "Clear" button

            # Set the layout for this widget
            self.setLayout(layout)
        except Exception as e:
            self._log_manager.log_error(f"Failed to create hotkey input widget", error = e)
            raise

    def _toggle_recording(self):
        """
        Toggle hotkey recording state
        """
        if not self._recording:
            self._recording = True
            self._record_button.setText("Stop")
            self._pressed.clear()
            self._old_hotkey = self._hotkey_display.text()
            self._hotkey_display.setText("Press keys...")
            if self._helper.get_hotkey_listener_status():
                self._hotkey_manager.stop_listeners()
            self._start_listeners()         
        else:
            self._recording = False
            if self._pressed == {'mouse_left'} and self._last_hotkey:
                # If no new key is pressed, keep the last hotkey
                self._pressed.add(self._last_hotkey)
            elif self._pressed == {'mouse_left'} and not self._last_hotkey:
                self._pressed.add(self._old_hotkey)
            self._record_button.setText("Record")
            self._stop_listeners()
            if self._helper.get_hotkey_listener_status():
                self._hotkey_manager.start_listeners()

    def _start_listeners(self):
        """
        Start the keyboard and mouse listeners
        """
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
        self._keyboard_listener.start()
        self._mouse_listener.start()

    def _stop_listeners(self):
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
    
    def _on_key_press(self, key):
        """
        Handles key press events
        """
        with self._lock:
            key_str = self._helper.key_to_string(key)
            
            self._cur_pressed.add(key_str)
            self._pressed.add(key_str)

    def _on_key_release(self, key):
        """
        Handles key release events
        """
        with self._lock:
            key_str = self._helper.key_to_string(key)

            self._cur_pressed.discard(key_str)
            if not self._cur_pressed:
                self._update_hotkey_string()
                QTimer.singleShot(0, self._toggle_recording)
        
    def _on_mouse_click(self, x, y, button, pressed):
        """
        Handles mouse click events.
        Tracks mouse buttons as part of hotkeys.
        """
        with self._lock:
            button_str = f"mouse_{button.name}"

            if pressed:
                self._pressed.add(button_str)
                self._cur_pressed.add(button_str)
            else:
                self._cur_pressed.discard(button_str)
            
            if not self._cur_pressed:
                self._update_hotkey_string()
                QTimer.singleShot(0, self._toggle_recording)

    def _update_hotkey_string(self):
        """
        Update the hotkey string based on current keys
        """
        if self._pressed == {'mouse_left'} and self._last_hotkey:
                # If no new key is pressed, keep the last hotkey
                hotkey_string = self._last_hotkey
        elif self._pressed == {'mouse_left'} and not self._last_hotkey:
                hotkey_string = self._old_hotkey
        else:
        # Sort keys: ctrl first, then modifiers (shift/alt), then others alphabetically
            sorted_keys = sorted(
                self._pressed,
                key=lambda k: (k != "ctrl", k not in self._modifier_keys, k)
            )
            hotkey_string = " ".join(sorted_keys)
        self._hotkey_display.setText(hotkey_string)
        self.hotkeyChanged.emit()
        self._last_hotkey = hotkey_string
        self._pressed.clear()

    def _clear_hotkey(self):
        """
        Clear the current hotkey
        """
        self._hotkey_display.setText("")
        self._last_hotkey = None

    def get_hotkey(self) -> str:
        """
        Get the current hotkey string
        """
        return self._hotkey_display.text()

    def set_hotkey(self, hotkey: str):
        """
        Set the hotkey string
        """
        # if hotkey:
        keys = set(hotkey.split())
        self._pressed = keys
        self._update_hotkey_string()