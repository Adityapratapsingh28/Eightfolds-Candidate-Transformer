import pytest
from src.projector.projection import ProjectionEngine
from src.models.candidate import CanonicalCandidate, Location, Skill, Links
from src.models.config import ProjectionConfig
from src.utils.exceptions import ProjectorError

@pytest.fixture
def sample_candidate():
    return CanonicalCandidate(
        candidate_id="merged_john_doe",
        full_name="John Doe",
        emails=["john.doe@example.com", "john.work@example.com"],
        phones=["+14155552671"],
        location=Location(city="San Francisco", region="CA", country="US"),
        links=Links(github="https://github.com/johndoe"),
        skills=[
            Skill(name="Python", confidence=0.9, sources=["resume"]),
            Skill(name="React", confidence=0.8, sources=["ats"])
        ],
        provenance=[{"field": "full_name", "source": "ats", "method": "json_path_mapping"}],
        overall_confidence=0.95
    )

def test_simple_remapping(sample_candidate):
    engine = ProjectionEngine()
    config_dict = {
        "fields": [
            {"path": "name", "from": "full_name", "type": "string"},
            {"path": "city", "from": "location.city", "type": "string"}
        ],
        "include_confidence": False,
        "include_provenance": False,
        "on_missing": "null"
    }
    config = ProjectionConfig.model_validate(config_dict)
    projected = engine.project(sample_candidate, config)
    
    assert projected == {
        "name": "John Doe",
        "city": "San Francisco"
    }

def test_array_indexing_and_list_mapping(sample_candidate):
    engine = ProjectionEngine()
    config_dict = {
        "fields": [
            {"path": "primary_email", "from": "emails[0]", "type": "string"},
            {"path": "skills_list", "from": "skills[].name", "type": "string[]"}
        ],
        "include_confidence": False,
        "include_provenance": False,
        "on_missing": "null"
    }
    config = ProjectionConfig.model_validate(config_dict)
    projected = engine.project(sample_candidate, config)
    
    assert projected == {
        "primary_email": "john.doe@example.com",
        "skills_list": ["Python", "React"]
    }

def test_missing_value_omit(sample_candidate):
    engine = ProjectionEngine()
    config_dict = {
        "fields": [
            {"path": "full_name", "type": "string"},
            {"path": "missing_field", "from": "headline", "type": "string"}
        ],
        "include_confidence": False,
        "include_provenance": False,
        "on_missing": "omit"
    }
    config = ProjectionConfig.model_validate(config_dict)
    projected = engine.project(sample_candidate, config)
    
    assert "missing_field" not in projected
    assert projected["full_name"] == "John Doe"

def test_missing_value_error(sample_candidate):
    engine = ProjectionEngine()
    config_dict = {
        "fields": [
            {"path": "full_name", "type": "string"},
            {"path": "missing_field", "from": "headline", "type": "string"}
        ],
        "include_confidence": False,
        "include_provenance": False,
        "on_missing": "error"
    }
    config = ProjectionConfig.model_validate(config_dict)
    with pytest.raises(ProjectorError):
        engine.project(sample_candidate, config)

def test_required_field_error(sample_candidate):
    engine = ProjectionEngine()
    config_dict = {
        "fields": [
            {"path": "headline", "type": "string", "required": True}
        ],
        "include_confidence": False,
        "include_provenance": False,
        "on_missing": "null"
    }
    config = ProjectionConfig.model_validate(config_dict)
    with pytest.raises(ProjectorError):
        engine.project(sample_candidate, config)

def test_toggles(sample_candidate):
    engine = ProjectionEngine()
    config_dict = {
        "fields": [{"path": "full_name", "type": "string"}],
        "include_confidence": True,
        "include_provenance": True,
        "on_missing": "null"
    }
    config = ProjectionConfig.model_validate(config_dict)
    projected = engine.project(sample_candidate, config)
    
    assert "overall_confidence" in projected
    assert projected["overall_confidence"] == 0.95
    assert "provenance" in projected
    assert len(projected["provenance"]) == 1

def test_immutability(sample_candidate):
    engine = ProjectionEngine()
    config_dict = {
        "fields": [{"path": "name", "from": "full_name", "type": "string"}],
        "include_confidence": False,
        "include_provenance": False,
        "on_missing": "null"
    }
    config = ProjectionConfig.model_validate(config_dict)
    projected = engine.project(sample_candidate, config)
    
    # Verify candidate properties did not change
    assert sample_candidate.full_name == "John Doe"
    projected["name"] = "Different Name"
    assert sample_candidate.full_name == "John Doe"

