import pytest
import csv
import json
import tempfile
from src.pipeline import CandidateTransformationPipeline
from src.models.config import ProjectionConfig
from src.utils.exceptions import ParserError, ValidationError

@pytest.fixture
def sample_sources(tmp_path):
    # CSV source
    csv_file = tmp_path / "recruiter.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "email", "phone", "current_company", "title"])
        writer.writerow(["John Doe", "john.doe@example.com", "4155552671", "Google", "Staff Engineer"])

    # ATS JSON source
    ats_file = tmp_path / "ats.json"
    ats_data = {
        "candidate": {
            "first_name": "John",
            "last_name": "Doe",
            "contact": {
                "email_address": "john.doe@example.com",
                "phone_number": "+14155552671"
            },
            "positions": [
                {
                    "company_name": "Google",
                    "job_title": "Senior Staff Engineer",
                    "start_date": "2020-01",
                    "end_date": "Present",
                    "description": "Orchestrating search infrastructures."
                }
            ]
        }
    }
    with open(ats_file, "w", encoding="utf-8") as f:
        json.dump(ats_data, f)

    # Notes source
    notes_file = tmp_path / "notes.txt"
    with open(notes_file, "w", encoding="utf-8") as f:
        f.write("Candidate Name: John Doe\nSkills: Python, Go, Docker\nWorked at Google.")

    # Custom projection config
    config_dict = {
        "fields": [
            {"path": "name", "from": "full_name", "type": "string", "required": True},
            {"path": "email", "from": "emails[0]", "type": "string"},
            {"path": "phone", "from": "phones[0]", "type": "string", "normalize": "E.164"},
            {"path": "skills", "from": "skills[].name", "type": "string[]"}
        ],
        "include_confidence": True,
        "include_provenance": False,
        "on_missing": "null"
    }
    config = ProjectionConfig.model_validate(config_dict)

    return {
        "csv": str(csv_file),
        "ats": str(ats_file),
        "notes": str(notes_file),
        "config": config
    }

def test_pipeline_e2e_success(sample_sources):
    pipeline = CandidateTransformationPipeline()
    result = pipeline.run(
        config=sample_sources["config"],
        csv_path=sample_sources["csv"],
        ats_path=sample_sources["ats"],
        notes_path=sample_sources["notes"]
    )
    
    assert result["name"] == "John Doe"
    assert result["email"] == "john.doe@example.com"
    assert result["phone"] == "+14155552671"
    # Skills from notes vocabulary
    assert "Python" in result["skills"]
    assert "Go" in result["skills"]
    assert "overall_confidence" in result
    assert result["overall_confidence"] > 0.8  # Redundancy and completeness bonus

def test_pipeline_graceful_degradation(sample_sources):
    pipeline = CandidateTransformationPipeline()
    
    # Write a corrupted json file
    corrupted_ats = tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False)
    corrupted_ats.write("{ invalid json payload ")
    corrupted_ats.close()
    
    # Run with one valid source (csv) and one corrupted source (ats)
    result = pipeline.run(
        config=sample_sources["config"],
        csv_path=sample_sources["csv"],
        ats_path=corrupted_ats.name
    )
    
    # Pipeline should still succeed because CSV is parsed successfully (graceful degradation)
    assert result["name"] == "John Doe"
    assert result["email"] == "john.doe@example.com"

def test_pipeline_all_sources_fail(sample_sources):
    pipeline = CandidateTransformationPipeline()
    
    # Write two corrupted files
    corrupted_ats = tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False)
    corrupted_ats.write("{ invalid json payload ")
    corrupted_ats.close()
    
    corrupted_csv = tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=False)
    # Write garbage text that pandas cannot parse as CSV
    corrupted_csv.write("")
    corrupted_csv.close()
    
    with pytest.raises(ParserError):
        pipeline.run(
            config=sample_sources["config"],
            csv_path=corrupted_csv.name,
            ats_path=corrupted_ats.name
        )
