from typing import Dict

import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.utils.dataclasses import Prompt
from src.utils.config_manager import ConfigManager 
from src.utils.log_manager import LogManager

class PromptManager:
    """Singleton class for managing prompts"""
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = PromptManager()
        return cls._instance
        
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._log_manager = LogManager.get_instance()
        self._config_manager = ConfigManager.get_instance()
        self.load_prompts()
        

        self._log_manager.log_info("PromptManager initialized")

    def load_prompts(self):
        """
        Get prompts from config manager
        """       
        self._prompts = self._config_manager.get_value('prompts')
     
    def get_all_prompts(self) -> Dict[str, Prompt]:
        """
        Returns all available prompts from the prompt manager
        
        Returns:
            Dict[str, Prompt]: Dict of prompt dictionaries
        """
        return self._prompts

    def get_prompt_by_id(self, prompt_id: str) -> Dict[str, Prompt]:
        """
        Get prompt by ID
        """
        try:
            return self._prompts.get(prompt_id)
        except Exception as e:
            self._log_manager.log_error(f"Error getting prompt by ID", error = e)

    def add_prompt(self, prompt: Prompt):
        """
        Add new prompt
        """
        try:
            self._prompts[prompt.id] = prompt
            self._save_prompts()
            self._log_manager.log_info(f"Added new prompt: {prompt.id}")
        except Exception as e:
            self._log_manager.log_error(f"Failed to add prompt", error = e)

    def update_prompt(self, prompt_id: str, updated_prompt: Prompt):
        """
        Update existing prompt and its key while preserving order
        """
        try:
            if prompt_id not in self._prompts:
                self._log_manager.log_warning(f"Prompt with ID {prompt_id} not found.")
                return

            # Create a new dictionary with the updated key-value pair in place
            new_prompts = {}
            for key, value in self._prompts.items():
                if key == prompt_id:
                    # Replace old key with new key
                    new_prompts[updated_prompt.id] = updated_prompt
                else:
                    # Keep other entries unchanged
                    new_prompts[key] = value

            # Replace old dictionary with updated one
            self._prompts = new_prompts
            self._save_prompts()
            self._log_manager.log_info(f"Updated prompt: {prompt_id} -> {updated_prompt.id}")
        except Exception as e:
            self._log_manager.log_error(f"Failed to update prompt", error = e)

    def delete_prompt(self, prompt_id: str):
        """
        Delete prompt
        """
        try:
            initial_length = len(self._prompts)
            del self._prompts[prompt_id]
            if len(self._prompts) < initial_length:
                self._save_prompts()
                self._log_manager.log_info(f"Deleted prompt: {prompt_id}")
        except Exception as e:
            self._log_manager.log_error(f"Failed to delete prompt", error = e)