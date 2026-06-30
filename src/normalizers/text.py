class TextNormalizer:
    """
    Cleans general unstructured strings (capitalization, removing excess spaces).
    """
    @staticmethod
    def clean(text: str) -> str:
        if not text:
            return ""
        return " ".join(text.strip().split())
