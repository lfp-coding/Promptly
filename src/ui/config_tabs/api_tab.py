from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QGroupBox, QMessageBox, QComboBox
)
import copy

import sys
from pathlib import Path

from src.clients.gemini_api_client import GeminiClient

root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))
from src.utils.credential_manager import CredentialManager
from src.utils.config_manager import ConfigManager
from src.utils.log_manager import LogManager

class APITab(QWidget):
    def __init__(self, parent=None):
        """
        Initialize API settings tab
        """
        super().__init__(parent)
        self._log_manager = LogManager.get_instance()
        self._credential_manager = CredentialManager.get_instance()
        self._config_manager = ConfigManager.get_instance()
        self._api_client = self._config_manager.get_api_client()
        self._api_clients = copy.deepcopy(self._config_manager.get_value('api_clients'))

        # Initialize UI variables
        self._api_key_input = None
        self._show_key_checkbox = None
        self._model_combo = None
        self._api_key_old = None

        # Create UI components
        try:
            self._create_widgets()
            self._load_config()
            self._log_manager.log_info("API tab initialized.")
        except Exception as e:
            self._log_manager.log_error(f"Failed to create API tab widgets: {e}")
            raise
        
        self._log_manager.log_info("API tab initialized")

    def _create_widgets(self):
        """
        Create all widgets for API settings
        """
        try:
            layout = QVBoxLayout()

            # API Key Section
            api_key_group = QGroupBox("OpenAI API Settings")
            api_key_layout = QVBoxLayout()

            api_key_label = QLabel("API Key:")
            self._api_key_input = QLineEdit()
            self._api_key_input.setEchoMode(QLineEdit.Password)  # Hide API key by default

            # Show/Hide API Key Checkbox
            self._show_key_checkbox = QCheckBox("Show API Key")
            self._show_key_checkbox.stateChanged.connect(self._toggle_api_key_visibility)

            # Buttons for Testing and Deleting API Key
            button_layout = QHBoxLayout()
            test_button = QPushButton("Test API Key")
            test_button.clicked.connect(self._test_api_key)
            
            delete_button = QPushButton("Delete API Key")
            delete_button.clicked.connect(self._delete_api_key)

            button_layout.addWidget(test_button)
            button_layout.addWidget(delete_button)

            # Add widgets to API Key section layout
            api_key_layout.addWidget(api_key_label)
            api_key_layout.addWidget(self._api_key_input)
            api_key_layout.addWidget(self._show_key_checkbox)
            api_key_layout.addLayout(button_layout)
            
            api_key_group.setLayout(api_key_layout)
            
            # Model Selection Section
            model_group = QGroupBox("Model Settings")
            model_layout = QHBoxLayout()

            model_label = QLabel("Model:")
            
            self._model_combo = QComboBox()
            self._model_combo.setEditable(False)  # Read-only dropdown

            model_layout.addWidget(model_label)
            model_layout.addWidget(self._model_combo)
            
            model_group.setLayout(model_layout)

            # Add groups to main layout
            layout.addWidget(api_key_group)
            layout.addWidget(model_group)
            
            layout.addStretch()  # Push everything to the top
            self.setLayout(layout)
            
            self._log_manager.log_info("API tab widgets created")
        except Exception as e:
            self._log_manager.log_error(f"Failed to create API tab widgets", error = e)
            raise

    def _toggle_api_key_visibility(self, entry):
        """
        Toggle API key visibility
        """
        if self._show_key_checkbox.isChecked():
            self._api_key_input.setEchoMode(QLineEdit.Normal)  # Show API key
        else:
            self._api_key_input.setEchoMode(QLineEdit.Password)  # Hide API key

    def _test_api_key(self):
        """
        Test the current API key
        """
        try:
            api_key = self._api_key_input.text().strip()
            if GeminiClient.validate_api_key(api_key):
                QMessageBox.information(self, "Validate API Key", "API Key is valid.")
            else:
                QMessageBox.warning(self, "Validate API Key", "API Key is NOT valid.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to validate API key: {e}")
       
    def _delete_api_key(self):
        """
        Clear the API key
        """
        confirm = QMessageBox.question(
            self,
            "Delete API Key",
            "Are you sure you want to delete the API key?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self._api_key_input.clear()

    def _load_config(self):
        """
        Load configuration into widgets
        """
        try:
            api_key = self._credential_manager.get_api_key(self._api_client.name)
            model = self._api_clients[self._api_client.name].model

            if api_key:
                self._api_key_input.setText(api_key)
                self._api_key_old = api_key

            if self._api_client.name == 'openai':
                available_models = [
                    model for model in self._api_client.get_available_models()
                    if "gpt" in model or "o1" in model
                ]
            elif self._api_client.name == 'gemini':
                available_models = [
                    model for model in self._api_client.get_available_models()
                ]
            
            if available_models:
                self._model_combo.addItems(available_models)
            
            if model in available_models:
                self._model_combo.setCurrentText(model)

            self._log_manager.log_info("API tab configuration loaded")
        except Exception as e:
            self._log_manager.log_error(f"Failed to load API tab configuration", error = e)
            raise

    def get_config(self) -> dict:
        """
        Get current configuration from widgets
        """
        current_api_key = self._api_key_input.text().strip()
        if self._api_key_old == current_api_key:
            api_key_encr = self._api_clients[self._api_client.name].api_key_encrypted
        elif current_api_key == "":
            api_key_encr = ""
        else:
            api_key_encr = self._credential_manager.get_encrypted_key(current_api_key)
        self._api_key_old = current_api_key
        self._api_clients[self._api_client.name].api_key_encrypted = api_key_encr
        self._api_clients[self._api_client.name].model = self._model_combo.currentText()

        return self._api_clients