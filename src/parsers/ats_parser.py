from typing import Any, Dict
from src.parsers.base import BaseParser

class ATSParser(BaseParser):
    """
    Parser for ATS JSON export payloads.
    """
    def parse(self, source_path: str) -> Dict[str, Any]:
        # TODO: Implement ATS JSON parsing logic
        return {}
