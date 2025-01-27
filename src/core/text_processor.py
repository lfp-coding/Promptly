import ctypes
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtGui import QFont
from typing import Optional


import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.core.clipboard_manager import ClipboardManager
from src.utils.prompt_manager import PromptManager, Prompt
from src.utils.chat_history import ChatHistory
from src.utils.log_manager import LogManager
from src.utils.ipc_command_handler import send_ipc_command
from src.utils.config_manager import ConfigManager

class TextProcessor:
    """Class responsible for all text processing operations"""
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = TextProcessor()
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._log_manager = LogManager.get_instance()
        
        # Initialize required managers
        self._config_manager = ConfigManager.get_instance()
        self._clipboard_manager = ClipboardManager.get_instance()
        self._api_client = self._config_manager.get_api_client()
        self._prompt_manager = PromptManager.get_instance()
        
        self._log_manager.log_info("TextProcessor initialized")

    def create_input_dialog(self):
        # Create the input dialog
        self._user_input = QInputDialog()
        self._user_input.setWindowTitle("Additional Input")
        self._user_input.setLabelText("Please enter your input:")
        # Set a larger font for the dialog
        font = QFont()
        font.setPointSize(11)  # Adjust the size as needed
        self._user_input.setFont(font)
        # Ensure the dialog is modal and brought to the foreground
        self._user_input.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint)

    def _set_busy_cursor(self):
        # Set the system-wide busy cursor (IDC_WAIT)
        ctypes.windll.user32.SetSystemCursor(ctypes.windll.user32.LoadCursorW(None, 32514), 32512)  # IDC_WAIT = 32514, OCR_NORMAL = 32512

    def _restore_default_cursor(self):
        # Restore the default system cursor
        ctypes.windll.user32.SystemParametersInfoW(0x0057, 0, None, 0)  # SPI_SETCURSORS = 0x0057

    def process_text_with_prompt(self, prompt_id: str):
        """
        Process selected text with a specific prompt
        
        Args:
            prompt_id: ID of the prompt to use
        """
        try:
            # Get the prompt
            prompt = self._prompt_manager.get_prompt_by_id(prompt_id)
            
            if not prompt:
                self._log_manager.log_error(f"Prompt not found: {prompt_id}")
                return False

            # Handle Chat history
            if prompt.behavior.clear_history:
                ChatHistory.get_instance().clear_history()
            
            # Get selected text
            selected_text = self._clipboard_manager.get_selected_text()
            
            # Handle text selection based on prompt behavior
            if selected_text and prompt.behavior.text_selected.value == 'skip':
                return True
            
            # Handle no selection based on prompt behavior
            if not selected_text:
                if prompt.behavior.no_text_selected.value == 'skip':
                    return True
                elif prompt.behavior.no_text_selected.value == 'process':
                    pass
                elif prompt.behavior.no_text_selected.value == 'select_all':  
                    selected_text = self._clipboard_manager.select_all_text()

            # Process the text
            self._process_with_openai(prompt, selected_text)
        except Exception as e:
            self._log_manager.log_error(f"Failed to process text", error = e)

    def _process_with_openai(self, prompt: Prompt, text: str):
        """
        Process text with OpenAI API
        
        Args:
            prompt: The prompt to use
            text: The text to process
        """
        try:
            # Get additional input if needed
            additional_input = ""
            if prompt.behavior.additional_input == True:
                additional_input = self._get_user_input()
                if additional_input is None:
                    return
            # Process the prompt template
            final_prompt = self._process_prompt(
                prompt, text, additional_input
            )
            if not final_prompt:
                return

            self._set_busy_cursor()

            # Send to OpenAI
            response = self._api_client.send_request_non_stream(final_prompt)
            if not response:
                return

            self._restore_default_cursor()

            if prompt.behavior.output_on_separate_window == True:
                send_ipc_command('show-chat')
            else:
                self._clipboard_manager.replace_text(response)
            self._log_manager.log_info("Text processed successfully.")            
        except Exception as e:
            self._log_manager.log_error(f"Error processing with OpenAI", error = e)
        
    def _get_user_input(self) -> str:
        """
        Get additional input from user
        """
        self._user_input.activateWindow()
        self._user_input.raise_()
        self._user_input.setFocus()

        # Execute the dialog and get user input
        if self._user_input.exec_() == QInputDialog.Accepted:
            return self._user_input.textValue() or ""
        else:
            return None  
    
    def _process_prompt(self, prompt: Prompt, selected_text: str = "", additional_input: str = "") -> Optional[str]:
        """
        Process prompt with given text and additional input
        """
        try:
            # Build final template
            template = prompt.template
            if prompt.behavior.additional_input:
                template = template.replace('{input}', additional_input or "")
            return template.replace('{text}', selected_text or "")            
        except Exception as e:
            self._log_manager.log_error(f"Error processing prompt", error = e)