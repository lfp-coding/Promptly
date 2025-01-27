from typing import Optional, List
import google.generativeai as genai

import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.clients.base_api_client import BaseAPIClient


class GeminiClient(BaseAPIClient):
    """Singleton class for managing Gemini API interactions."""

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """
        Validate the Gemini API key by making a test request.

        Args:
            api_key (str): The API key to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            if api_key == "":
                return False
            genai.configure(api_key=api_key)

            test_model = genai.GenerativeModel('gemini-1.5-flash')
            test_model.generate_content(["Test"])
            return True
        except Exception as e:
            return False

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        super().__init__()
        self._initialized = True
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Gemini client with API key and configuration."""
        try:
            self.name = "gemini"
            api_key = self._credential_manager.get_api_key("gemini")
            if not api_key:
                return
            genai.configure(api_key=api_key)
            self._start_chat_session()
            self._log_manager.log_info("Gemini client configured successfully.")
        except Exception as e:
            self._log_manager.log_error("Failed to initialize Gemini client.", error=e)
            raise

    def _start_chat_session(self):
        """
        Start a new chat session with a specified model.

        Args:
            model_name (str): The name of the Gemini model to use.

        Returns:
            genai.ChatSession: The initialized chat session.
        """
        try:
            api_clients = self._config_manager.get_value('api_clients')
            stored_model = api_clients['gemini'].model
            model = genai.GenerativeModel(stored_model)
            self._chat_session = model.start_chat()
            self._log_manager.log_info(f"Chat session started with model: {stored_model}")
        except Exception as e:
            self._log_manager.log_error("Failed to start chat session.", error=e)
            raise

    def send_request_non_stream(self, prompt: str, retry_count: int = 0) -> Optional[str]:
        """
        Send a request to the Gemini API.

        Args:
            prompt (str): The prompt to send.
            retry_count (int): Current retry attempt number.

        Returns:
            Optional[str]: Response text or None if failed.
        """
        if not genai:
            self._log_manager.log_error("Gemini client not initialized.")
            return None

        try:
            response = self._chat_session.send_message(prompt)
            response_text = response.text

            self._chat_history.add_message("user", prompt)
            self._chat_history.add_message("assistant", response.text)
            self._chat_history.save_history()

            if response_text:
                self._chat_history.save_history()

            return response_text
        except Exception as e:
            self._log_manager.log_error("Failed to send request.", error=e)

    def clear_history(self):
        self._chat_session.history.clear()

    def send_request(self, prompt: str, retry_count: int = 0):
        """
        Send a streaming request to the Gemini API.

        Args:
            prompt (str): The prompt to send.

        Yields:
            str: Chunks of the response as they are generated.
        """
        if not genai:
            self._log_manager.log_error("Gemini client not initialized.")
            return None
        try:
            response = self._chat_session.send_message(prompt, stream=True)
            self._cancel_flag = False

            # Process and yield each chunk
            result = ""
            for chunk in response:
                if self._cancel_flag:  # Stop processing if canceled
                    response.resolve()
                    break
                text_chunk = chunk.text  # Extract text from the chunk
                if text_chunk:
                    yield text_chunk  # Yield each chunk for real-time processing

            if not self._cancel_flag:
                # Optionally log or save to chat history
                self._chat_history.add_message("user", prompt)
                self._chat_history.add_message("assistant", response.text)
                self._chat_history.save_history()

        except Exception as e:
            self._log_manager.log_error("Failed to send streaming request.", error=e)
            raise

    def get_available_models(self) -> List[str]:
        """
        Get a list of available Gemini models.

        Returns:
            List[str]: List of model names.
        """
        try:
            models = genai.list_models()
            model_names = [model.name.split('/')[-1] for model in models]

            return sorted(model_names)
        except Exception as e:
            self._log_manager.log_error("Failed to get available models.", error=e)

        return []
