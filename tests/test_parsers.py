import os
import json
import csv
import pytest
import fitz
from src.parsers.base import get_parser_for_source
from src.parsers.csv_parser import CSVParser
from src.parsers.ats_parser import ATSParser
from src.parsers.resume_parser import ResumeParser
from src.parsers.notes_parser import NotesParser
from src.parsers.github_parser import GitHubParser
from src.utils.exceptions import ParserError

@pytest.fixture
def temp_files(tmp_path):
    # Create a temporary CSV file
    csv_file = tmp_path / "recruiter.csv"
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "email", "phone", "current_company", "title"])
        writer.writerow(["John Doe", "john.doe@example.com", "+14155552671", "Google", "Staff Engineer"])
    
    # Create a temporary JSON file
    ats_file = tmp_path / "ats.json"
    ats_data = {
        "candidate": {
            "first_name": "John",
            "last_name": "Doe",
            "contact": {
                "email_address": "john.doe@example.com"
            }
        }
    }
    with open(ats_file, "w", encoding="utf-8") as f:
        json.dump(ats_data, f)

    # Create a temporary PDF file using PyMuPDF (fitz)
    resume_file = tmp_path / "resume.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "John Doe Resume\nEmail: john.doe@example.com\nWorked at Google as Staff Engineer.")
    doc.save(str(resume_file))
    doc.close()

    # Create a temporary Notes text file
    notes_file = tmp_path / "notes.txt"
    with open(notes_file, "w", encoding="utf-8") as f:
        f.write("Candidate John Doe is very experienced with Python. Email: john.doe@example.com")

    return {
        "csv": str(csv_file),
        "ats": str(ats_file),
        "resume": str(resume_file),
        "notes": str(notes_file)
    }

def test_source_detection(temp_files):
    assert isinstance(get_parser_for_source(temp_files["csv"]), CSVParser)
    assert isinstance(get_parser_for_source(temp_files["ats"]), ATSParser)
    assert isinstance(get_parser_for_source(temp_files["resume"]), ResumeParser)
    assert isinstance(get_parser_for_source(temp_files["notes"]), NotesParser)
    assert isinstance(get_parser_for_source("https://github.com/mockuser"), GitHubParser)
    
    with pytest.raises(ParserError):
        get_parser_for_source("invalid_file_format.zip")

def test_csv_parser(temp_files):
    parser = CSVParser()
    result = parser.parse(temp_files["csv"])
    assert result["source_type"] == "csv"
    assert len(result["raw_content"]) == 1
    assert result["raw_content"][0]["name"] == "John Doe"

def test_ats_parser(temp_files):
    parser = ATSParser()
    result = parser.parse(temp_files["ats"])
    assert result["source_type"] == "ats"
    assert result["raw_content"]["candidate"]["first_name"] == "John"

def test_resume_parser(temp_files):
    parser = ResumeParser()
    result = parser.parse(temp_files["resume"])
    assert result["source_type"] == "resume"
    assert "John Doe Resume" in result["raw_content"]["raw_text"]

def test_notes_parser(temp_files):
    parser = NotesParser()
    result = parser.parse(temp_files["notes"])
    assert result["source_type"] == "notes"
    assert "experienced with Python" in result["raw_content"]["raw_text"]

def test_github_parser(monkeypatch):
    monkeypatch.setenv("GITHUB_MOCK", "true")
    parser = GitHubParser()
    result = parser.parse("https://github.com/mockuser")
    assert result["source_type"] == "github"
    assert result["raw_content"]["user"]["name"] == "Mock Candidate"
    assert "candidate-transformer" in [r["name"] for r in result["raw_content"]["repos"]]
