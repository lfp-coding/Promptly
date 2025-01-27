from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QMessageBox
from PyQt5.QtCore import QSettings, QSize, QPoint
from PyQt5.QtGui import QFont, QIcon
import winreg
import sys
import copy
import hashlib
import json
from typing import Dict

from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.ui.config_tabs.general_tab import GeneralTab
from src.ui.config_tabs.api_tab import APITab
from src.ui.config_tabs.prompts_tab import PromptsTab
from src.utils.path_manager import get_base_path
from src.utils.config_manager import ConfigManager
from src.utils.credential_manager import CredentialManager
from src.utils.prompt_manager import PromptManager
from src.utils.log_manager import LogManager
from src.utils.ipc_command_handler import send_ipc_command
from src.core.hotkey_manager import HotkeyManager
from src.utils.path_manager import get_assets_path

class ConfigWindow(QMainWindow):
    def __init__(self, on_window_close_callback=None):
        """
        Initialize ConfigWindow to manage application settings
        """
        try:
            super().__init__()
            # Initialize managers
            self._log_manager = LogManager.get_instance()
            self._config_manager = ConfigManager.get_instance()
            self._credential_manager = CredentialManager.get_instance()
            self._on_window_close_callback = on_window_close_callback
            
            self._log_manager.log_info("Initializing Config Window")
            
            self._initialize_ui()
            self._restore_window_geometry()
            self._adjust_font_sizes()

            # icon_path = get_assets_path() / 'Promptly.ico'
            # self.setWindowIcon(QIcon(str(icon_path)))
            
            # Track changes
            self._config_new = copy.deepcopy(self._config_manager.get_value('config'))
        except Exception as e:
            self._log_manager.log_error(f"Failed to initialize settings window", error = e)
            raise
        
    def _initialize_ui(self):
        """
        Create the main configuration window
        """
        try:
            self.setWindowTitle("Promptly - Settings")
            self.setMinimumSize(800, 620)
            
            # Initialize tabs
            self._tab_widget = QTabWidget()
            self._general_tab = GeneralTab(self)
            self._api_tab = APITab(self)
            self._prompts_tab = PromptsTab(self)

            # Add tabs to tab widget
            self._tab_widget.addTab(self._general_tab, "General")
            self._tab_widget.addTab(self._api_tab, "API Settings")
            self._tab_widget.addTab(self._prompts_tab, "Prompts")

            # Control buttons
            self._start_button = QPushButton("Start hotkey listener")
            self._start_button.clicked.connect(self._start_service)
            self._stop_button = QPushButton("Stop hotkey listener")
            self._stop_button.clicked.connect(self._stop_service)
            self._save_button = QPushButton("Save")
            self._save_button.clicked.connect(self._save_changes)
            self._exit_button = QPushButton("Exit")
            self._exit_button.clicked.connect(self.close)

            button_layout = QHBoxLayout()
            button_layout.addWidget(self._start_button)
            button_layout.addWidget(self._stop_button)
            button_layout.addWidget(self._save_button)
            button_layout.addWidget(self._exit_button)

            # Main layout
            main_layout = QVBoxLayout()
            main_layout.addWidget(self._tab_widget)
            main_layout.addLayout(button_layout)

            central_widget = QWidget()
            central_widget.setLayout(main_layout)
            self.setCentralWidget(central_widget)

            # Apply a smaller font size to all buttons
            buttons = [self._start_button, self._stop_button, self._save_button, self._exit_button]
            for button in buttons:
                current_font = button.font()
                smaller_font = QFont(current_font.family(), max(1, current_font.pointSize() - 1))  # Ensure font size doesn't go below 1
                button.setFont(smaller_font)
            
            self._log_manager.log_info("Config Window initialized")
        except Exception as e:
            self._log_manager.log_error(f"Failed to initialize settings ui", error = e)
            raise

    def _adjust_font_sizes(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        scaling_factor = screen_geometry.width() / 1920
        default_font_size = max(10, int(11 * scaling_factor))
        
        # Apply font globally or to specific widgets
        global_font = QFont("Arial", default_font_size)
        self.setFont(global_font)

        button_font = QFont("Arial", default_font_size - 1)
        body_font = QFont("Arial", default_font_size - 1)
        heading_font = QFont("Arial", default_font_size - 1)

        font_mapping = {
            "QPushButton": button_font,
            "QLabel": body_font,
            "QTabWidget": heading_font
        }

        # Traverse all child widgets
        for widget in self.findChildren(QWidget):
            widget_type = widget.metaObject().className()
            if widget_type in font_mapping:
                widget.setFont(font_mapping[widget_type])

    def _check_unsaved_changes(self) -> bool:
        if not self._get_configs():
            raise ValueError("Failed to retrieve configurations.")

        original_hash = self._calculate_config_hash(self._config_manager.get_value('config'))
        new_hash = self._calculate_config_hash(self._config_new)

        return new_hash != original_hash

    def _save_changes(self) -> bool:
        """
        Save all changes from all tabs
        """
        try:
            if self._check_unsaved_changes():
                hotkey_conflicts = self._validate_new_config()
                
                if hotkey_conflicts:
                    conflict_text = f"Settings could not be saved. Please resolve the following hotkey conflicts:\n\n"
                    for key, items in hotkey_conflicts.items():
                        conflict_text += f"{key}:\n"
                        for item in items:
                            conflict_text += f"  {item}\n"
                    QMessageBox.warning(self, "Hotkey conflict", conflict_text)
                    return

                if self._config_manager.get_value('config').general_config.autostart != self._config_new.general_config.autostart:
                    self._configure_autostart(self._config_new.general_config.autostart)

                self._config_manager.set_value('config', self._config_new)
                HotkeyManager.get_instance().load_hotkeys()
                PromptManager.get_instance().load_prompts()

                QMessageBox.information(self, "Success", "Settings saved successfully")
                                
                self._log_manager.log_info("Changes saved successfully.")
                return True
            else:
                QMessageBox.information(self, "Success", "No changed settings")
        except ValueError:
            return
        except Exception as e:
            self._log_manager.log_error(f"Failed to save changes", error = e)
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def _calculate_config_hash(self, config):
        """
        Calculate a hash for the given configuration dictionary.

        Args:
            config (dict): The configuration dictionary.

        Returns:
            str: The SHA256 hash of the serialized configuration.
        """
        # Serialize the config to JSON, ensuring consistent ordering
        serialized_config = json.dumps(config.to_dict(), sort_keys=False)
        return hashlib.sha256(serialized_config.encode()).hexdigest()

    def closeEvent(self, event):
        """
        Handle window closing
        """
        try:
            if self._check_unsaved_changes():
                result = QMessageBox.question(
                    self,
                    "Save Changes",
                    "There are unsaved changes. Save before closing?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                )
                if result == QMessageBox.Cancel:
                    event.ignore()
                    return
                elif result == QMessageBox.Yes:
                    if not self._save_changes():
                        event.ignore()
                        return
            
            # Save geometry on close
            self._save_window_geometry()

            self._log_manager.log_info("Chat window closing")
            self.hide()  # Hide the window instead of destroying it
            event.ignore()
            if self._on_window_close_callback:
                self._on_window_close_callback()
        except ValueError:
            event.ignore()
        except Exception as e:
            self._log_manager.log_error(f"Error during window closing: {e}")

    def _save_window_geometry(self):
        """
        Save window size and position
        """
        settings = QSettings("Promptly - Textprocessor", "Settings Window")
        settings.setValue("pos", self.pos())
        settings.setValue("size", self.size())

    def _restore_window_geometry(self):
        """
        Restore window size and position
        """
        settings = QSettings("Promptly - Textprocessor", "Settings Window")
        self.move(settings.value("pos", QPoint(100, 100)))  # Default position if none saved
        self.resize(settings.value("size", QSize(800, 620)))  # Default size if none saved

    def _configure_autostart(self, enable: bool):
        """
        Configure autostart in Windows registry
        """
        try:
            key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
            if getattr(sys, 'frozen', False):
                app_path = get_base_path() / 'Promptly.exe'
            else:
                app_path = get_base_path() / 'src' / 'main.py'
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, 
                              winreg.KEY_ALL_ACCESS) as key:
                if enable:
                    winreg.SetValueEx(key, "Promptly - Textprocessor", 0,
                                    winreg.REG_SZ, f'"{sys.executable}" --start-listener')
                else:
                    try:
                        winreg.DeleteValue(key, "Promptly - Textprocessor")
                    except FileNotFoundError:
                        pass
                        
            self._log_manager.log_info(f"Autostart {'enabled' if enable else 'disabled'}")
        except Exception as e:
            self._log_manager.log_error(f"Failed to configure autostart", error = e)
            raise

    def _start_service(self):
        """
        Start the main service
        """
        send_ipc_command('start-listener')

    def _stop_service(self):
        """
        Stop the main service using ProcessSingleton.
        """
        send_ipc_command('stop-listener')
        
    def _on_closing(self):
        """
        Handle window closing
        """
        try:
            if self._check_unsaved_changes():
                result = QMessageBox.question(
                    self,
                    "Save Changes",
                    "There are unsaved changes. Save before closing?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                )
                if result == QMessageBox.Cancel:
                    return
                elif result == QMessageBox.Yes:
                    self._save_changes()
            
            self._log_manager.log_info("Chat window closing")
            self.hide()  # Hide the window instead of destroying it
            if self._on_window_close_callback:
                self._on_window_close_callback()
        except ValueError:
            return
        except Exception as e:
            self._log_manager.log_error(f"Error during window closing: {e}")

    def _get_configs(self) -> bool:
        """
        Get Configs from Tabs
        """
        if not self._prompts_tab.save_current_prompt():
            return False
        self._general_tab.save_hotkeys()

        self._config_new.general_config.autostart = self._general_tab.get_config()['autostart']
        self._config_new.api_clients = self._api_tab.get_config()
        self._config_new.prompts = self._prompts_tab.get_config()
        self._config_new.system_hotkeys = self._general_tab.get_config()['system_hotkeys']

        return True

    def show(self):
        """
        Show the settings window
        """
        try:
            # If the window is hidden or not created, show it
            self.showNormal()
            self.raise_()  # Bring the window to the front
            self.activateWindow()  # Focus on the window

            # Log that the settings window is being shown
            self._log_manager.log_info("Settings window shown.")
        except Exception as e:
            self._log_manager.log_error(f"Failed to show settings window: {e}")

    def _validate_new_config(self) -> Dict:
        """
        Validate new config
        Returns:
            Dict of Hotkeys with the conflicting Ids
        """
        hotkey_conflicts = {}
        for key, value in self._config_new.system_hotkeys.items():
            if value.hotkey_enabled == False: continue
            if value.hotkey not in hotkey_conflicts:
                hotkey_conflicts[value.hotkey] = []
            hotkey_conflicts[value.hotkey].append(key)
        for key, value in self._config_new.prompts.items():
            if value.hotkey_enabled == False: continue
            if value.hotkey not in hotkey_conflicts:
                hotkey_conflicts[value.hotkey] = []
            hotkey_conflicts[value.hotkey].append(key)

        # Filter out hotkeys with only one entry (no conflict)
        hotkey_conflicts = {hotkey: ids for hotkey, ids in hotkey_conflicts.items() if len(ids) > 1}

        return hotkey_conflicts