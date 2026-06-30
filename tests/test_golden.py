import json
from src.utils.loader import load_config
from src.pipeline import CandidateTransformationPipeline

def test_golden_profile_comparison():
    config_path = "config/default.json"
    config = load_config(config_path)
    
    pipeline = CandidateTransformationPipeline()
    result = pipeline.run(
        config=config,
        csv_path="sample_inputs/recruiter.csv",
        ats_path="sample_inputs/ats.json",
        resume_path="sample_inputs/resume.pdf",
        notes_path="sample_inputs/notes.txt"
    )
    
    # Load golden profile
    golden_path = "sample_outputs/golden_profile.json"
    with open(golden_path, "r", encoding="utf-8") as f:
        golden_data = json.load(f)
        
    assert result == golden_data
