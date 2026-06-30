import pytest
from src.merger.matcher import CandidateMatcher
from src.merger.resolver import ConflictResolver
from src.models.candidate import CanonicalCandidate, Location, Skill, Experience, Education

@pytest.fixture
def sample_profiles():
    # ATS Profile (highest priority)
    ats_profile = CanonicalCandidate(
        candidate_id="ats_john_doe",
        full_name="John Doe",
        emails=["john.doe@example.com"],
        phones=["+1-415-555-2671"],
        location=Location(city="San Francisco", region="CA", country="US"),
        experience=[
            Experience(company="Google", title="Staff Engineer", start="2020-01", end="Present", summary="Worked on Search.")
        ],
        provenance=[{"field": "full_name", "source": "ats", "method": "json_path_mapping"}]
    )

    # CSV Profile (second priority)
    csv_profile = CanonicalCandidate(
        candidate_id="csv_john_doe",
        full_name="John R. Doe",
        emails=["john.doe@example.com", "john.work@example.com"],
        phones=["4155552671"],
        experience=[
            Experience(company="Google", title="Staff Engineer", summary="Core Search Infrastructure")
        ],
        provenance=[{"field": "full_name", "source": "csv", "method": "direct_mapping"}]
    )

    # Resume Profile (lower priority)
    resume_profile = CanonicalCandidate(
        candidate_id="resume_john_doe",
        full_name="John Doe",
        emails=["john.doe@example.com"],
        skills=[
            Skill(name="Python", confidence=0.7, sources=["resume"]),
            Skill(name="C++", confidence=0.7, sources=["resume"])
        ],
        provenance=[]
    )

    # Notes Profile (lowest priority)
    notes_profile = CanonicalCandidate(
        candidate_id="notes_john_doe",
        full_name="John Doe",
        skills=[
            Skill(name="Python", confidence=0.7, sources=["notes"]),
            Skill(name="Git", confidence=0.7, sources=["notes"])
        ],
        provenance=[]
    )

    return {
        "ats": ats_profile,
        "csv": csv_profile,
        "resume": resume_profile,
        "notes": notes_profile
    }

def test_candidate_matcher_email_overlap(sample_profiles):
    # Match on email
    assert CandidateMatcher.match(sample_profiles["ats"], sample_profiles["csv"]) is True
    assert CandidateMatcher.match(sample_profiles["ats"], sample_profiles["resume"]) is True

def test_candidate_matcher_name_metadata_overlap():
    profile_a = CanonicalCandidate(
        candidate_id="resume_alice",
        full_name="Alice Adams",
        location=Location(city="Seattle", region="WA"),
        experience=[Experience(company="Amazon", title="SDE")]
    )
    profile_b = CanonicalCandidate(
        candidate_id="notes_alice",
        full_name="Alice Adams",
        experience=[Experience(company="Amazon", title="SDE II")]
    )
    # Name + company overlap
    assert CandidateMatcher.match(profile_a, profile_b) is True

def test_candidate_resolver_single_values(sample_profiles):
    resolver = ConflictResolver()
    merged = resolver.merge([sample_profiles["notes"], sample_profiles["csv"], sample_profiles["ats"]])
    
    # ATS name ("John Doe") should win over CSV name ("John R. Doe")
    assert merged.full_name == "John Doe"

def test_candidate_resolver_skills_merging(sample_profiles):
    resolver = ConflictResolver()
    merged = resolver.merge([sample_profiles["resume"], sample_profiles["notes"]])
    
    skills = {s.name: s for s in merged.skills}
    assert "Python" in skills
    # Python is in both resume (0.70 weight) and notes (0.55 weight)
    # Base confidence = 0.70 + 0.1 bonus for extra source = 0.80
    assert skills["Python"].confidence == 0.80
    assert "resume" in skills["Python"].sources
    assert "notes" in skills["Python"].sources

def test_candidate_resolver_experience_merging(sample_profiles):
    resolver = ConflictResolver()
    merged = resolver.merge([sample_profiles["ats"], sample_profiles["csv"]])
    
    assert len(merged.experience) == 1
    # Company description should match the longest summary: "Core Search Infrastructure" from CSV is longer than "Worked on Search."
    assert merged.experience[0].summary == "Core Search Infrastructure"
    assert merged.experience[0].end == "Present"
