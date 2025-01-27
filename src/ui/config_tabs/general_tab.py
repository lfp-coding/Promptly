from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QCheckBox, QLabel, QGroupBox, QGridLayout
)
from PyQt5.QtCore import Qt
import copy

import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.utils.log_manager import LogManager
from src.utils.config_manager import ConfigManager
from src.ui.widgets.hotkey_input import HotkeyInputWidget
from src.core.hotkey_manager import HotkeyManager


class GeneralTab(QWidget):
    def __init__(self, parent=None):
        """
        Initialize general settings tab
        """
        super().__init__(parent)
        self._log_manager = LogManager.get_instance()
        
        self._hotkey_manager = HotkeyManager.get_instance()
        self._modified_hotkeys = copy.deepcopy(ConfigManager.get_instance().get_value('system_hotkeys'))

        # UI variables
        self._autostart_checkbox = None
        self._service_status_label = None
        self._settings_hotkey_widget = None
        self._chat_hotkey_widget = None

        # Create UI components
        try:
            self._create_widgets()
            if ConfigManager.get_instance().get_value('general_config.autostart'):
                self._autostart_checkbox.setChecked(True)
            self._log_manager.log_info("General tab initialized.")
        except Exception as e:
            self._log_manager.log_error(f"Failed to create general tab widgets: {e}")
            raise
        self._log_manager.log_info("General tab initialized")

    def _create_widgets(self):
        """
        Create all widgets for general settings
        """
        try:
            layout = QVBoxLayout()

            # Autostart Section
            autostart_group = QGroupBox("Startup Settings")
            autostart_layout = QVBoxLayout()
            self._autostart_checkbox = QCheckBox("Start hotkey listener with Windows")
            autostart_layout.addWidget(self._autostart_checkbox)
            autostart_group.setLayout(autostart_layout)
            layout.addWidget(autostart_group)

            # System Hotkeys Section
            hotkeys_group = QGroupBox("System Hotkeys")
            hotkeys_layout = QGridLayout()

            # Chat Window Hotkey
            hotkeys_layout.addWidget(QLabel("Chat Window:"), 0, 0)
            self._chat_hotkey_widget = HotkeyInputWidget(self)
            self._chat_hotkey_widget.set_hotkey(self._modified_hotkeys['chat_window'].hotkey)
            hotkeys_layout.addWidget(self._chat_hotkey_widget, 0, 1)
            
            self._chat_enabled_checkbox = QCheckBox("Enabled")
            self._chat_enabled_checkbox.setChecked(self._modified_hotkeys['chat_window'].hotkey_enabled)
            self._chat_enabled_checkbox.stateChanged.connect(
                lambda state: self._update_hotkey_state("chat_window", state)
            )
            hotkeys_layout.addWidget(self._chat_enabled_checkbox, 0, 2)

            # Settings Window Hotkey
            hotkeys_layout.addWidget(QLabel("Settings Window:"), 1, 0)
            self._settings_hotkey_widget = HotkeyInputWidget(self)
            self._settings_hotkey_widget.set_hotkey(self._modified_hotkeys['settings_window'].hotkey)
            hotkeys_layout.addWidget(self._settings_hotkey_widget, 1, 1)

            self._settings_enabled_checkbox = QCheckBox("Enabled")
            self._settings_enabled_checkbox.setChecked(self._modified_hotkeys['settings_window'].hotkey_enabled)
            self._settings_enabled_checkbox.stateChanged.connect(
                lambda state: self._update_hotkey_state("settings_window", state)
            )
            hotkeys_layout.addWidget(self._settings_enabled_checkbox, 1, 2)

            # Promp Selector Hotkey
            hotkeys_layout.addWidget(QLabel("Prompt Selector:"), 2, 0)
            self._prompt_selector_hotkey_widget = HotkeyInputWidget(self)
            self._prompt_selector_hotkey_widget.set_hotkey(self._modified_hotkeys['prompt_selector'].hotkey)
            hotkeys_layout.addWidget(self._prompt_selector_hotkey_widget, 2, 1)

            self._prompt_selector_enabled_checkbox = QCheckBox("Enabled")
            self._prompt_selector_enabled_checkbox.setChecked(self._modified_hotkeys['prompt_selector'].hotkey_enabled)
            self._prompt_selector_enabled_checkbox.stateChanged.connect(
                lambda state: self._update_hotkey_state("prompt_selector", state)
            )
            hotkeys_layout.addWidget(self._prompt_selector_enabled_checkbox, 2, 2)

            hotkeys_group.setLayout(hotkeys_layout)
            layout.addWidget(hotkeys_group)

            # Service Status Section
            status_group = QGroupBox("Hotkey Listener Status")
            status_layout = QVBoxLayout()
            
            self._service_status_label = QLabel("Checking...")
            status_layout.addWidget(self._service_status_label)
            
            status_group.setLayout(status_layout)
            layout.addWidget(status_group)

            layout.addStretch()  # Push everything to the top
            self.setLayout(layout)

            self._log_manager.log_info("General tab widgets created")          
        except Exception as e:
            self._log_manager.log_error(f"Failed to create general tab widgets", error = e)
            raise

    def _update_hotkey_state(self, window_type: str, state: int):
        """
        Update the enabled state of a specific hotkey
        """
        is_enabled = state == Qt.Checked
        self._modified_hotkeys[window_type].hotkey_enabled = is_enabled

    def get_config(self) -> dict:
        """
        Get current configuration from widgets
        """
        return {
            'autostart': self._autostart_checkbox.isChecked(),
            'system_hotkeys': self._modified_hotkeys
        }

    def update_service_status(self, is_running: bool):
        """
        Update hotkey listener status
        """
        # Update the UI or internal state based on is_running
        status = "Running" if is_running else "Stopped"
        self._service_status_label.setText(f"Status: {status}")

    def is_hotkey_listener_running(self) -> bool:
        """
        Returns:
            True if hotkey listener is active, False otherwise
        """
        return self._service_status_label.text() == "Status: Running"
        
    def save_hotkeys(self):
        """
        Save system hotkeys
        """
        self._modified_hotkeys['settings_window'].hotkey = self._settings_hotkey_widget.get_hotkey()
        self._modified_hotkeys['settings_window'].hotkey_enabled = self._settings_enabled_checkbox.isChecked()
        self._modified_hotkeys['chat_window'].hotkey = self._chat_hotkey_widget.get_hotkey()
        self._modified_hotkeys['chat_window'].hotkey_enabled = self._chat_enabled_checkbox.isChecked()
        self._modified_hotkeys['prompt_selector'].hotkey = self._prompt_selector_hotkey_widget.get_hotkey()
        self._modified_hotkeys['prompt_selector'].hotkey_enabled = self._prompt_selector_enabled_checkbox.isChecked()