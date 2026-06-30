from src.models.candidate import CanonicalCandidate
from src.normalizers.text import TextNormalizer

class CandidateMatcher:
    """
    Evaluates whether two candidate profiles match (e.g., matching by unique email, phone number, etc.).
    """
    @staticmethod
    def match(candidate_a: CanonicalCandidate, candidate_b: CanonicalCandidate) -> bool:
        # 1. Match by Email (case-insensitive, cleaned)
        emails_a = {e.strip().lower() for e in candidate_a.emails if e}
        emails_b = {e.strip().lower() for e in candidate_b.emails if e}
        if emails_a & emails_b:
            return True

        # 2. Match by Phone (digits only comparison)
        def clean_phone(p: str) -> str:
            import re
            return re.sub(r"\D", "", p)

        phones_a = {clean_phone(p) for p in candidate_a.phones if p}
        phones_b = {clean_phone(p) for p in candidate_b.phones if p}
        if phones_a & phones_b:
            return True

        # 3. Match by Name + Company/Location
        name_a = TextNormalizer.clean_text(candidate_a.full_name or "").lower()
        name_b = TextNormalizer.clean_text(candidate_b.full_name or "").lower()

        if name_a and name_a == name_b:
            # Check for shared location city
            city_a = candidate_a.location.city.strip().lower() if candidate_a.location and candidate_a.location.city else None
            city_b = candidate_b.location.city.strip().lower() if candidate_b.location and candidate_b.location.city else None
            if city_a and city_a == city_b:
                return True

            # Check for shared company in experience
            companies_a = {exp.company.strip().lower() for exp in candidate_a.experience if exp.company}
            companies_b = {exp.company.strip().lower() for exp in candidate_b.experience if exp.company}
            if companies_a & companies_b:
                return True

        return False

