import pytest
from src.normalizers.phone import PhoneNormalizer
from src.normalizers.date import DateNormalizer
from src.normalizers.location import LocationNormalizer
from src.normalizers.skills import SkillsNormalizer
from src.normalizers.text import TextNormalizer

def test_phone_normalizer():
    # US Standard parsing
    assert PhoneNormalizer.normalize("415.555.2671") == "+14155552671"
    assert PhoneNormalizer.normalize("1-415-555-2671") == "+14155552671"
    
    # International parsing
    assert PhoneNormalizer.normalize("+91 99999 88888") == "+919999988888"
    assert PhoneNormalizer.normalize("919999988888") == "+919999988888"
    
    # Fallback/Malformed handling
    assert PhoneNormalizer.normalize("abc-1234567") == "+1234567"
    assert PhoneNormalizer.normalize("") == ""

def test_date_normalizer():
    assert DateNormalizer.normalize("January 2020") == "2020-01"
    assert DateNormalizer.normalize("2018-05-12") == "2018-05"
    assert DateNormalizer.normalize("Present") == "Present"
    assert DateNormalizer.normalize("ongoing") == "Present"
    assert DateNormalizer.normalize("05/1999") == "1999-05"
    
    # Unparseable fallback
    assert DateNormalizer.normalize("Unknown Date") == "Unknown Date"
    assert DateNormalizer.normalize("") == ""

def test_location_normalizer():
    raw_us = {"city": "san francisco", "region": "ca", "country": "United States"}
    norm_us = LocationNormalizer.normalize(raw_us)
    assert norm_us["city"] == "San Francisco"
    assert norm_us["region"] == "Ca"
    assert norm_us["country"] == "US"
    
    raw_in = {"city": "mumbai", "region": "maharashtra", "country": "india"}
    norm_in = LocationNormalizer.normalize(raw_in)
    assert norm_in["city"] == "Mumbai"
    assert norm_in["region"] == "Maharashtra"
    assert norm_in["country"] == "IN"

    raw_unknown = {"city": "Sydney", "country": "Australia"}
    norm_unknown = LocationNormalizer.normalize(raw_unknown)
    assert norm_unknown["country"] == "AU"

    # Already a code
    assert LocationNormalizer.normalize({"country": "DE"})["country"] == "DE"

def test_skills_normalizer():
    assert SkillsNormalizer.normalize("py") == "Python"
    assert SkillsNormalizer.normalize("python3") == "Python"
    assert SkillsNormalizer.normalize("reactjs") == "React"
    assert SkillsNormalizer.normalize("aws") == "AWS"
    assert SkillsNormalizer.normalize("Docker") == "Docker"
    assert SkillsNormalizer.normalize("ml") == "Machine Learning"
    
    # No map lookup
    assert SkillsNormalizer.normalize("Fortran") == "Fortran"

def test_text_normalizer():
    assert TextNormalizer.clean_text("  hello    world   ") == "hello world"
    assert TextNormalizer.clean_email("  JANE.DOE@example.com  ") == "jane.doe@example.com"
    assert TextNormalizer.clean_email("mailto:alice@smith.com") == "alice@smith.com"
    assert TextNormalizer.clean_email("malformed_email") == "malformed_email"
