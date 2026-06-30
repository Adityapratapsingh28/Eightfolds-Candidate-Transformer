import phonenumbers
import re

class PhoneNormalizer:
    """
    Normalizes phone numbers to E.164 format.
    """
    @staticmethod
    def normalize(phone: str, region: str = "US") -> str:
        if not phone:
            return ""
        
        # Clean up whitespace and brackets first
        cleaned_phone = phone.strip()
        
        try:
            # Attempt to parse phone number
            parsed = phonenumbers.parse(cleaned_phone, region)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            pass

        # Fallback: if it's already digits only with optional '+'
        digits = re.sub(r"[^\d+]", "", cleaned_phone)
        if len(digits) >= 7:
            if not digits.startswith("+") and region == "US" and not digits.startswith("1") and len(digits) == 10:
                return f"+1{digits}"
            return digits if digits.startswith("+") else f"+{digits}"

        return cleaned_phone

