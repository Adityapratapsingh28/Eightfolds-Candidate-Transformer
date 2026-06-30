from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseParser(ABC):
    """
    Abstract Base Class for all source parsers in the Candidate Transformation Engine.
    """
    @abstractmethod
    def parse(self, source_path: str) -> Dict[str, Any]:
        """
        Parses a candidate source file and returns a source-specific dictionary.
        """
        pass
