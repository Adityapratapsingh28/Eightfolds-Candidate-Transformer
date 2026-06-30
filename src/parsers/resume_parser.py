import fitz  # PyMuPDF
from typing import Any, Dict
from src.parsers.base import BaseParser
from src.utils.exceptions import ParserError

class ResumeParser(BaseParser):
    """
    Parser for unstructured Resume PDF files.
    """
    def parse(self, source_path: str) -> Dict[str, Any]:
        try:
            doc = fitz.open(source_path)
            full_text = []
            for page in doc:
                text = page.get_text()
                if text:
                    full_text.append(text)
            doc.close()
            
            return {
                "source_type": "resume",
                "source_path": source_path,
                "raw_content": {
                    "raw_text": "\n".join(full_text)
                }
            }
        except Exception as e:
            raise ParserError(f"Failed to parse PDF resume at {source_path}: {e}") from e

