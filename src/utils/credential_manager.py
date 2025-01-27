import keyring
from cryptography.fernet import Fernet

import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.utils.config_manager import ConfigManager
from src.utils.log_manager import LogManager
from src.utils.dataclasses import APIClient

class CredentialManager:
    """Class to manage API credentials using Windows Credential Manager"""
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = CredentialManager()
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._log_manager = LogManager.get_instance()
        self._config_manager = ConfigManager.get_instance()

        self._initialize_encryption()
        self._log_manager.log_info("Credential Manager initialized")

    def _initialize_encryption(self):
        """
        Initialize encryption for sensitive data
        """
        try:
            # Try to get existing key
            stored_key = keyring.get_password("Promptly - Textprocessor", "encryption_key")
            if stored_key:
                self._encryption_key = stored_key.encode()
            else:
                # Generate new key if none exists
                self._encryption_key = Fernet.generate_key()
                # Store as string
                keyring.set_password("Promptly - Textprocessor", "encryption_key",
                                   self._encryption_key.decode())
        
            # Create Fernet-Instance for De-/Encryption
            self._cipher_suite = Fernet(self._encryption_key)
            self._log_manager.log_info("Encryption initialized successfully")

        except Exception as e:
            self._log_manager.log_error(f"Failed to initialize encryption", error = e)
            raise

    def get_encrypted_key(self, api_key: str):
        """
        Return the encrypted api key
        """
        return self._cipher_suite.encrypt(api_key.encode()).decode()

    def store_api_key(self, api_provider: str, api_key: str):
        """
        Save encrypted API key
        
        Args:
            api_key: The API key to store
        """
        try:
            if api_provider == 'openai':
                model = 'gpt-4o'
            elif api_provider == 'gemini':
                model = 'gemini-1.5-flash'

            api_client = APIClient(
                api_key_encrypted=self._cipher_suite.encrypt(api_key.encode()).decode(),
                model=model,
                temperature=None,
                max_tokens=None,
                timeout=None
            )
            api_clients = self._config_manager.get_value('api_clients')
            api_clients[api_provider] = api_client
            self._config_manager.set_value('api_clients', api_clients)
            self._config_manager.set_value('general_config.api_provider', api_provider)
            self._log_manager.log_info("API key saved successfully")
        except Exception as e:
            self._log_manager.log_error(f"Failed to save API key", error = e)
            raise

    def get_api_key(self, api_provider) -> str:
        """
        Get decrypted API key
        
        Returns:
            str: The stored API key or empty string if not found
        """
        try:
            api_clients = self._config_manager.get_value("api_clients")
            if api_provider not in api_clients or not api_clients[api_provider].api_key_encrypted:
                self._log_manager.log_warning(f"No API key found for provider: {api_provider}")
                return ""
            api_key = api_clients[api_provider].api_key_encrypted
            return self._cipher_suite.decrypt(api_key).decode()
        except Exception as e:
            self._log_manager.log_error(f"Failed to get API key", error = e)
            raise

    def delete_api_key(self):
        """
        Delete the stored API key
        
        Returns:
            bool: True if successful or no key existed, False if deletion failed
        """
        try:
            self._config_manager.set_value("general_config.api_key_encrypted", "")
            self._log_manager.log_.info("API key deleted successfully")
            
        except Exception as e:
            self._log_manager.log_error(f"Failed to delete API key", error = e)

    def validate_api_key(self, api_key: str) -> tuple[bool, str]:
        """
        Validate API key format
        
        Args:
            api_key: The API key to validate
            
        Returns:
            tuple[bool, str]: (True, '') if valid format, (False, error_message) otherwise
        """
        try:
            if not api_key:
                return False, "API key cannot be empty"
                
            # Check if key starts with expected prefix
            if not api_key.startswith("sk-"):
                error_msg = "Invalid API key format: should start with 'sk-'"
                self._log_manager.log_warning(error_msg)
                return False, error_msg
                
            # Check minimum length
            if len(api_key) < 20:
                error_msg = "Invalid API key format: too short"
                self._log_manager.log_warning(error_msg)
                return False, error_msg
                
            return True, ""
        
        except Exception as e:
            self._log_manager.log_error(f"Error validating API key", error = e)
            return False, error_msg

    def _list_credentials(self):
        """
        List stored API key (masked) for debugging
        """
        try:
            api_key = self.get_api_key()
            if api_key:
                # Mask the API key for secure logging
                masked_key = f"{api_key[:4]}...{'*' * (len(api_key) - 8)}{api_key[-4:]}"
                self._log_manager.log_info(f"Stored API Key: {masked_key}")
            else:
                self._log_manager.log_info("No stored API key found")
                
        except Exception as e:
            self._log_manager.log_error(f"Failed to list credentials", error = e)
        
    def delete_credentials(self):
        """
        Delete all credentials from keyring and config
        """
        try:
            # Try to delete encryption key from keyring
            try:
                keyring.delete_password("Promptly - Textprocessor", "encryption_key")
                self._log_manager.log_info("Encryption key deleted from keyring")
            except keyring.errors.PasswordDeleteError:
                # Key didn't exist, that's okay
                self._log_manager.log_info("No encryption key found in keyring")
                
            # Reset instance variables
            self._encryption_key = None
            self._cipher_suite = None           
        except Exception as e:
            self._log_manager.log_error(f"Unexpected error deleting credentials", error = e)