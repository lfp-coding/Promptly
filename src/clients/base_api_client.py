from abc import ABC, abstractmethod
from typing import List
from time import sleep

import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.utils.credential_manager import CredentialManager
from src.utils.config_manager import ConfigManager
from src.utils.log_manager import LogManager
from src.utils.chat_history import ChatHistory

class BaseAPIClient(ABC):
    """
    An abstract base class for shared functionality across different API clients.
    """

    def __init__(self):
        self._log_manager = LogManager.get_instance()
        self._credential_manager = CredentialManager.get_instance()
        self._config_manager = ConfigManager.get_instance()
        self._chat_history = ChatHistory.get_instance()
        self._client = None
        self._cancel_flag = False
        self.name = None

    @abstractmethod
    def _initialize_client(self):
        """
        Abstract method for API-specific client initialization.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def send_request(self, prompt: str, retry_count: int = 0):
        """
        Abstract method for sending a prompt to the API client.
        Must be implemented by subclasses.
        """
        pass

    def cancel_request(self):
        """
        Set the cancellation flag for stopping an ongoing request.
        """
        self._cancel_flag = True

    def handle_rate_limit(self, retry_count: int, max_retries: int, retry_delay: int) -> bool:
        """
        Shared rate-limit handling across APIs.
        Args:
            retry_count (int): Current retry attempt.
            max_retries (int): Maximum number of retries.
            retry_delay (int): Time delay between retries.

        Returns:
            bool: True if retry should proceed, False otherwise.
        """
        if retry_count < max_retries:
            sleep(retry_delay)
            return True
        self._log_manager.log_error("Maximum retries reached.")
        return False

    def validate_api_key(self, api_key: str) -> bool:
        """
        API Key validation logic shared between different clients.
        Subclasses should override this as necessary.

        Args:
            api_key (str): API key to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Shared mechanism for getting available models.
        To be implemented by subclasses.
        """
        pass