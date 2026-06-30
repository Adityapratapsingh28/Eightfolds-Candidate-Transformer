import json
from typing import Any, Dict
from src.models.config import ProjectionConfig

import pydantic
from src.utils.exceptions import ValidationError

def load_json(file_path: str) -> Dict[str, Any]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON format in file {file_path}: {e}") from e
    except Exception as e:
        raise ValidationError(f"Failed to open/read file {file_path}: {e}") from e

def load_config(file_path: str) -> ProjectionConfig:
    """
    Loads and validates a JSON configuration file into a ProjectionConfig model.
    """
    data = load_json(file_path)
    try:
        return ProjectionConfig.model_validate(data)
    except pydantic.ValidationError as e:
        raise ValidationError(f"Configuration validation failed: {e}") from e


