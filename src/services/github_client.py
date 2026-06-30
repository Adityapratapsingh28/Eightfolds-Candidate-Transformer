import re
import os
import requests
from typing import Any, Dict, Optional
from src.utils.logger import get_logger

logger = get_logger("GitHubClient")

class GitHubClient:
    """
    HTTP Client for fetching public candidate profile details from GitHub REST API.
    """
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({"Authorization": f"token {self.token}"})

    def _extract_username(self, profile_url: str) -> Optional[str]:
        """Extracts github username from URL."""
        match = re.search(r"github\.com/([^/?#\s]+)", profile_url)
        return match.group(1) if match else None

    def fetch_profile(self, profile_url: str) -> Optional[Dict[str, Any]]:
        username = self._extract_username(profile_url)
        if not username:
            logger.warning(f"Could not extract GitHub username from URL: {profile_url}")
            return None

        # Check if environment variable requests mock or if we are offline
        if os.getenv("GITHUB_MOCK") == "true" or username.lower() == "mockuser":
            logger.info(f"Using mock data for GitHub user: {username}")
            return self._get_mock_profile(username)

        try:
            # Fetch user bio & general info
            user_url = f"https://api.github.com/users/{username}"
            user_response = self.session.get(user_url, timeout=10)
            
            if user_response.status_code == 403:
                logger.warning("GitHub API rate limit hit or forbidden. Falling back to mock data.")
                return self._get_mock_profile(username)
                
            if user_response.status_code != 200:
                logger.warning(f"Failed to fetch GitHub profile for {username}: Status {user_response.status_code}")
                return None

            user_data = user_response.json()

            # Fetch repos to gather repositories & languages
            repos_url = f"https://api.github.com/users/{username}/repos?per_page=50"
            repos_response = self.session.get(repos_url, timeout=10)
            repos_data = []
            if repos_response.status_code == 200:
                repos_data = repos_response.json()

            return {
                "user": user_data,
                "repos": repos_data
            }

        except Exception as e:
            logger.error(f"GitHub client request error for {username}: {e}. Falling back to mock data.")
            return self._get_mock_profile(username)

    def _get_mock_profile(self, username: str) -> Dict[str, Any]:
        """Returns mock profile data for testing offline or on rate limit."""
        return {
            "user": {
                "login": username,
                "name": "Mock Candidate",
                "bio": "Senior Software Engineer specializing in Python & Machine Learning.",
                "html_url": f"https://github.com/{username}",
                "location": "San Francisco, CA",
                "email": "mock.candidate@example.com"
            },
            "repos": [
                {
                    "name": "candidate-transformer",
                    "language": "Python",
                    "description": "Deterministic transformation pipeline"
                },
                {
                    "name": "web-scrappy",
                    "language": "JavaScript",
                    "description": "Simple DOM scraper"
                },
                {
                    "name": "deep-learning-notes",
                    "language": "Python",
                    "description": "Jupyter notes"
                }
            ]
        }

