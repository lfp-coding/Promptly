import argparse
import signal
import socket
import sys
import threading
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal, QPoint, Qt, QByteArray
from PyQt5.QtGui import QCursor, QIcon, QFont, QPixmap
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog, QSystemTrayIcon, QMenu, QAction, \
    QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton
from pynput import mouse, keyboard



root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))
from src.core.hotkey_manager import HotkeyManager
from src.utils.log_manager import LogManager
from src.utils.process_singleton import ProcessSingleton
from src.ui.config_window import ConfigWindow
from src.ui.chat_window import ChatWindow
from src.ui.prompt_selector_window import PromptSelector
from src.utils.path_manager import get_assets_path, get_config_path, get_base_path
from src.clients.gemini_api_client import GeminiClient
from src.utils.cleanup_manager import CleanupManager
from src.utils.credential_manager import CredentialManager

from src.utils.ipc_command_handler import send_ipc_command
from src.utils.helper_methods import HelperMethods
from src.core.text_processor import TextProcessor
from src.core.clipboard_manager import ClipboardManager

class SignalHelper(QObject):
    execute_command_signal = pyqtSignal(str)
    process_text_signal = pyqtSignal(str)

class HelperWindow(QDialog):
    def __init__(self, parent):
        super().__init__(parent = parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(1, 1)

class APIKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Gemini API Key")
        self.setModal(True)

        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Initialize layout
        layout = QVBoxLayout()

        # Instruction label
        instruction_label = QLabel("Please provide a valid Gemini API Key to continue:")
        font = QFont()
        font.setPointSize(11)  # Larger font size
        instruction_label.setFont(font)
        layout.addWidget(instruction_label)

        # Link for obtaining the API Key
        link_label = QLabel(
            '<a href="https://aistudio.google.com/app/apikey">Click here to get your Gemini API Key</a>'
        )
        link_label.setFont(font)
        link_label.setOpenExternalLinks(True)
        layout.addWidget(link_label)

        # Input for API key
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your API Key here")
        self.api_key_input.setFont(font)
        layout.addWidget(self.api_key_input)

        # Buttons for Validate and Cancel
        button_layout = QHBoxLayout()
        validate_button = QPushButton("Validate")
        validate_button.setFont(font)
        validate_button.clicked.connect(self.validate_api_key)
        cancel_button = QPushButton("Cancel")
        cancel_button.setFont(font)
        cancel_button.clicked.connect(self.reject)  # Close the dialog
        button_layout.addWidget(validate_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Set the main layout for the dialog
        self.setLayout(layout)

    def validate_api_key(self):
        """
        Method to validate the API key. Update this with your actual validation logic.
        """
        api_key = self.api_key_input.text().strip()

        if not api_key:
            QMessageBox.warning(self, "Validation Failed", "API Key cannot be empty!")
            return

        if GeminiClient.validate_api_key(api_key):
            CredentialManager.get_instance().store_api_key('gemini', api_key)
            QMessageBox.information(
                self, "Validation Successful", "The provided API Key is valid.\nContinuing..."
            )
            self.accept()  # Proceed and close the dialog
        else:
            QMessageBox.warning(
                self, "Validation Failed", "The provided API Key is invalid.\nPlease try again."
            )
            self.api_key_input.clear()  # Clear the input field for retry

class MainProcess:
    def __init__(self):
        """
        Initialize the main process
        """
        # Initialize LogManager first
        self._log_manager = LogManager.get_instance()
        self._log_manager.cleanup_old_logs()
        self._log_manager.log_info("Initializing Promptly service")
        self._hotkey_listener_running = False

        # Initialize QApplication

        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        # icon_path = get_assets_path() / 'Promptly.ico'
        self._app = QApplication(sys.argv)
        self._icon = HelperMethods.get_instance().get_icon()
        self._app.setApplicationName("Promptly")
        self._app.setWindowIcon(self._icon)
        self._ensure_valid_api_key()

        self._hotkey_manager = HotkeyManager.get_instance()
        self._clipboard_manager = ClipboardManager.get_instance()
        self._signal_helper = SignalHelper()
        self._signal_helper.execute_command_signal.connect(self._execute_command)
        self._signal_helper.process_text_signal.connect(self._process_text_in_main_thread)
        self._keep_running = False

        self._listeners = []

        try:        
            # Check for running instance
            self._process_singleton = ProcessSingleton.get_instance("main")
            if not self._process_singleton.acquire():
                self._log_manager.log_error("Another instance of Promptly is already running.")
                sys.exit(1)
            if getattr(sys, 'frozen', False):
                self.ensure_shortcuts_exist()

            # Initialize windows
            self._config_window = ConfigWindow(self.check_active_components)
            self._chat_window = ChatWindow(self.check_active_components)
            self._helper_window = HelperWindow(self._config_window)
            self._prompt_selector = PromptSelector()
            self._log_manager.log_info("Promptly initialization completed")
            # Start IPC server in a separate thread
            self._ipc_thread = threading.Thread(target=self._start_ipc_server, daemon=True)
            self._ipc_thread.start()
        except Exception as e:
            self._log_manager.log_error(f"Failed to initialize Promptly", error = e)
            self.cleanup()
            sys.exit(1)

    def ensure_shortcuts_exist(self):
        """
        Ensures that shortcuts to main.exe are created for each of the arguments in the main process.
        """
        base_path = get_base_path()
        main_exe_path = base_path / "Promptly.exe"
        icon_path = get_assets_path() / 'Promptly.ico'

        # List of arguments to create shortcuts for
        shortcut_args = [
            ("--show-chat", "Show Chat Window"),
            ("--start-listener", "Start Hotkey Listener"),
            ("--stop-listener", "Stop Hotkey Listener"),
            ("--cleanup", "Uninstall  Promptly"),
        ]

        # Iterate through the arguments and ensure a shortcut exists for each
        for arg, name in shortcut_args:
            shortcut_file = base_path / f"{name}.lnk"

            # If the shortcut does not exist, create it
            if not shortcut_file.exists():
                import winshell
                with winshell.shortcut(str(shortcut_file)) as shortcut:
                    shortcut.path = str(main_exe_path)
                    shortcut.arguments = arg
                    shortcut.working_directory = str(main_exe_path)
                    shortcut.description = f"Shortcut to run main.exe with argument {arg}"
                    shortcut.icon_location = (str(main_exe_path), 0)

    def _ensure_valid_api_key(self):
        """
        Ensures a valid Gemini API Key is available by:
        1) Checking the config file.
        2) Prompting the user to input a key if one is not available or invalid.
        Exits the application if a valid key is not provided.

        Raises:
            SystemExit: If no valid API key is provided.
        """

        config_path = get_config_path() / "config.json"
        api_key = None

        # Check if API key exists in configuration
        if config_path.exists():
            try:
                valid_api_key = False
                api_key = CredentialManager.get_instance().get_api_key('gemini')
                if GeminiClient.validate_api_key(api_key):
                    self._log_manager.log_info("Valid API key found.")
                    return
            except Exception as e:
                self._log_manager.log_error(f"Error validating API key: {e}")

        # Prompt for API key until it is valid or user cancels
        while True:
            dialog = APIKeyDialog(parent=None)  # Create the dialog
            result = dialog.exec_()  # Show the dialog modally

            if result == QDialog.Accepted:  # User successfully validated the key
                self._log_manager.log_info("API key input validated successfully.")
                break  # Exit the loop and proceed
            else:  # User canceled the dialog
                self._log_manager.log_error("User canceled API key input.")
                QMessageBox.critical(None, "Setup Failed", "A valid API Key is required to run this application.")
                self.cleanup()
                break
                # sys.exit(1)  # Exit the application

        self._log_manager.log_info("API key validation completed successfully.")

    def setup_tray_icon(self):
        # Create the tray icon
        icon_path = get_base_path() / "Promptly.exe"
        self.tray_icon = QSystemTrayIcon(self._icon, self._app)
        tray_menu = QMenu()

        # Add menu actions
        show_config_action = QAction("Show Config", self._app)
        show_config_action.triggered.connect(self.show_config_gui)
        tray_menu.addAction(show_config_action)

        show_chat_action = QAction("Show Chat", self._app)
        show_chat_action.triggered.connect(self.show_chat_window)
        tray_menu.addAction(show_chat_action)

        quit_action = QAction("Quit", self._app)
        quit_action.triggered.connect(self.cleanup)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("Promptly")
        self.tray_icon.show()

    def _start_ipc_server(self):
        """
        Start an IPC server to listen for commands
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind(("127.0.0.1", 65432))  # Bind to localhost and port 65432
            server_socket.listen()
            self._log_manager.log_info("IPC server listening on port 65432.")

            while True:
                conn, addr = server_socket.accept()
                threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()

    def _handle_client(self, conn):
        """
        Handle incoming IPC client connections
        """
        with conn:
            command = conn.recv(1024).decode("utf-8")
            self._log_manager.log_info(f"Received IPC command: {command}")
            self._signal_helper.execute_command_signal.emit(command)

    def _execute_command(self, command):
        if command == "show-config":
            self.show_config_gui()
        elif command == "show-chat":
            self.show_chat_window()
        elif command == "start-listener":
            self.start_hotkey_listener()
        elif command == "stop-listener":
            self.stop_hotkey_listener()
        elif command == "show-prompt_selector":
            self._keep_running = True
            self.stop_hotkey_listener()
            self.show_prompt_selector()
            self.start_hotkey_listener()
            self._keep_running = False

    def _setup_signal_handlers(self):
        """
        Setup handlers for graceful shutdown
        """
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        self._log_manager.log_info("Signal handlers registered")

    def _handle_shutdown(self, signum):
        """
        Handle shutdown gracefully
        """
        self._log_manager.log_info(f"Received signal {signum}, performing cleanup...")
        self.cleanup()
        sys.exit(0)

    def start_hotkey_listener(self):
        """
        Start hotkey listener
        """
        try:
            self._log_manager.log_info("Starting hotkey listener")
            TextProcessor.get_instance().create_input_dialog()
            self._hotkey_manager.start_listeners()
            self._hotkey_listener_running = True
            HelperMethods.get_instance().update(hotkey_listener_running=self._hotkey_listener_running)
            self._config_window._general_tab.update_service_status(self._hotkey_listener_running)
        except Exception as e:
            self._log_manager.log_error(f"Service error", error = e)

    def stop_hotkey_listener(self):
        """
        Stop hotkey listener
        """
        try:
            self._log_manager.log_info("Stopping hotkey listener")
            self._hotkey_manager.stop_listeners()
            self._hotkey_listener_running = False
            HelperMethods.get_instance().update(hotkey_listener_running=self._hotkey_listener_running)
            self._config_window._general_tab.update_service_status(self._hotkey_listener_running)
            self.check_active_components()
        except Exception as e:
            self._log_manager.log_error(f"Service error", error = e)

    def show_config_gui(self):
        """
        Bring the config GUI to focus
        """
        self._config_window.show()
        self._config_window._general_tab.update_service_status(self._hotkey_listener_running)

    def show_chat_window(self):
        """
        Bring the chat window to focus
        """
        self._chat_window.scroll_to_bottom()
        self._chat_window.show()

    def show_prompt_selector(self):
        """
        Show the PromptSelector window at the cursor's position
        """
        self._prompt_selector = None
        self._prompt_selector = PromptSelector()
        try:

            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_press,
                suppress=True
            )
            self._mouse_listener = mouse.Listener(
                on_click=self._on_click,
                on_move=self._on_move
            )

            self._keyboard_listener.start()
            self._mouse_listener.start()
            self._clipboard_manager.release_all_modifiers()
            pos = QCursor.pos()
            self._helper_window.move(pos)
            self._helper_window.show()
            # Get the text caret position (Windows-specific)
            self.pos = pos
            self.prompt_global_rect = self._prompt_selector.rect()  # Local rectangle
            self.prompt_global_rect.moveTo(self.pos)
            self._prompt_selector.move(pos)
            self._prompt_selector.show()
            self._helper_window.hide()


        except Exception as e:
            self._log_manager.log_error(f"Error showing prompt selector: {e}")

    def _on_press(self, key):
        self._prompt_selector.key_press(key)
        if not key == keyboard.Key.up and not key == keyboard.Key.down:
            action = None
            if key == keyboard.Key.enter:
                if self._prompt_selector.activeAction():
                    action = self._prompt_selector.activeAction().text() 
            self._stop_listeners()
            self._prompt_selector.hide()
            self._prompt_selector.deleteLater()
            if action is not None:
                self._signal_helper.process_text_signal.emit(action)

    def _on_move(self, x, y):
        """
        Callback for mouse movement. Clears selection in PromptSelector.
        """
        if self._prompt_selector:
            # Mouse position on screen
            current_position = QPoint(x, y)

            # Get the global position and size of the PromptSelector
            prompt_global_rect = self._prompt_selector.rect()  # Local rectangle
            prompt_global_rect.moveTo(self.pos)  # Convert to global position

            # Check if the mouse is outside the globally mapped PromptSelector rectangle
            if not self.prompt_global_rect.contains(current_position):
                self._prompt_selector.setActiveAction(None)


    def _on_click(self, x, y, button, pressed):
        if not pressed:  
            return
        action = None

        if self._prompt_selector.activeAction():
            action = self._prompt_selector.activeAction().text()   
        self._stop_listeners()
        self._prompt_selector.deleteLater()
        if action is not None:
            self._signal_helper.process_text_signal.emit(action)

    def _stop_listeners(self):
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

    def _process_text_in_main_thread(self, action):
        """Process text with prompt in the main thread."""
        try:
            TextProcessor.get_instance().process_text_with_prompt(action)
        except Exception as e:
            self._log_manager.log_error(f"Error processing text in main thread: {e}")

    def check_active_components(self):
        """
        Check if any components are active
        """
        config_active = hasattr(self, '_config_window') and not (self._config_window.isHidden())
        chat_active = hasattr(self, '_chat_window') and not (self._chat_window.isHidden())
        
        if not (config_active or chat_active or self._hotkey_listener_running or self._keep_running):
            self.cleanup()
            sys.exit(0)

    def cleanup(self):
        """
        Clean up resources
        """
        try:
            self._log_manager.log_info("Cleaning up resources...")
            if self._hotkey_listener_running:
                self._hotkey_manager.stop_listeners()

            if hasattr(self, '_clipboard_manager'):
                self._clipboard_manager.release_all_modifiers()

            if hasattr(self, '_process_singleton'):
                self._process_singleton.release()  

            QApplication.quit()  # Gracefully exit QApplication
            sys.exit(0)

        except Exception as e:
            self._log_manager.log_error(f"Cleanup error", error = e)

def main():
    """
    Main entry point for the program
    """
    process = None
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Promptly Main Process")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--show-config", action="store_true", help="Show the configuration window")
    group.add_argument("--show-chat", action="store_true", help="Show the chat window")
    group.add_argument("--start-listener", action="store_true", help="Start the hotkey listener")
    group.add_argument("--stop-listener", action="store_true", help="Stop the hotkey listener")
    group.add_argument("--cleanup", action="store_true", help="Erase all program data")
    args = parser.parse_args()


    try:
        if args.show_config:
            if not send_ipc_command('show-config'):
                process = MainProcess()
                process.show_config_gui()
        elif args.show_chat:
            if not send_ipc_command('show-chat'):
                process = MainProcess()
                process.show_chat_window()
        elif args.start_listener:
            if not send_ipc_command('start-listener'):
                process = MainProcess()
                process.start_hotkey_listener()
        elif args.stop_listener:
            send_ipc_command('stop-listener')
        elif args.cleanup:
            app = QApplication(sys.argv)
            # Ensure no other instance is running
            process_singleton = ProcessSingleton.get_instance("main")
            if process_singleton.is_running():
                QMessageBox.critical(None, "Error", "Cannot perform cleanup while another instance is running.")
                sys.exit(1)

            # Perform cleanup
            cleanup_manager = CleanupManager(parent=None)
            cleanup_manager.perform_cleanup()
            sys.exit(0)
        else:
            # Default behavior here, e.g., starting a listener or showing configuration
            if not send_ipc_command('show-config'):
                process = MainProcess()
                process.show_config_gui()  # Replace with any desired default behavior

        # Start PyQt event loop
        if process is None:
            sys.exit(0)
        process.setup_tray_icon()
        sys.exit(process._app.exec_())    
    except SystemExit as se:
        LogManager.get_instance().log_error(f"SystemExit occurred: {se}")
        raise  # Re-raise if you want to terminate

    except Exception as e:
        LogManager.get_instance().log_error(f"Unhandled exception in main process", error=e)
        process.cleanup()

if __name__ == "__main__":
    main()