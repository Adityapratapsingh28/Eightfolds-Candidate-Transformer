from typing import Any, Dict
from src.parsers.base import BaseParser
from src.utils.exceptions import ParserError

class NotesParser(BaseParser):
    """
    Parser for unstructured recruiter note text files (.txt).
    """
    def parse(self, source_path: str) -> Dict[str, Any]:
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                text = f.read()
            return {
                "source_type": "notes",
                "source_path": source_path,
                "raw_content": {
                    "raw_text": text
                }
            }
        except Exception as e:
            raise ParserError(f"Failed to parse notes file at {source_path}: {e}") from e

