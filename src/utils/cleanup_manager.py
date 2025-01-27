import winreg
from PyQt5.QtWidgets import QMessageBox

import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.utils.credential_manager import CredentialManager
from src.utils.process_singleton import ProcessSingleton
from src.utils.log_manager import LogManager
from src.utils.path_manager import get_base_path

class CleanupManager:
    def __init__(self, parent=None):
        self.parent = parent  # For QMessageBox dialogs

    def remove_autostart_entry(self):
        try:
            key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0,
                                winreg.KEY_ALL_ACCESS) as key:
                try:
                    winreg.DeleteValue(key, "Promptly - Textprocessor")
                except FileNotFoundError:
                    pass
        except Exception as e:
            self._show_error(f"Failed to remove autostart entry: {e}")

    def remove_lock_file(self):
        try:
            ProcessSingleton.get_instance("main").release()
        except Exception as e:
            self._show_error(f"Failed to remove ProcessSingleton files: {e}")

    def clear_windows_credentials(self):
        try:
            CredentialManager.get_instance().delete_credentials()
        except Exception as e:
            self._show_error(f"Failed to clear Windows credentials: {e}")

    def delete_log_directory(self):
        try:
            LogManager.get_instance().delete_log_dir()
        except Exception as e:
            self._show_error(f"Failed to delete log directory: {e}")

    def delete_shortcuts(self):
        """
        Deletes the shortcuts created for Promptly.
        """
        try:
            base_path = get_base_path()

            # List of shortcut names corresponding to the arguments
            shortcut_args = [
                "Show Chat Window",
                "Start Hotkey Listener",
                "Stop Hotkey Listener",
                "Uninstall  Promptly",
            ]

            # Delete each shortcut
            for name in shortcut_args:
                shortcut_file = base_path / f"{name}.lnk"

                # Check if the shortcut exists and delete it
                if shortcut_file.exists():
                    shortcut_file.unlink()  # Deletes the shortcut file

        except Exception as e:
            self._show_error(f"Failed to delete shortcuts: {e}")

    def perform_cleanup(self):
        reply = QMessageBox.question(
            self.parent,
            "Confirm Cleanup",
            "This will erase log files, autostart configuration, API keys stored in Windows credentials, and shortcuts. Are you sure you want to proceed? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.remove_autostart_entry()
            self.remove_lock_file()
            self.clear_windows_credentials()
            self.delete_shortcuts()
            self.delete_log_directory()
            QMessageBox.information(self.parent, "Cleanup Completed", "All program data has been erased.")
        else:
            QMessageBox.information(self.parent, "Cleanup Canceled", "No changes were made.")

    def _show_error(self, message):
        QMessageBox.critical(self.parent, "Error", message)
