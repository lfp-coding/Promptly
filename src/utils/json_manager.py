import json
from typing import Type, TypeVar, Any, Optional
from dataclass_wizard import JSONWizard

import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
from src.utils.log_manager import LogManager

# Generic type for deserialization
T = TypeVar("T")

class JsonManager:
    """
    A utility class for handling JSON serialization and deserialization of dataclasses,
    including support for nested dataclasses and Enums
    """

    @staticmethod
    def save_to_file(data: Any, filename: Path):
        """
        Save data to a JSON file
        
        Args:
            data (Any): Data to save. Can be a dictionary, list, or a dataclass instance
            filename (Path): File path to save the JSON data
        """
        log_manager = LogManager.get_instance()
        log_manager.log_info(f"Saving data to {filename}")

        try:  
            # Ensure directory exists
            filename.parent.mkdir(parents=True, exist_ok=True)
            
            if isinstance(data, JSONWizard):
                data = data.to_dict()

            # Write serialized data to file
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            
            log_manager.log_info("Data saved successfully")
        except Exception as e:
            log_manager.log_error(f"Failed to save data to {filename}", error = e)
            raise

    @staticmethod
    def load_from_file(filename: Path, cls: Optional[Type[T]] = None) -> Any:
        """
        Load data from a JSON file
        
        Args:
            filename (Path): File path to load the JSON data from
            cls (Optional[Type[JSONWizard]]): Optional dataclass type for deserialization

        Returns:
            Any: Loaded data. If `cls` is provided, returns an instance of that dataclass
        """
        log_manager = LogManager.get_instance()
        log_manager.log_info(f"Loading data from {filename}")
        try:
            if not filename.exists():
                log_manager.log_info(f"File {filename} does not exist.")
                return None

            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)

            # Convert dictionary to dataclass if needed
            if cls:
                return cls.from_dict(data)

            return data
        except Exception as e:
            log_manager.log_error(f"Failed to load data from {filename}", error = e)
            raise