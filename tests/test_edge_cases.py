import pytest
from src.normalizers.location import LocationNormalizer
from src.normalizers.date import DateNormalizer
from src.normalizers.phone import PhoneNormalizer
from src.normalizers.skills import SkillsNormalizer
from src.normalizers.text import TextNormalizer
from src.projector.projection import ProjectionEngine
from src.models.candidate import CanonicalCandidate
from src.models.config import ProjectionConfig
from src.utils.exceptions import ProjectorError

def test_location_normalizer_weird_casing():
    raw_loc = {"city": "   new york   ", "region": "  ny  ", "country": "  uNiTeD sTaTeS   "}
    norm = LocationNormalizer.normalize(raw_loc)
    assert norm["city"] == "New York"
    assert norm["region"] == "Ny"
    assert norm["country"] == "US"

def test_location_normalizer_unrecognized_country():
    raw_loc = {"country": "Atlantis"}
    norm = LocationNormalizer.normalize(raw_loc)
    assert norm["country"] == "Atlantis"

def test_date_normalizer_empty_and_odd():
    assert DateNormalizer.normalize("") == ""
    assert DateNormalizer.normalize(None) == ""
    assert DateNormalizer.normalize("2022/11/25") == "2022-11"
    assert DateNormalizer.normalize("Active") == "Present"

def test_phone_normalizer_letters():
    # If the number of extracted digits is >= 7, it returns the formatted digits.
    assert PhoneNormalizer.normalize("1-800-444-PYTHON") == "+1800444"
    # Otherwise, it falls back to the original string
    assert PhoneNormalizer.normalize("1-800-PYTHON") == "1-800-PYTHON"

def test_skills_normalizer_trimming():
    assert SkillsNormalizer.normalize("   py   ") == "Python"
    assert SkillsNormalizer.normalize("   react.js   ") == "React"

def test_text_normalizer_consecutive_spaces():
    assert TextNormalizer.clean_text("lots   of      spaces   here") == "lots of spaces here"

def test_projector_empty_lists_omit():
    engine = ProjectionEngine()
    candidate = CanonicalCandidate(
        candidate_id="merged_test",
        full_name="Test Name",
        emails=[]
    )
    # Target path emails[0] is missing (emails list is empty)
    config_dict = {
        "fields": [
            {"path": "name", "from": "full_name", "type": "string"},
            {"path": "email", "from": "emails[0]", "type": "string"}
        ],
        "include_confidence": False,
        "include_provenance": False,
        "on_missing": "omit"
    }
    config = ProjectionConfig.model_validate(config_dict)
    projected = engine.project(candidate, config)
    
    # 'email' should be omitted
    assert "email" not in projected
    assert projected["name"] == "Test Name"
