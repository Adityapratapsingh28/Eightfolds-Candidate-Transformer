import re

class TextNormalizer:
    """
    Cleans general unstructured strings (capitalization, removing excess spaces, emails).
    """
    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        return " ".join(text.strip().split())

    @staticmethod
    def clean_email(email: str) -> str:
        if not email:
            return ""
        
        cleaned = email.strip().lower()
        # Basic validation: must contain '@' and '.'
        if "@" in cleaned and "." in cleaned:
            # Further strip out formatting artifacts (e.g. angle brackets, trailing text)
            match = re.search(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", cleaned)
            if match:
                return match.group(0)
        return cleaned

