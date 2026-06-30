from abc import ABC, abstractmethod
from typing import Any, Dict, Type

class BaseParser(ABC):
    """
    Abstract Base Class for all source parsers in the Candidate Transformation Engine.
    """
    @abstractmethod
    def parse(self, source_path: str) -> Dict[str, Any]:
        """
        Parses a candidate source file/URL and returns a dict with structure:
        {
            "source_type": str,
            "source_path": str,
            "raw_content": Any
        }
        """
        pass

def get_parser_for_source(source_path: str) -> BaseParser:
    """
    Detects the source type from file extension/URL and returns the appropriate parser.
    """
    from src.parsers.csv_parser import CSVParser
    from src.parsers.ats_parser import ATSParser
    from src.parsers.resume_parser import ResumeParser
    from src.parsers.notes_parser import NotesParser
    from src.parsers.github_parser import GitHubParser
    from src.utils.exceptions import ParserError

    path_lower = source_path.lower()
    
    if path_lower.startswith("http://") or path_lower.startswith("https://") or "github.com" in path_lower:
        return GitHubParser()
    elif path_lower.endswith(".csv"):
        return CSVParser()
    elif path_lower.endswith(".json"):
        return ATSParser()
    elif path_lower.endswith(".pdf"):
        return ResumeParser()
    elif path_lower.endswith(".txt"):
        return NotesParser()
    else:
        raise ParserError(f"Unsupported source format or URL: {source_path}")

