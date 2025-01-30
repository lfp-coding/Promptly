from pathlib import Path
from typing import Any

import sys
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.utils.json_manager import JsonManager
from src.utils.log_manager import LogManager
from src.utils.path_manager import get_config_path
from src.utils.dataclasses import Config, Prompt, SystemHotkey, GeneralConfig, PromptBehavior, TextSelectionBehaviour

class ConfigManager:
    """Singleton class for managing application configuration"""
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ConfigManager()
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._log_manager = LogManager.get_instance()
        self._config_file = get_config_path() / 'config.json'
        self._load_config()

        self._log_manager.log_info("ConfigManager initialized")

    def _load_config(self):
        """
        Load configuration from JSON file
        """
        try:
            self._log_manager.log_info("Loading config file...")
            self._config = JsonManager.load_from_file(self._config_file, Config)
            if not self._config:
                self._log_manager.log_info("No prompt file found, creating default")
                self._get_default_config()
                self._save_config()
        except Exception as e:
            self._log_manager.log_error(f"Failed to load configuration", error = e)
       
    def _save_config(self):
        """
        Save configuration to JSON file
        """
        try:
            self._log_manager.log_info("Saving config file...")
            JsonManager.save_to_file(self._config, self._config_file)
            self._load_config()
        except Exception as e:
            self._log_manager.log_error(f"Failed to save configuration", error = e)

    def get_value(self, key: str) -> Any:
        """
        Get a value from the configuration using dot notation.

        Args:
            key (str): The configuration key, supports dot notation.

        Returns:
            Any: The value of the specified configuration key.
        """
        try:
            if key == 'config':
                return self._config
            keys = key.split(".")
            value = self._config  # Start with the root Config object
            for k in keys:
                value = getattr(value, k)  # Traverse to the next attribute
            self._log_manager.log_info(f"Attribute '{key}' returned successfully.")
            return value
        except AttributeError as e:
            self._log_manager.log_error(f"Attribute '{key}' not found", error = e)
            raise

    def set_value(self, key: str, value: Any):
        """
        Set a value in the configuration using dot notation.

        Args:
            key (str): The configuration key, supports dot notation.
            value (Any): The value to set.
        """
        try:
            if key == 'config':
                self._config = value
            else:
                keys = key.split(".")
                current = self._config  # Start with the root Config object
                for k in keys[:-1]:  # Traverse to the second-to-last attribute
                    current = getattr(current, k)
                setattr(current, keys[-1], value)  # Set the final attribute
            self._save_config()  # Save changes back to file
            self._log_manager.log_info(f"Attribute '{key}' set successfully.")
        except AttributeError as e:
            self._log_manager.log_error(f"Failed to set attribute '{key}'", error = e)
            raise

    def get_api_client(self):
        from src.clients.gemini_api_client import GeminiClient
        api = self._config.general_config.api_provider
        if not api:
            raise KeyError("Missing 'api_provider' in configuration file.")

        if api == 'openai':
            if not self._config.api_clients[api].model: self._config.api_clients[api].model = 'gpt-4o'
            return OpenAIClient().get_instance()

        elif api == 'gemini':
            if not self._config.api_clients[api].model: self._config.api_clients[api].model = 'gemini-1.5-flash'
            return GeminiClient().get_instance()

    def _get_default_config(self):
        """
        Get default configuration
        """
        general_config = GeneralConfig(
            autostart=False,
            api_provider=""
        )

        api_clients = {}

        system_hotkeys = {
            "settings_window": SystemHotkey(
                hotkey="",
                hotkey_enabled=False,
                callback='open_settings'
            ),
            "chat_window": SystemHotkey(
                hotkey="",
                hotkey_enabled=False,
                callback='open_chat'
            ),
            "prompt_selector": SystemHotkey(
                hotkey="ctrl alt Y",
                hotkey_enabled=True,
                callback='open_context_menu'
            )
        }

        prompts = {
                "Prompt": Prompt(
                    description="Procceses selectect text if selected, processess prompt otherwise",
                    template="{input}\n\n\"{text}\"\n\n Reply only with the response, no comments. Keep the original language.",
                    hotkey="",
                    hotkey_enabled=False,
                    behavior=PromptBehavior(
                        clear_history=True,
                        text_selected=TextSelectionBehaviour.PROCESS,
                        no_text_selected=TextSelectionBehaviour.PROCESS,
                        additional_input=True,
                        output_on_separate_window=False
                    )
                ),
                "Proofread": Prompt(
                    description="Proofreads the selected text",
                    template="Proofread the following text, while preserving the original language and intend. Reply only with the corrected version nothing additionally, even if it just one word.\n\nText: {text}",
                    hotkey="ctrl alt X",
                    hotkey_enabled=True,
                    behavior=PromptBehavior(
                        clear_history=True,
                        text_selected=TextSelectionBehaviour.PROCESS,
                        no_text_selected=TextSelectionBehaviour.SELECT_ALL,
                        additional_input=False,
                        output_on_separate_window=False
                    )
                ),
                "More formal": Prompt(
                    description="Rewrite the selected text in a more formal tone",
                    template="Rewrite the following text using a more formal tone. Keep the original language. Reply only with the new version:\n\nText:\n\n{text}",
                    hotkey="",
                    hotkey_enabled=False,
                    behavior=PromptBehavior(
                        clear_history=True,
                        text_selected=TextSelectionBehaviour.PROCESS,
                        no_text_selected=TextSelectionBehaviour.SELECT_ALL,
                        additional_input=False,
                        output_on_separate_window=False
                    )
                ),                
                "Summarize Text": Prompt(
                    description="Creates a concise summary of the selected text",
                    template="Summarize the following text in a concise way. Keep the original language of the text:\n\n{text}",
                    hotkey="",
                    hotkey_enabled=False,
                    behavior=PromptBehavior(
                        clear_history=True,
                        text_selected=TextSelectionBehaviour.PROCESS,
                        no_text_selected=TextSelectionBehaviour.SKIP,
                        additional_input=False,
                        output_on_separate_window=True
                    )
                ),
                "Translate to English": Prompt(
                    description="Translates text into English",
                    template="Translate the following text into Englisch. Just reply with the translated text or word.\n\nText: {text}",
                    hotkey="",
                    hotkey_enabled=False,
                    behavior=PromptBehavior(
                        clear_history=True,
                        text_selected=TextSelectionBehaviour.PROCESS,
                        no_text_selected=TextSelectionBehaviour.SKIP,
                        additional_input=False,
                        output_on_separate_window=True
                    )
                ),
                "Translater": Prompt(
                    description="Translates text into specified language",
                    template="Translate the following text into {input}. Just reply with the translated text or word.\n\nText: {text}",
                    hotkey="",
                    hotkey_enabled=False,
                    behavior=PromptBehavior(
                        clear_history=True,
                        text_selected=TextSelectionBehaviour.PROCESS,
                        no_text_selected=TextSelectionBehaviour.SKIP,
                        additional_input=True,
                        output_on_separate_window=False
                    )
                ),
        }

        self._config = Config(general_config=general_config, api_clients=api_clients, prompts=prompts, system_hotkeys= system_hotkeys)
        