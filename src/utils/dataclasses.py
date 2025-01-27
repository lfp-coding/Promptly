from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict
from dataclass_wizard import JSONWizard

@dataclass(slots=True)
class GeneralConfig(JSONWizard):
    autostart: bool
    api_provider: Optional[str]

@dataclass(slots=True)
class APIClient(JSONWizard):
    api_key_encrypted: str
    model: str
    temperature: Optional[float]
    max_tokens: Optional[int]
    timeout: Optional[int]

class TextSelectionBehaviour(Enum):
    SKIP = 'skip'
    PROCESS = 'process'
    SELECT_ALL = 'select_all'

class HotkeyCategory(Enum):
    GLOBAL = 'global'
    PROMPT = 'prompt'

@dataclass(slots=True)
class HotkeyMapping(JSONWizard):
    id: str
    callback: str

@dataclass(slots=True)
class PromptBehavior(JSONWizard):
    clear_history: bool
    text_selected: TextSelectionBehaviour
    no_text_selected: TextSelectionBehaviour
    additional_input: bool
    output_on_separate_window: bool

@dataclass(slots=True)
class Prompt(JSONWizard):
    # id: str
    description: str
    template: str
    hotkey: str
    hotkey_enabled: bool
    behavior: PromptBehavior

@dataclass(slots=True)
class SystemHotkey(JSONWizard):
    hotkey: str
    hotkey_enabled: bool
    callback: str  

@dataclass(slots=True)
class Config(JSONWizard):
    general_config: GeneralConfig
    api_clients: Dict[str, APIClient]
    prompts: Dict[str, Prompt]
    system_hotkeys: Dict[str, SystemHotkey]