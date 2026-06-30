import json
from typing import Any, Dict
from src.models.config import ProjectionConfig

def load_json(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_config(file_path: str) -> ProjectionConfig:
    """
    Loads and validates a JSON configuration file into a ProjectionConfig model.
    """
    data = load_json(file_path)
    return ProjectionConfig.model_validate(data)

