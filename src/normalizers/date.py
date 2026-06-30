from dateutil import parser
import re

class DateNormalizer:
    """
    Normalizes dates to YYYY-MM format.
    """
    @staticmethod
    def normalize(date_str: str) -> str:
        if not date_str:
            return ""

        cleaned_date = date_str.strip()

        # Handle Present/Current fallbacks
        if cleaned_date.lower() in ["present", "current", "active", "now", "ongoing"]:
            return "Present"

        try:
            # Parse date using dateutil parser
            dt = parser.parse(cleaned_date)
            return dt.strftime("%Y-%m")
        except Exception:
            pass

        # Fallback: regex search for YYYY-MM
        match = re.search(r"(\d{4})[-/](\d{1,2})", cleaned_date)
        if match:
            year, month = match.group(1), match.group(2).zfill(2)
            return f"{year}-{month}"

        return cleaned_date

