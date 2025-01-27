from pathlib import Path
import sys

# Base directory of the project (calculated dynamically)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Necessary directories
CONFIG_DIR = BASE_DIR / "config"
LOGS_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"

# Files
CHAT_HISTORY_FILE = CONFIG_DIR / "chathistory.json"

def ensure_directories():
    """
    Ensures that the necessary directories exist.
    Creates the directories if they are missing.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

def get_base_path() -> Path:
    """
    Returns the base directory of the project
    """
    return BASE_DIR

def get_config_path() -> Path:
    """
    Returns the path to the configuration directory
    """
    return CONFIG_DIR

def get_logs_path() -> Path:
    """
    Returns the path to the logs directory
    """
    return LOGS_DIR

def get_chat_history_file() -> Path:
    """
    Returns the path to the 'chat_history.json' file
    """
    return CHAT_HISTORY_FILE

def get_assets_path() -> Path:
    """
    Return the path to the assets files
    """
    return ASSETS_DIR
