from typing import Any, Dict
from src.parsers.base import BaseParser
from src.services.github_client import GitHubClient
from src.utils.exceptions import ParserError

class GitHubParser(BaseParser):
    """
    Parser for GitHub profiles using API results.
    """
    def __init__(self):
        self.client = GitHubClient()

    def parse(self, source_path: str) -> Dict[str, Any]:
        try:
            profile_data = self.client.fetch_profile(source_path)
            if not profile_data:
                raise ParserError(f"Could not retrieve GitHub profile data from: {source_path}")
            
            return {
                "source_type": "github",
                "source_path": source_path,
                "raw_content": profile_data
            }
        except Exception as e:
            if not isinstance(e, ParserError):
                raise ParserError(f"Failed to fetch/parse GitHub profile for {source_path}: {e}") from e
            raise e

