import pytest
from src.mapper.canonical_mapper import CanonicalMapper
from src.models.candidate import CanonicalCandidate

@pytest.fixture
def mapper():
    return CanonicalMapper()

def test_map_csv(mapper):
    raw_payload = {
        "source_type": "csv",
        "source_path": "recruiter.csv",
        "raw_content": [
            {
                "name": "Jane Doe",
                "email": "jane.doe@example.com",
                "phone": "123-456-7890",
                "current_company": "Netflix",
                "title": "Senior Engineer"
            }
        ]
    }
    candidate = mapper.map_to_canonical(raw_payload, "csv")
    assert isinstance(candidate, CanonicalCandidate)
    assert candidate.full_name == "Jane Doe"
    assert candidate.emails == ["jane.doe@example.com"]
    assert candidate.phones == ["123-456-7890"]
    assert len(candidate.experience) == 1
    assert candidate.experience[0].company == "Netflix"
    assert candidate.experience[0].title == "Senior Engineer"
    
    # Provenance checks
    fields = [prov["field"] for prov in candidate.provenance]
    assert "full_name" in fields
    assert "emails" in fields
    assert "phones" in fields
    assert "experience" in fields
    for prov in candidate.provenance:
        assert prov["source"] == "csv"

def test_map_ats(mapper):
    raw_payload = {
        "source_type": "ats",
        "source_path": "ats.json",
        "raw_content": {
            "candidate": {
                "first_name": "Alice",
                "last_name": "Smith",
                "contact": {
                    "email_address": "alice@example.com",
                    "phone_number": "987-654-3210"
                },
                "positions": [
                    {
                        "company_name": "Meta",
                        "job_title": "Product Manager",
                        "start_date": "2021-06",
                        "end_date": "Present",
                        "description": "Led product strategy"
                    }
                ],
                "education_records": [
                    {
                        "school": "Stanford",
                        "degree_name": "Bachelor",
                        "major": "Symbolic Systems",
                        "graduation_year": 2020
                    }
                ]
            }
        }
    }
    candidate = mapper.map_to_canonical(raw_payload, "ats")
    assert candidate.full_name == "Alice Smith"
    assert candidate.emails == ["alice@example.com"]
    assert candidate.phones == ["987-654-3210"]
    assert len(candidate.experience) == 1
    assert candidate.experience[0].company == "Meta"
    assert candidate.experience[0].title == "Product Manager"
    assert len(candidate.education) == 1
    assert candidate.education[0].institution == "Stanford"
    assert candidate.education[0].end_year == 2020

def test_map_resume(mapper):
    raw_payload = {
        "source_type": "resume",
        "source_path": "resume.pdf",
        "raw_content": {
            "raw_text": "Bob Builder\nEmail: bob@builder.com\nTel: +1-555-0199\nSkills: Python, AWS, Docker."
        }
    }
    candidate = mapper.map_to_canonical(raw_payload, "resume")
    assert candidate.full_name == "Bob Builder"
    assert candidate.emails == ["bob@builder.com"]
    assert candidate.phones == ["+1-555-0199"]
    skills = [s.name for s in candidate.skills]
    assert "Python" in skills
    assert "AWS" in skills
    assert "Docker" in skills

def test_map_notes(mapper):
    raw_payload = {
        "source_type": "notes",
        "source_path": "notes.txt",
        "raw_content": {
            "raw_text": "Candidate: Charlie Chaplin\nEmail: charlie@cinema.com\nInterested in Python & Rust."
        }
    }
    candidate = mapper.map_to_canonical(raw_payload, "notes")
    assert candidate.full_name == "Charlie Chaplin"
    assert candidate.emails == ["charlie@cinema.com"]
    skills = [s.name for s in candidate.skills]
    assert "Python" in skills
    assert "Rust" in skills

def test_map_github(mapper):
    raw_payload = {
        "source_type": "github",
        "source_path": "https://github.com/coder",
        "raw_content": {
            "user": {
                "name": "Dev Coder",
                "login": "coder",
                "email": "coder@github.com",
                "bio": "Open source enthusiast",
                "html_url": "https://github.com/coder",
                "location": "Berlin, Germany"
            },
            "repos": [
                {"language": "Python"},
                {"language": "Go"},
                {"language": "Python"}
            ]
        }
    }
    candidate = mapper.map_to_canonical(raw_payload, "github")
    assert candidate.full_name == "Dev Coder"
    assert candidate.emails == ["coder@github.com"]
    assert candidate.headline == "Open source enthusiast"
    assert candidate.links.github == "https://github.com/coder"
    assert candidate.location.city == "Berlin"
    assert candidate.location.region == "Germany"
    skills = [s.name for s in candidate.skills]
    assert "Python" in skills
    assert "Go" in skills
