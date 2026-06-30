import json
from typing import Any, Dict
from src.parsers.base import BaseParser
from src.utils.exceptions import ParserError

class ATSParser(BaseParser):
    """
    Parser for ATS JSON export payloads.
    """
    def parse(self, source_path: str) -> Dict[str, Any]:
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "source_type": "ats",
                "source_path": source_path,
                "raw_content": data
            }
        except Exception as e:
            raise ParserError(f"Failed to parse ATS JSON file at {source_path}: {e}") from e

